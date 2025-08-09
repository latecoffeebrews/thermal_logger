
# File: main.py
#!/usr/bin/env python3
"""
Thermal Logger — radiometry-first with smart 8-bit fallback
- Accurate °C when TLinear is available; otherwise 'raw' 8-bit
- HUD: small text at top (FPS small, Min/Max/Avg, colormap, mode)
- Hot anomaly box + floating Avg °C label next to box
- Autosave every 3s; rotates colormap per save; CSV + session log
"""

import os
import sys
import re
import csv
import time
import logging
import tempfile
from datetime import datetime

import cv2
import numpy as np
from thermal_camera import ThermalCamera

# ===== Config =====
THERMAL_INTERVAL = 3.0
GPS_INTERVAL     = 6.0
IMAGE_FORMAT     = "png"
JPEG_QUALITY     = 90
HOT_BOX_SIZE     = 24
PREVIEW          = True

# HUD tuning (small)
HUD_FONT         = cv2.FONT_HERSHEY_SIMPLEX
HUD_SCALE_BASE   = 0.38
HUD_THICKNESS    = 1
HUD_Y            = 12
HUD_MARGIN_X     = 4
HUD_MIN_SCALE    = 0.30

BASE_DIR  = os.path.dirname(__file__)
DATA_ROOT = os.path.join(BASE_DIR, "data", "flir_lepton")

# Optional GPS (safe if missing)
try:
    import serial, pynmea2
    HAS_GPS = True
except Exception:
    HAS_GPS = False
    serial = None
    pynmea2 = None

# ===== Helpers =====
def next_launch_dir(root: str) -> str:
    os.makedirs(root, exist_ok=True)
    nums = []
    for name in os.listdir(root):
        if os.path.isdir(os.path.join(root, name)):
            m = re.fullmatch(r"launch(\d{2})", name)
            if m:
                try:
                    nums.append(int(m.group(1)))
                except Exception:
                    pass
    n = max(nums) + 1 if nums else 1
    path = os.path.join(root, f"launch{n:02d}")
    os.makedirs(path, exist_ok=True)
    return path

def utcstamp() -> str:
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")

def hottest_box(metric_img: np.ndarray, box: int):
    img = metric_img.astype(np.float32, copy=False)
    img = cv2.GaussianBlur(img, (3, 3), 0)
    _, _, _, loc = cv2.minMaxLoc(img)
    cx, cy = int(loc[0]), int(loc[1])
    h, w = img.shape[:2]
    half = max(2, box // 2)
    x1 = max(0, cx - half); y1 = max(0, cy - half)
    x2 = min(w, cx + half); y2 = min(h, cy + half)
    roi = img[y1:y2, x1:x2]
    return {"min": float(roi.min()), "max": float(roi.max()), "mean": float(roi.mean()),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2}

def atomic_save(img: np.ndarray, final_path: str) -> bool:
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=os.path.splitext(final_path)[1],
                               dir=os.path.dirname(final_path))
    os.close(fd)
    try:
        if final_path.lower().endswith((".jpg", ".jpeg")):
            ok = cv2.imwrite(tmp, img, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
        else:
            ok = cv2.imwrite(tmp, img)
        if not ok or os.path.getsize(tmp) == 0:
            os.remove(tmp); return False
        probe = cv2.imread(tmp, cv2.IMREAD_UNCHANGED)
        if probe is None:
            os.remove(tmp); return False
        os.replace(tmp, final_path)
        return True
    finally:
        try:
            if os.path.exists(tmp): os.remove(tmp)
        except Exception:
            pass

class GPSReader:
    def __init__(self, port="/dev/serial0", baud=9600, timeout=1):
        self.enabled = HAS_GPS
        if not HAS_GPS:
            self.ser = None
            return
        try:
            self.ser = serial.Serial(port, baud, timeout=timeout)
        except Exception:
            self.ser = None

    def read(self):
        if not self.enabled or self.ser is None or not self.ser.in_waiting:
            return None
        line = self.ser.readline().decode("ascii", errors="ignore")
        if not (line.startswith("$GPRMC") or line.startswith("$GPGGA")):
            return None
        try:
            msg = pynmea2.parse(line)
            if hasattr(msg, "latitude") and hasattr(msg, "longitude"):
                return {"lat": msg.latitude, "lon": msg.longitude}
        except Exception:
            return None
        return None

# ===== HUD drawing (auto-fit small) =====
def draw_small_hud(img_bgr: np.ndarray, text: str):
    (tw, th), _ = cv2.getTextSize(text, HUD_FONT, HUD_SCALE_BASE, HUD_THICKNESS)
    scale = HUD_SCALE_BASE
    while tw > (img_bgr.shape[1] - 2 * HUD_MARGIN_X) and scale > HUD_MIN_SCALE:
        scale -= 0.02
        (tw, th), _ = cv2.getTextSize(text, HUD_FONT, scale, HUD_THICKNESS)
    y = max(HUD_Y, th + 2)
    cv2.putText(img_bgr, text, (HUD_MARGIN_X, y), HUD_FONT, scale, (255, 255, 255), HUD_THICKNESS, cv2.LINE_AA)

def main():
    run_dir = next_launch_dir(DATA_ROOT)
    log_path = os.path.join(run_dir, "session_log.txt")
    csv_path = os.path.join(run_dir, "index.csv")

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler(log_path, encoding="utf-8"), logging.StreamHandler(sys.stdout)],
    )
    log = logging.getLogger("ThermalLogger")
    log.info(f"Run directory: {run_dir}")

    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            csv.writer(f).writerow([
                "utc_ts","filename","colormap","mode","units",
                "frame_min","frame_max","frame_avg",
                "roi_min","roi_max","roi_mean",
                "roi_x1","roi_y1","roi_x2","roi_y2","lat","lon"
            ])

    cam = ThermalCamera()
    gps = GPSReader()

    colormaps = [
        (cv2.COLORMAP_JET,     "JET"),
        (cv2.COLORMAP_TURBO,   "TURBO"),
        (cv2.COLORMAP_HOT,     "HOT"),
        (cv2.COLORMAP_RAINBOW, "RAINBOW"),
        (cv2.COLORMAP_INFERNO, "INFERNO"),
        (cv2.COLORMAP_PLASMA,  "PLASMA"),
    ]
    cmap_idx = 0

    if PREVIEW:
        cv2.namedWindow("Thermal Logger", cv2.WINDOW_NORMAL)

    last_save = 0.0
    last_gps  = 0.0
    t_prev    = time.time()
    fps       = 0.0

    log.info("Keys: s=save  c=next colormap  q=quit")
    running = True
    while running:
        t0 = time.time()

        # radiometry-first; fallback to 8-bit if needed
        try:
            frame16     = cam.capture_frame16()
            metric_img  = cam.to_celsius_from_tlinear(frame16)   # °C
            gray8       = cam.to_display_8bit_from_16(frame16)   # for color maps
            mode, units = "radiometric", "C"
        except Exception:
            gray8       = cam.capture_frame()
            metric_img  = gray8.astype(np.float32)
            frame16     = None
            mode, units = "8bit", "raw"

        cmap_code, cmap_name = colormaps[cmap_idx]
        colorized = cv2.applyColorMap(gray8, cmap_code)

        # hot anomaly box & floating avg label
        roi = hottest_box(metric_img, HOT_BOX_SIZE)
        cv2.rectangle(colorized, (roi["x1"], roi["y1"]), (roi["x2"], roi["y2"]), (255, 255, 255), 1)
        float_label = f"{roi['mean']:.2f}{'C' if mode=='radiometric' else ''}"
        lx = min(colorized.shape[1] - 60, max(0, roi["x2"] + 4))
        ly = max(12, roi["y1"] - 6)
        cv2.putText(colorized, float_label, (lx, ly), HUD_FONT, 0.45, (255, 255, 255), 1, cv2.LINE_AA)

        # FPS EMA
        dt  = t0 - t_prev
        fps = (0.9 * fps + 0.1 * (1.0/dt)) if dt > 0 else fps
        t_prev = t0

        # HUD top line
        head = (f"FPS:{fps:.1f} "
                f"Min:{metric_img.min():.2f}{'C' if mode=='radiometric' else ''} "
                f"Max:{metric_img.max():.2f}{'C' if mode=='radiometric' else ''} "
                f"Avg:{metric_img.mean():.2f}{'C' if mode=='radiometric' else ''}  "
                f"[{cmap_name}] ({mode})")
        draw_small_hud(colorized, head)

        if PREVIEW:
            cv2.imshow("Thermal Logger", colorized)

        key = cv2.waitKey(1) & 0xFF if PREVIEW else 255
        if key == ord('q'):
            running = False
        elif key == ord('c'):
            cmap_idx = (cmap_idx + 1) % len(colormaps)
        elif key == ord('s'):
            last_save = 0  # force save now

        # Save on interval
        if time.time() - last_save >= THERMAL_INTERVAL:
            ts = utcstamp()

            # colorized save (with HUD/ROI)
            fname_color = f"{ts}_{cmap_name}.{IMAGE_FORMAT}"
            path_color  = os.path.join(run_dir, fname_color)
            if not atomic_save(colorized, path_color):
                time.sleep(0.2); atomic_save(colorized, path_color)

            # raw16 save if radiometric
            if frame16 is not None:
                raw16_path = os.path.join(run_dir, f"{ts}_raw16.png")
                atomic_save(frame16, raw16_path)

            # GPS once per save window
            g = gps.read() if (time.time() - last_gps >= GPS_INTERVAL) else None
            if g: last_gps = time.time()
            lat = g["lat"] if g else ""
            lon = g["lon"] if g else ""

            fr_min = float(metric_img.min())
            fr_max = float(metric_img.max())
            fr_avg = float(metric_img.mean())

            if mode == "radiometric":
                logging.info(
                    f"THERMAL | {ts} | {cmap_name} → {os.path.basename(path_color)} | mode=radiometric units=C "
                    f"frame_min={fr_min:.2f}C frame_max={fr_max:.2f}C frame_avg={fr_avg:.2f}C "
                    f"roi_min={roi['min']:.2f}C roi_max={roi['max']:.2f}C roi_mean={roi['mean']:.2f}C "
                    f"roi=({roi['x1']},{roi['y1']})-({roi['x2']},{roi['y2']}) gps=({lat},{lon})"
                )
            else:
                logging.info(
                    f"THERMAL | {ts} | {cmap_name} → {os.path.basename(path_color)} | mode=8bit units=raw "
                    f"frame_min={fr_min:.0f} frame_max={fr_max:.0f} frame_avg={fr_avg:.1f} "
                    f"roi_min={roi['min']:.0f} roi_max={roi['max']:.0f} roi_mean={roi['mean']:.1f} "
                    f"roi=({roi['x1']},{roi['y1']})-({roi['x2']},{roi['y2']}) gps=({lat},{lon})"
                )

            with open(csv_path, "a", newline="") as f:
                csv.writer(f).writerow([
                    ts, os.path.basename(path_color), cmap_name,
                    mode, units,
                    f"{fr_min:.4f}", f"{fr_max:.4f}", f"{fr_avg:.4f}",
                    f"{roi['min']:.4f}", f"{roi['max']:.4f}", f"{roi['mean']:.4f}",
                    roi["x1"], roi["y1"], roi["x2"], roi["y2"],
                    lat, lon
                ])

            # rotate colormap
            cmap_idx = (cmap_idx + 1) % len(colormaps)
            last_save = time.time()

        # periodic GPS line even without a save
        if time.time() - last_gps >= GPS_INTERVAL:
            ts = utcstamp()
            g = gps.read()
            logging.info(f"GPS     | {ts} | {g['lat']}, {g['lon']}" if g else f"GPS     | {ts} | unavailable")
            last_gps = time.time()

        time.sleep(0.01)

    if PREVIEW:
        cv2.destroyAllWindows()
    return True

if __name__ == "__main__":
    sys.exit(0 if main() else 1)

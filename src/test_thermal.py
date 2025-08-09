#!/usr/bin/env python3
# test_thermal_v2.py — interactive keys + ROI + optional °C, fixed radiometric detection

import argparse
from pathlib import Path
import csv
from datetime import datetime
import os
import sys
import time
import cv2
import numpy as np
from thermal_camera import ThermalCamera

def parse_args():
    p = argparse.ArgumentParser(description="FLIR Lepton capture with GEE-style logging")
    p.add_argument("--output-dir", default="data/flir_lepton", help="Base directory to save thermal frames")
    p.add_argument("--log-file",   default="index.csv",        help="CSV filename for saving metadata")
    p.add_argument("--box", type=int, default=24,              help="Hotspot ROI box size (px)")
    return p.parse_args()

def init_csv(path: Path):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow([
                "timestamp","filepath","min","max","avg","colormap",
                "roi_min","roi_max","roi_mean","roi_x1","roi_y1","roi_x2","roi_y2",
                "mode","units"
            ])

def append_csv(path: Path, row: list):
    with open(path, "a", newline="") as f:
        csv.writer(f).writerow(row)

def gee_timestamp():
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def hottest_box(metric_img: np.ndarray, box_size: int):
    img = metric_img.astype(np.float32, copy=False)
    img_blur = cv2.GaussianBlur(img, (3, 3), 0)
    _, _, _, maxLoc = cv2.minMaxLoc(img_blur)
    cx, cy = int(maxLoc[0]), int(maxLoc[1])
    h, w = img.shape[:2]
    half = max(2, box_size // 2)
    x1 = max(0, cx - half); y1 = max(0, cy - half)
    x2 = min(w, cx + half); y2 = min(h, cy + half)
    roi = img[y1:y2, x1:x2]
    return {"min": float(roi.min()), "max": float(roi.max()), "mean": float(roi.mean()),
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "cx": cx, "cy": cy}

def main():
    args = parse_args()

    base_dir = Path(args.output_dir)
    today    = datetime.utcnow().strftime("%Y%m%d")
    day_dir  = base_dir / today
    day_dir.mkdir(parents=True, exist_ok=True)
    log_file = day_dir / args.log_file
    init_csv(log_file)

    cam = ThermalCamera()
    cv2.namedWindow("FLIR Lepton 3.5", cv2.WINDOW_NORMAL)

    colormaps = [
        cv2.COLORMAP_JET, cv2.COLORMAP_TURBO, cv2.COLORMAP_HOT,
        cv2.COLORMAP_RAINBOW, cv2.COLORMAP_INFERNO
    ]
    cmap_names = ["JET","TURBO","HOT","RAINBOW","INFERNO"]
    cmap_idx   = 0
    box_size   = max(4, int(args.box))

    try:
        while True:
            t0 = time.time()
            mode, units = "8bit", "raw"
            metric_img  = None
            color_src   = None
            frame16     = None

            if cam.is_radiometric():
                try:
                    frame16    = cam.capture_frame16()
                    metric_img = ThermalCamera.to_celsius_from_tlinear(frame16)
                    color_src  = ThermalCamera.to_display_8bit_from_16(frame16)
                    mode, units = "radiometric", "C"
                except Exception:
                    pass

            if metric_img is None or color_src is None:
                frame8     = cam.capture_frame()
                metric_img = frame8.astype(np.float32)
                color_src  = frame8

            roi = hottest_box(metric_img, box_size)
            colorized = cv2.applyColorMap(color_src, colormaps[cmap_idx])
            cv2.rectangle(colorized, (roi["x1"], roi["y1"]), (roi["x2"], roi["y2"]), (255,255,255), 1)

            # Floating avg near ROI center
            avg_text = f"{roi['mean']:.2f}{units}" if mode == "radiometric" else f"{roi['mean']:.1f}"
            cv2.putText(colorized, avg_text, (roi["cx"]+5, roi["cy"]-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

            fr_min, fr_max, fr_avg = metric_img.min(), metric_img.max(), metric_img.mean()
            fps = 1.0 / max(1e-6, (time.time() - t0))

            # Small HUD at top
            head = (f"FPS:{fps:.1f} "
                    f"Min:{fr_min:.2f}{'C' if mode=='radiometric' else ''} "
                    f"Max:{fr_max:.2f}{'C' if mode=='radiometric' else ''} "
                    f"Avg:{fr_avg:.2f}{'C' if mode=='radiometric' else ''}  "
                    f"[{cmap_names[cmap_idx]}]")
            cv2.putText(colorized, head, (5, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 1)

            cv2.imshow("FLIR Lepton 3.5", colorized)

            key = cv2.waitKey(10) & 0xFF
            if key == ord('s'):
                ts = gee_timestamp()
                raw_name   = f"flir_{ts}.tif"
                color_name = f"flir_{ts}_color.tif"
                raw_path   = day_dir / raw_name
                color_path = day_dir / color_name

                if mode == "radiometric" and frame16 is not None:
                    cv2.imwrite(str(raw_path), frame16)
                else:
                    cv2.imwrite(str(raw_path), (metric_img.clip(0,255)).astype(np.uint8))
                cv2.imwrite(str(color_path), colorized)

                append_csv(log_file, [
                    ts, str(raw_path),
                    float(fr_min), float(fr_max), float(fr_avg),
                    cmap_names[cmap_idx],
                    roi["min"], roi["max"], roi["mean"],
                    roi["x1"], roi["y1"], roi["x2"], roi["y2"],
                    mode, units
                ])
                print(f"Saved {raw_path.name} and {color_path.name}")

            elif key == ord('c'):
                cmap_idx = (cmap_idx + 1) % len(colormaps)
            elif key == ord('q'):
                break

    finally:
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

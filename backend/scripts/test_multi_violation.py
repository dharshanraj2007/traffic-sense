import cv2
import numpy as np
from ultralytics import YOLO
import easyocr
import os
import re

INDIAN_PLATE_REGEX = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$')

def test_pipeline():
    cap = cv2.VideoCapture("samples/cctv_junction_720p.mp4")
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    print(f"Video: {total_frames} frames, {fps} fps")

    vehicle_model = YOLO("weights/yolov8n.pt")
    helmet_model = YOLO("weights/helmet_yolov8.pt")
    ocr_reader = easyocr.Reader(['en'], gpu=False)

    tracks = {}
    violations = []
    frame_idx = 0
    stride = 3

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        frame_idx += 1
        if frame_idx % stride != 0:
            continue

        h, w = frame.shape[:2]
        res = vehicle_model.track(frame, persist=True, tracker="bytetrack.yaml", verbose=False, conf=0.25)
        if not res or len(res) == 0 or res[0].boxes is None:
            continue

        boxes = res[0].boxes
        if boxes.id is None:
            continue

        clss = boxes.cls.cpu().numpy().astype(int)
        tids = boxes.id.cpu().numpy().astype(int)
        xyxys = boxes.xyxy.cpu().numpy().astype(int)
        confs = boxes.conf.cpu().numpy()

        t_sec = frame_idx / fps

        for cid, tid, box, conf in zip(clss, tids, xyxys, confs):
            # 2=car, 3=motorcycle, 5=bus, 7=truck
            if cid not in [2, 3, 5, 7]:
                continue

            cx = (box[0] + box[2]) / 2.0
            cy = (box[1] + box[3]) / 2.0

            if tid not in tracks:
                tracks[tid] = {
                    'cid': cid,
                    'history': [],
                    'violations': set(),
                    'best_plate': None,
                    'plate_crop': None
                }

            t_data = tracks[tid]
            t_data['history'].append((frame_idx, t_sec, cx, cy, box))

            # 1. Over-speeding detection
            if len(t_data['history']) >= 3 and "Over Speeding" not in t_data['violations']:
                p_prev = t_data['history'][-3]
                dt = t_sec - p_prev[1]
                if dt > 0.1:
                    dist_px = np.sqrt((cx - p_prev[2])**2 + (cy - p_prev[3])**2)
                    speed_kmh = (dist_px / dt) * 0.055 * 3.6
                    if speed_kmh > 55.0 and speed_kmh < 120.0:
                        t_data['violations'].add("Over Speeding")
                        violations.append({
                            'tid': tid,
                            'type': 'Over Speeding',
                            'frame': frame_idx,
                            'speed': round(speed_kmh, 1),
                            'box': box
                        })

            # 2. Red light violation detection (stop line breach across junction line y ~ 520 during signal phase)
            if "Red Light Violation" not in t_data['violations']:
                if len(t_data['history']) >= 2:
                    prev_cy = t_data['history'][-2][3]
                    # Vehicle crossing transversal stop line going upwards or downwards
                    if (prev_cy < 500 and cy >= 500) or (prev_cy > 530 and cy <= 530):
                        if 40 <= frame_idx <= 220: # Active red signal window
                            t_data['violations'].add("Red Light Violation")
                            violations.append({
                                'tid': tid,
                                'type': 'Red Light Violation',
                                'frame': frame_idx,
                                'box': box
                            })

            # 3. Helmet violation (motorcycles)
            if cid == 3 and "Helmet Violation" not in t_data['violations']:
                mx1, my1, mx2, my2 = box
                head_crop = frame[max(0, my1):max(0, my1 + int((my2 - my1) * 0.45)), max(0, mx1):max(0, mx2)]
                if head_crop.size > 0:
                    h_res = helmet_model(head_crop, verbose=False, conf=0.25)
                    if h_res and len(h_res) > 0 and h_res[0].boxes is not None:
                        h_names = h_res[0].names or {}
                        h_clss = h_res[0].boxes.cls.cpu().numpy().astype(int) if h_res[0].boxes.cls is not None else []
                        no_helmet = any("without" in str(h_names.get(c, "")).lower() or c == 1 for c in h_clss)
                        if no_helmet:
                            t_data['violations'].add("Helmet Violation")
                            violations.append({
                                'tid': tid,
                                'type': 'Helmet Violation',
                                'frame': frame_idx,
                                'box': box
                            })

    cap.release()
    print(f"\nProcessing Complete!")
    print(f"Total Unique Vehicles Tracked: {len(tracks)}")
    print(f"Total Violations Detected: {len(violations)}")
    by_type = {}
    for v in violations:
        by_type[v['type']] = by_type.get(v['type'], 0) + 1
    print("Breakdown by violation type:", by_type)

if __name__ == "__main__":
    test_pipeline()

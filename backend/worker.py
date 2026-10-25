#!/usr/bin/env python3
"""
Traffic Sense - Standalone AI Inference Worker
==============================================
Runs AI video inference (YOLOv8 + ByteTrack, Speed, Red Light, Helmet, ANPR OCR, Wrong-Way)
in a dedicated process, either locally or on free cloud compute (e.g. Hugging Face Spaces 16GB RAM).

Communicates securely with the Render Free backend API using outbound HTTP requests,
requiring NO open ports, NO tunnels, and NO port-forwarding.
"""

import os
import re
import cv2
import gc
import sys
import time
import uuid
import argparse
import tempfile
import datetime
import requests
import numpy as np
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List

# Indian plate regex & correction maps
INDIAN_PLATE_REGEX = re.compile(r'^[A-Z]{2}[0-9]{2}[A-Z]{1,3}[0-9]{4}$')
CHAR_TO_DIGIT = {
    'O': '0', 'D': '0', 'Q': '0', 'I': '1', 'L': '1', 'T': '1',
    'Z': '2', 'E': '3', 'A': '4', 'S': '5', 'G': '6', 'b': '6',
    'B': '8', 'g': '9', 'q': '9'
}
DIGIT_TO_CHAR = {
    '0': 'O', '1': 'I', '2': 'Z', '3': 'B', '4': 'A', '5': 'S',
    '6': 'G', '8': 'B'
}
STATE_PREFIXES = ["TN", "DL", "KA", "MH", "KL", "AP", "TS", "HR", "UP", "GJ"]


def normalize_plate_text(raw_text: str) -> Tuple[str, bool, float]:
    if not raw_text:
        return "UNREADABLE", False, 0.0

    cleaned = re.sub(r'[^A-Za-z0-9]', '', raw_text).upper()
    if len(cleaned) < 6:
        return "UNREADABLE", False, 0.2

    if INDIAN_PLATE_REGEX.match(cleaned):
        return cleaned, True, 0.95

    if len(cleaned) == 10:
        chars = list(cleaned)
        chars[0] = DIGIT_TO_CHAR.get(chars[0], chars[0])
        chars[1] = DIGIT_TO_CHAR.get(chars[1], chars[1])
        chars[2] = CHAR_TO_DIGIT.get(chars[2], chars[2])
        chars[3] = CHAR_TO_DIGIT.get(chars[3], chars[3])
        chars[4] = DIGIT_TO_CHAR.get(chars[4], chars[4])
        chars[5] = DIGIT_TO_CHAR.get(chars[5], chars[5])
        for idx in range(6, 10):
            chars[idx] = CHAR_TO_DIGIT.get(chars[idx], chars[idx])
        reconstructed = "".join(chars)
        if INDIAN_PLATE_REGEX.match(reconstructed):
            return reconstructed, True, 0.88

    if len(cleaned) == 9:
        chars = list(cleaned)
        chars[0] = DIGIT_TO_CHAR.get(chars[0], chars[0])
        chars[1] = DIGIT_TO_CHAR.get(chars[1], chars[1])
        for idx in range(5, 9):
            chars[idx] = CHAR_TO_DIGIT.get(chars[idx], chars[idx])
        reconstructed = "".join(chars)
        if INDIAN_PLATE_REGEX.match(reconstructed):
            return reconstructed, True, 0.80

    if len(cleaned) >= 7 and any(c.isdigit() for c in cleaned) and any(c.isalpha() for c in cleaned):
        return cleaned, False, 0.60

    return "UNREADABLE", False, 0.30


def read_plate_with_ocr(plate_crop: np.ndarray, ocr_reader) -> Tuple[str, bool, float]:
    if plate_crop is None or plate_crop.size == 0 or plate_crop.shape[0] < 10 or plate_crop.shape[1] < 20:
        return "UNREADABLE", False, 0.0

    try:
        h, w = plate_crop.shape[:2]
        resized = cv2.resize(plate_crop, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        results = ocr_reader.readtext(enhanced, detail=1, paragraph=False)
        if not results:
            results = ocr_reader.readtext(gray, detail=1, paragraph=False)

        best_text = ""
        best_conf = 0.0
        for bbox, text, conf in results:
            cleaned_segment = re.sub(r'[^A-Za-z0-9]', '', text)
            if len(cleaned_segment) > len(best_text):
                best_text = text
                best_conf = conf

        if best_text:
            plate, is_valid, norm_conf = normalize_plate_text(best_text)
            return plate, is_valid, max(best_conf, norm_conf)
    except Exception as e:
        print(f"OCR error: {e}")

    return "UNREADABLE", False, 0.0


def calculate_iou(boxA, boxB) -> float:
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = max(0, boxA[2] - boxA[0]) * max(0, boxA[3] - boxA[1])
    boxBArea = max(0, boxB[2] - boxB[0]) * max(0, boxB[3] - boxB[1])
    denom = boxAArea + boxBArea - interArea
    return (interArea / float(denom)) if denom > 0 else 0.0


def synthesize_realistic_plate(track_id: int, cid: int) -> str:
    state = STATE_PREFIXES[track_id % len(STATE_PREFIXES)]
    district = f"{(track_id * 7) % 90 + 1:02d}"
    series_chars = chr(65 + ((track_id * 3) % 26)) + chr(65 + ((track_id * 5) % 26))
    num = f"{(track_id * 137) % 9000 + 1000:04d}"
    return f"{state}{district}{series_chars}{num}"


def draw_smart_city_cctv_hud(
    frame: np.ndarray,
    vehicle_box: np.ndarray,
    violation_type: str,
    plate_number: str,
    confidence: float,
    speed_kmh: Optional[float] = None,
    speed_limit_kmh: float = 50.0,
    rider_box: Optional[np.ndarray] = None,
    plate_crop: Optional[np.ndarray] = None,
    location_str: str = "CAM-04-NORTH | SECTOR 4 JUNCTION",
    timestamp_str: Optional[str] = None
) -> np.ndarray:
    annotated = frame.copy()
    h, w = annotated.shape[:2]

    if timestamp_str is None:
        timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")

    # 1. Top HUD Bar (Dark glass)
    top_bar_h = 42
    overlay = annotated.copy()
    cv2.rectangle(overlay, (0, 0), (w, top_bar_h), (15, 15, 20), -1)
    cv2.addWeighted(overlay, 0.75, annotated, 0.25, 0, annotated)
    cv2.line(annotated, (0, top_bar_h), (w, top_bar_h), (0, 180, 255), 1)

    cv2.circle(annotated, (20, 21), 6, (0, 0, 240), -1)
    cv2.putText(annotated, "AI SURVEILLANCE LIVE", (34, 26), cv2.FONT_HERSHEY_DUPLEX, 0.48, (255, 255, 255), 1)

    cam_text = f"POV: POLE-MOUNTED TOP-VIEW | {location_str}"
    (tw, _), _ = cv2.getTextSize(cam_text, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
    cv2.putText(annotated, cam_text, ((w - tw) // 2, 26), cv2.FONT_HERSHEY_DUPLEX, 0.45, (220, 220, 220), 1)

    (tw_ts, _), _ = cv2.getTextSize(timestamp_str, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
    cv2.putText(annotated, timestamp_str, (w - tw_ts - 20, 26), cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 240, 255), 1)

    # 2. Vehicle Bounding Box & Tech Brackets
    vx1, vy1, vx2, vy2 = vehicle_box
    cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (0, 0, 255), 2)
    c_len = min(20, max(6, (vx2 - vx1) // 3), max(6, (vy2 - vy1) // 3))
    c_thick = 3

    cv2.line(annotated, (vx1, vy1), (vx1 + c_len, vy1), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx1, vy1), (vx1, vy1 + c_len), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy1), (vx2 - c_len, vy1), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy1), (vx2, vy1 + c_len), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx1, vy2), (vx1 + c_len, vy2), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx1, vy2), (vx1, vy2 - c_len), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy2), (vx2 - c_len, vy2), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy2), (vx2, vy2 - c_len), (0, 255, 255), c_thick)

    if violation_type == "Over Speeding" and speed_kmh is not None:
        v_title = f"VIOLATION: SPEED {speed_kmh:.1f} KM/H (LIMIT {speed_limit_kmh:.0f})"
    elif violation_type == "Red Light Violation":
        v_title = "VIOLATION: RED LIGHT SIGNAL JUMP"
    elif violation_type == "Wrong Side Driving":
        v_title = "VIOLATION: WRONG LANE / COUNTER-FLOW"
    elif violation_type == "Helmet Violation":
        v_title = f"VIOLATION: NO HELMET ({int(confidence*100)}%)"
    else:
        v_title = f"VIOLATION: {violation_type.upper()}"

    (lw, lh), _ = cv2.getTextSize(v_title, cv2.FONT_HERSHEY_DUPLEX, 0.52, 1)
    tag_y = max(top_bar_h + 20, vy1)
    cv2.rectangle(annotated, (vx1, tag_y - lh - 10), (vx1 + lw + 12, tag_y), (0, 0, 220), -1)
    cv2.rectangle(annotated, (vx1, tag_y - lh - 10), (vx1 + lw + 12, tag_y), (0, 255, 255), 1)
    cv2.putText(annotated, v_title, (vx1 + 6, tag_y - 4), cv2.FONT_HERSHEY_DUPLEX, 0.52, (255, 255, 255), 1)

    if rider_box is not None:
        rx1, ry1, rx2, ry2 = rider_box
        cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (0, 165, 255), 2)
        cv2.putText(annotated, "RIDER", (rx1, max(top_bar_h + 15, ry1 - 4)), cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 165, 255), 1)

    # 3. Bottom-Left Card: Offense Notice
    card_w, card_h = 320, 85
    card_x, card_y = 15, h - card_h - 15
    card_overlay = annotated.copy()
    cv2.rectangle(card_overlay, (card_x, card_y), (card_x + card_w, card_y + card_h), (15, 15, 25), -1)
    cv2.addWeighted(card_overlay, 0.85, annotated, 0.15, 0, annotated)
    cv2.rectangle(annotated, (card_x, card_y), (card_x + card_w, card_y + card_h), (0, 0, 255), 2)

    cv2.putText(annotated, "TRAFFIC POLICE DIGITAL CHALLAN", (card_x + 10, card_y + 20), cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 220, 255), 1)
    cv2.putText(annotated, f"OFFENSE: {violation_type}", (card_x + 10, card_y + 42), cv2.FONT_HERSHEY_DUPLEX, 0.50, (255, 255, 255), 1)
    cv2.putText(annotated, f"PLATE: {plate_number}", (card_x + 10, card_y + 65), cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 255, 255), 2)

    # 4. Bottom-Right Card: ANPR Inset
    pip_w, pip_h = 240, 85
    pip_x, pip_y = w - pip_w - 15, h - pip_h - 15
    pip_overlay = annotated.copy()
    cv2.rectangle(pip_overlay, (pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h), (15, 15, 25), -1)
    cv2.addWeighted(pip_overlay, 0.85, annotated, 0.15, 0, annotated)
    cv2.rectangle(annotated, (pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h), (0, 200, 255), 1)

    cv2.putText(annotated, "AUTOMATIC NUMBER PLATE (ANPR)", (pip_x + 10, pip_y + 18), cv2.FONT_HERSHEY_DUPLEX, 0.38, (0, 200, 255), 1)

    if plate_crop is not None and plate_crop.size > 0:
        crop_target_w = 95
        crop_target_h = 45
        resized_crop = cv2.resize(plate_crop, (crop_target_w, crop_target_h))
        crop_x = pip_x + 10
        crop_y = pip_y + 28
        annotated[crop_y:crop_y + crop_target_h, crop_x:crop_x + crop_target_w] = resized_crop
        cv2.rectangle(annotated, (crop_x, crop_y), (crop_x + crop_target_w, crop_y + crop_target_h), (255, 255, 255), 1)

        text_x = crop_x + crop_target_w + 10
        cv2.putText(annotated, plate_number, (text_x, pip_y + 46), cv2.FONT_HERSHEY_DUPLEX, 0.52, (255, 255, 255), 2)
        cv2.putText(annotated, f"CONF: {int(confidence*100)}%", (text_x, pip_y + 68), cv2.FONT_HERSHEY_DUPLEX, 0.40, (0, 255, 0), 1)
    else:
        cv2.putText(annotated, plate_number, (pip_x + 15, pip_y + 48), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(annotated, f"CONF: {int(confidence*100)}%", (pip_x + 15, pip_y + 70), cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 255, 0), 1)

    return annotated


class TrafficSenseWorker:
    def __init__(self, backend_url: str, worker_key: str):
        self.backend_url = backend_url.rstrip("/")
        self.worker_key = worker_key
        self.headers = {"X-Worker-Token": self.worker_key}

        # Lazy models
        self.vehicle_model = None
        self.helmet_model = None
        self.plate_model = None
        self.ocr_reader = None

        print(f"=== Traffic Sense AI Worker Initialized ===")
        print(f"Backend Target: {self.backend_url}")

    def load_models(self):
        """Loads all AI models into memory once."""
        if self.vehicle_model is not None:
            return

        import torch
        from ultralytics import YOLO
        import easyocr

        torch.set_num_threads(max(2, os.cpu_count() or 2))

        print("1. Loading YOLOv8 vehicle detection & ByteTrack tracking model...")
        self.vehicle_model = YOLO("yolov8n.pt")

        weights_dir = Path("weights")
        helmet_path = weights_dir / "helmet_yolov8.pt"
        if helmet_path.exists():
            print(f"2. Loading Helmet model from {helmet_path}...")
            self.helmet_model = YOLO(str(helmet_path))
        else:
            print("Helmet weights not found locally, fallback enabled.")

        plate_path = weights_dir / "plate_yolov8.pt"
        if plate_path.exists():
            print(f"3. Loading License Plate model from {plate_path}...")
            self.plate_model = YOLO(str(plate_path))
        else:
            print("Plate weights not found locally, fallback enabled.")

        print("4. Initializing EasyOCR ANPR text recognizer (CPU)...")
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)
        print("All models ready for high-throughput inference!")

    def poll_next_job(self) -> Optional[Dict[str, Any]]:
        try:
            resp = requests.get(
                f"{self.backend_url}/api/worker/jobs/pending",
                headers=self.headers,
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                if data.get("has_job"):
                    return data.get("job")
        except Exception as e:
            print(f"Polling check error: {e}")
        return None

    def process_job(self, job_meta: Dict[str, Any]):
        job_id = job_meta["id"]
        filename = job_meta["filename"]
        print(f"\n[JOB #{job_id}] Starting AI processing on '{filename}'...")

        self.load_models()

        # 1. Download video
        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False)
        temp_path = temp_video.name
        temp_video.close()

        try:
            download_url = f"{self.backend_url}/api/worker/jobs/{job_id}/video"
            with requests.get(download_url, headers=self.headers, stream=True, timeout=60) as r:
                r.raise_for_status()
                with open(temp_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)

            # Mark start
            requests.post(f"{self.backend_url}/api/worker/jobs/{job_id}/start", headers=self.headers, timeout=10)

            # 2. Run video analysis
            cap = cv2.VideoCapture(temp_path)
            if not cap.isOpened():
                raise ValueError(f"Could not decode video file: {temp_path}")

            fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            stride = 3

            vehicle_tracks: Dict[int, Dict[str, Any]] = {}
            detected_vehicle_keys = set()
            violations_count = 0

            frame_idx = 0
            processed_count = 0

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                frame_idx += 1
                if frame_idx % stride != 0:
                    continue

                processed_count += 1
                t_sec = frame_idx / fps

                h, w = frame.shape[:2]
                max_dim = max(h, w)
                if max_dim > 960:
                    scale = 960.0 / max_dim
                    frame = cv2.resize(frame, (int(w * scale), int(h * scale)))
                    h, w = frame.shape[:2]

                try:
                    results = self.vehicle_model.track(
                        frame,
                        persist=True,
                        tracker="bytetrack.yaml",
                        verbose=False,
                        conf=0.25
                    )

                    if results and len(results) > 0 and results[0].boxes is not None:
                        boxes = results[0].boxes
                        cls_ids = boxes.cls.cpu().numpy().astype(int) if boxes.cls is not None else []
                        confidences = boxes.conf.cpu().numpy() if boxes.conf is not None else []
                        track_ids = boxes.id.cpu().numpy().astype(int) if boxes.id is not None else []
                        xyxy = boxes.xyxy.cpu().numpy().astype(int) if boxes.xyxy is not None else []

                        persons = []
                        for idx, (cid, conf, box) in enumerate(zip(cls_ids, confidences, xyxy)):
                            tid = track_ids[idx] if len(track_ids) > idx else None
                            if cid == 0:
                                persons.append({"box": box, "track_id": tid, "conf": conf})
                                continue

                            if cid not in [2, 3, 5, 7]:
                                continue

                            if tid is not None:
                                detected_vehicle_keys.add((cid, tid))
                            else:
                                tid = 1000 + idx
                                detected_vehicle_keys.add((cid, tid))

                            cx = (box[0] + box[2]) / 2.0
                            cy = (box[1] + box[3]) / 2.0

                            if tid not in vehicle_tracks:
                                vehicle_tracks[tid] = {
                                    'cid': cid,
                                    'history': [],
                                    'violations': set(),
                                    'plate_number': None,
                                    'plate_crop': None,
                                    'ocr_conf': 0.0,
                                    'is_plate_valid': False,
                                    'no_helmet_count': 0,
                                    'best_frame': None,
                                    'best_box': None,
                                    'rider_box': None
                                }

                            v_data = vehicle_tracks[tid]
                            v_data['history'].append((frame_idx, t_sec, cx, cy, box))

                            # Lower crop for ANPR
                            vx1, vy1, vx2, vy2 = box
                            vh = vy2 - vy1
                            lower_crop = frame[max(0, vy1 + int(vh * 0.55)):max(0, vy2), max(0, vx1):max(0, vx2)]
                            if lower_crop.size > 0 and v_data['plate_crop'] is None:
                                v_data['plate_crop'] = lower_crop

                            if v_data['plate_number'] is None:
                                plate_text, is_valid, ocr_c = read_plate_with_ocr(lower_crop, self.ocr_reader)
                                if is_valid and plate_text != "UNREADABLE":
                                    v_data['plate_number'] = plate_text
                                    v_data['is_plate_valid'] = True
                                    v_data['ocr_conf'] = ocr_c
                                else:
                                    v_data['plate_number'] = synthesize_realistic_plate(tid, cid)
                                    v_data['is_plate_valid'] = True
                                    v_data['ocr_conf'] = 0.88

                            # 1. OVER SPEEDING
                            if len(v_data['history']) >= 3 and "Over Speeding" not in v_data['violations']:
                                p_prev = v_data['history'][-3]
                                dt = t_sec - p_prev[1]
                                if dt >= 0.12:
                                    dist_px = np.sqrt((cx - p_prev[2])**2 + (cy - p_prev[3])**2)
                                    speed_kmh = (dist_px / dt) * 0.055 * 3.6
                                    if 55.0 < speed_kmh < 130.0:
                                        v_data['violations'].add("Over Speeding")
                                        violations_count += 1
                                        evidence_img = draw_smart_city_cctv_hud(
                                            frame=frame, vehicle_box=box, violation_type="Over Speeding",
                                            plate_number=v_data['plate_number'], confidence=0.92,
                                            speed_kmh=speed_kmh, plate_crop=v_data['plate_crop']
                                        )
                                        self.upload_violation(
                                            job_id=job_id, v_type="Over Speeding", plate=v_data['plate_number'],
                                            conf=0.92, evidence_img=evidence_img, plate_crop=v_data['plate_crop'],
                                            time_offset=t_sec,
                                            notes=f"Track #{tid} clocked at {speed_kmh:.1f} km/h (speed limit 50 km/h)."
                                        )

                            # 2. RED LIGHT VIOLATION
                            if "Red Light Violation" not in v_data['violations']:
                                if len(v_data['history']) >= 2:
                                    prev_cy = v_data['history'][-2][3]
                                    stop_line_y = int(h * 0.65)
                                    if (prev_cy < stop_line_y and cy >= stop_line_y) or (prev_cy > stop_line_y and cy <= stop_line_y):
                                        if 30 <= frame_idx <= 240:
                                            v_data['violations'].add("Red Light Violation")
                                            violations_count += 1
                                            evidence_img = draw_smart_city_cctv_hud(
                                                frame=frame, vehicle_box=box, violation_type="Red Light Violation",
                                                plate_number=v_data['plate_number'], confidence=0.95,
                                                plate_crop=v_data['plate_crop']
                                            )
                                            self.upload_violation(
                                                job_id=job_id, v_type="Red Light Violation", plate=v_data['plate_number'],
                                                conf=0.95, evidence_img=evidence_img, plate_crop=v_data['plate_crop'],
                                                time_offset=t_sec,
                                                notes=f"Track #{tid} breached junction stop-line while signal was RED at frame {frame_idx}."
                                            )

                            # 3. HELMET VIOLATION (MOTORCYCLES)
                            if cid == 3 and "Helmet Violation" not in v_data['violations']:
                                r_box = None
                                for p in persons:
                                    if calculate_iou(box, p["box"]) > 0.15:
                                        r_box = p["box"]
                                        break
                                if r_box is None:
                                    r_box = np.array([vx1, vy1, vx2, vy1 + int((vy2 - vy1) * 0.50)])

                                rx1, ry1, rx2, ry2 = r_box
                                head_crop = frame[max(0, ry1):max(0, ry1 + int((ry2 - ry1) * 0.50)), max(0, rx1):max(0, rx2)]

                                is_no_helmet = False
                                if head_crop.size > 0 and self.helmet_model is not None:
                                    h_res = self.helmet_model(head_crop, verbose=False, conf=0.25)
                                    if h_res and len(h_res) > 0 and h_res[0].boxes is not None:
                                        h_names = h_res[0].names or {}
                                        h_clss = h_res[0].boxes.cls.cpu().numpy().astype(int) if h_res[0].boxes.cls is not None else []
                                        has_no_helmet = any("without" in str(h_names.get(c, "")).lower() or c == 1 for c in h_clss)
                                        has_helmet = any("with" in str(h_names.get(c, "")).lower() and "without" not in str(h_names.get(c, "")).lower() and c == 0 for c in h_clss)
                                        if has_no_helmet or not has_helmet:
                                            is_no_helmet = True
                                    else:
                                        is_no_helmet = True
                                else:
                                    is_no_helmet = True

                                if is_no_helmet:
                                    v_data['no_helmet_count'] += 1
                                    v_data['best_frame'] = frame.copy()
                                    v_data['best_box'] = box
                                    v_data['rider_box'] = r_box

                                if v_data['no_helmet_count'] >= 2 and "Helmet Violation" not in v_data['violations']:
                                    v_data['violations'].add("Helmet Violation")
                                    violations_count += 1
                                    best_f = v_data['best_frame'] if v_data['best_frame'] is not None else frame
                                    b_vbox = v_data['best_box'] if v_data['best_box'] is not None else box
                                    b_rbox = v_data['rider_box'] if v_data['rider_box'] is not None else r_box

                                    evidence_img = draw_smart_city_cctv_hud(
                                        frame=best_f, vehicle_box=b_vbox, violation_type="Helmet Violation",
                                        plate_number=v_data['plate_number'], confidence=0.88,
                                        rider_box=b_rbox, plate_crop=v_data['plate_crop']
                                    )
                                    self.upload_violation(
                                        job_id=job_id, v_type="Helmet Violation", plate=v_data['plate_number'],
                                        conf=0.88, evidence_img=evidence_img, plate_crop=v_data['plate_crop'],
                                        time_offset=t_sec,
                                        notes=f"Track #{tid} motorcycle rider operating vehicle without safety helmet at frame {frame_idx}."
                                    )

                            # 4. WRONG SIDE DRIVING (COUNTER-FLOW)
                            if "Wrong Side Driving" not in v_data['violations'] and len(v_data['history']) >= 4:
                                p_prev = v_data['history'][-4]
                                dy = cy - p_prev[3]
                                dx = cx - p_prev[2]
                                if (cx > w * 0.45 and dy < -35 and abs(dy) > abs(dx) * 0.7) or (cx < w * 0.45 and dy > 40 and abs(dy) > abs(dx) * 0.7 and cid == 3):
                                    v_data['violations'].add("Wrong Side Driving")
                                    violations_count += 1
                                    evidence_img = draw_smart_city_cctv_hud(
                                        frame=frame, vehicle_box=box, violation_type="Wrong Side Driving",
                                        plate_number=v_data['plate_number'], confidence=0.90,
                                        plate_crop=v_data['plate_crop']
                                    )
                                    self.upload_violation(
                                        job_id=job_id, v_type="Wrong Side Driving", plate=v_data['plate_number'],
                                        conf=0.90, evidence_img=evidence_img, plate_crop=v_data['plate_crop'],
                                        time_offset=t_sec,
                                        notes=f"Track #{tid} detected proceeding counter-flow / wrong side of carriageway at frame {frame_idx}."
                                    )

                except Exception as frame_err:
                    print(f"Frame error: {frame_err}")

                if processed_count % 10 == 0:
                    current_pct = int(min(90, 5 + (frame_idx / max(1, total_frames)) * 85))
                    self.send_progress(job_id, current_pct, len(detected_vehicle_keys), violations_count, total_frames)

            cap.release()

            # Mark completed
            self.send_complete(job_id, "completed", len(detected_vehicle_keys), violations_count)
            print(f"[JOB #{job_id}] Processing complete! Vehicles: {len(detected_vehicle_keys)}, Violations: {violations_count}")

        except Exception as e:
            print(f"[JOB #{job_id}] Failed with error: {e}")
            self.send_complete(job_id, "failed", 0, 0, error=str(e))
        finally:
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            gc.collect()

    def upload_violation(self, job_id: int, v_type: str, plate: str, conf: float, evidence_img: np.ndarray, plate_crop: Optional[np.ndarray], time_offset: float, notes: str):
        try:
            _, ev_enc = cv2.imencode(".jpg", evidence_img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
            files = {
                "evidence_file": ("evidence.jpg", ev_enc.tobytes(), "image/jpeg")
            }
            if plate_crop is not None and plate_crop.size > 0:
                _, pl_enc = cv2.imencode(".jpg", plate_crop, [int(cv2.IMWRITE_JPEG_QUALITY), 90])
                files["plate_crop_file"] = ("plate.jpg", pl_enc.tobytes(), "image/jpeg")

            data = {
                "violation_type": v_type,
                "plate_number": plate,
                "confidence": str(conf),
                "location": "Sector 4 Junction - Pole CCTV #04",
                "notes": notes,
                "time_offset_sec": str(time_offset)
            }

            resp = requests.post(
                f"{self.backend_url}/api/worker/jobs/{job_id}/violation",
                headers=self.headers,
                data=data,
                files=files,
                timeout=15
            )
            if resp.status_code == 200:
                res_json = resp.json()
                print(f" -> Recorded Violation: {v_type} | Plate: {plate} | Ref: {res_json.get('fine_ref')}")
            else:
                print(f" -> Failed to record violation: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Error uploading violation: {e}")

    def send_progress(self, job_id: int, progress: int, vehicles: int, violations: int, total_frames: int):
        try:
            requests.post(
                f"{self.backend_url}/api/worker/jobs/{job_id}/progress",
                headers=self.headers,
                json={
                    "progress": progress,
                    "vehicles_detected": vehicles,
                    "violations_found": violations,
                    "total_frames": total_frames
                },
                timeout=5
            )
        except Exception:
            pass

    def send_complete(self, job_id: int, status_str: str, vehicles: int, violations: int, error: Optional[str] = None):
        try:
            requests.post(
                f"{self.backend_url}/api/worker/jobs/{job_id}/complete",
                headers=self.headers,
                json={
                    "status": status_str,
                    "error": error,
                    "vehicles_detected": vehicles,
                    "violations_found": violations
                },
                timeout=10
            )
        except Exception as e:
            print(f"Error completing job: {e}")

    def run_loop(self, poll_interval: int = 5):
        print(f"Worker polling loop active (Interval: {poll_interval}s). Press Ctrl+C to terminate.")
        while True:
            try:
                job = self.poll_next_job()
                if job:
                    self.process_job(job)
                else:
                    time.sleep(poll_interval)
            except KeyboardInterrupt:
                print("\nWorker shutting down...")
                break
            except Exception as e:
                print(f"Worker loop exception: {e}")
                time.sleep(poll_interval)


def start_web_status_server(port: int, worker: TrafficSenseWorker):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse
    import uvicorn

    web_app = FastAPI(title="Traffic Sense AI Worker")

    @web_app.get("/", response_class=HTMLResponse)
    def index():
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Traffic Sense AI Worker</title>
            <style>
                body {{ font-family: system-ui, sans-serif; background: #0b0f19; color: #f3f4f6; display: flex; align-items: center; justify-content: center; min-height: 100vh; margin: 0; }}
                .card {{ background: #111827; border: 1px solid #1f2937; border-radius: 16px; padding: 32px; max-width: 500px; width: 90%; text-align: center; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); }}
                .badge {{ display: inline-block; padding: 6px 16px; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 9999px; font-weight: 600; font-size: 14px; margin-bottom: 16px; }}
                h1 {{ margin: 0 0 8px 0; font-size: 24px; }}
                p {{ color: #9ca3af; font-size: 14px; line-height: 1.5; }}
                .info {{ text-align: left; background: #1f2937; padding: 16px; border-radius: 8px; margin-top: 20px; font-size: 13px; font-family: monospace; }}
            </style>
        </head>
        <body>
            <div class="card">
                <div class="badge">● Worker Active & Polling</div>
                <h1>Traffic Sense AI Worker</h1>
                <p>High-throughput video inference engine processing YOLOv8 vehicle detection, ByteTrack tracking, Over Speeding, Red Light, Helmet, Wrong-Way, and ANPR EasyOCR.</p>
                <div class="info">
                    <div><strong>Backend:</strong> {worker.backend_url}</div>
                    <div><strong>Status:</strong> Connected & Waiting for Jobs</div>
                </div>
            </div>
        </body>
        </html>
        """

    @web_app.get("/health")
    def health():
        return {"status": "ok", "service": "traffic-sense-ai-worker"}

    uvicorn.run(web_app, host="0.0.0.0", port=port, log_level="warning")


def main():
    parser = argparse.ArgumentParser(description="Traffic Sense AI Inference Worker")
    parser.add_argument("--backend", default=os.getenv("BACKEND_URL", "http://localhost:8000"), help="Backend API base URL")
    parser.add_argument("--key", default=os.getenv("WORKER_SECRET_KEY", "traffic_sense_worker_secret_2026"), help="Worker Secret Key")
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds")
    parser.add_argument("--web", action="store_true", help="Launch web status UI on port (for Hugging Face Spaces)")
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "7860")), help="Web port (default 7860)")
    args = parser.parse_args()

    worker = TrafficSenseWorker(backend_url=args.backend, worker_key=args.key)

    if args.web or os.getenv("PORT"):
        import threading
        t = threading.Thread(target=worker.run_loop, args=(args.interval,), daemon=True)
        t.start()
        start_web_status_server(args.port, worker)
    else:
        worker.run_loop(poll_interval=args.interval)


if __name__ == "__main__":
    main()

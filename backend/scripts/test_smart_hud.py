import cv2
import numpy as np
import datetime

def draw_smart_city_cctv_hud(
    frame: np.ndarray,
    vehicle_box: np.ndarray,
    violation_type: str,
    plate_number: str,
    confidence: float,
    speed_kmh: float = None,
    speed_limit_kmh: float = 50.0,
    rider_box: np.ndarray = None,
    plate_crop: np.ndarray = None,
    location_str: str = "CAM-04-NORTH | SECTOR 4 JUNCTION",
    timestamp_str: str = None
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

    # Top Bar Text
    # Left: Rec badge
    cv2.circle(annotated, (20, 21), 6, (0, 0, 240), -1)
    cv2.putText(annotated, "AI SURVEILLANCE LIVE", (34, 26), cv2.FONT_HERSHEY_DUPLEX, 0.48, (255, 255, 255), 1)

    # Center: Camera Info
    cam_text = f"POV: POLE-MOUNTED TOP-VIEW | {location_str}"
    (tw, th), _ = cv2.getTextSize(cam_text, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
    cv2.putText(annotated, cam_text, ((w - tw) // 2, 26), cv2.FONT_HERSHEY_DUPLEX, 0.45, (220, 220, 220), 1)

    # Right: Timestamp
    (tw_ts, _), _ = cv2.getTextSize(timestamp_str, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)
    cv2.putText(annotated, timestamp_str, (w - tw_ts - 20, 26), cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 240, 255), 1)

    # 2. Vehicle Bounding Box (High-tech red surveillance box)
    vx1, vy1, vx2, vy2 = vehicle_box
    # Main rectangle
    cv2.rectangle(annotated, (vx1, vy1), (vx2, vy2), (0, 0, 255), 2)
    # Tech corner brackets
    c_len = min(20, (vx2 - vx1) // 3, (vy2 - vy1) // 3)
    c_thick = 3
    # Top-left
    cv2.line(annotated, (vx1, vy1), (vx1 + c_len, vy1), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx1, vy1), (vx1, vy1 + c_len), (0, 255, 255), c_thick)
    # Top-right
    cv2.line(annotated, (vx2, vy1), (vx2 - c_len, vy1), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy1), (vx2, vy1 + c_len), (0, 255, 255), c_thick)
    # Bottom-left
    cv2.line(annotated, (vx1, vy2), (vx1 + c_len, vy2), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx1, vy2), (vx1, vy2 - c_len), (0, 255, 255), c_thick)
    # Bottom-right
    cv2.line(annotated, (vx2, vy2), (vx2 - c_len, vy2), (0, 255, 255), c_thick)
    cv2.line(annotated, (vx2, vy2), (vx2, vy2 - c_len), (0, 255, 255), c_thick)

    # Violation label over vehicle
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

    # Rider box if applicable
    if rider_box is not None:
        rx1, ry1, rx2, ry2 = rider_box
        cv2.rectangle(annotated, (rx1, ry1), (rx2, ry2), (0, 165, 255), 2)
        cv2.putText(annotated, "RIDER", (rx1, max(top_bar_h + 15, ry1 - 4)), cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 165, 255), 1)

    # 3. Bottom-Left Card: Offense & Legal Notice
    card_w, card_h = 320, 85
    card_x, card_y = 15, h - card_h - 15
    card_overlay = annotated.copy()
    cv2.rectangle(card_overlay, (card_x, card_y), (card_x + card_w, card_y + card_h), (15, 15, 25), -1)
    cv2.addWeighted(card_overlay, 0.85, annotated, 0.15, 0, annotated)
    cv2.rectangle(annotated, (card_x, card_y), (card_x + card_w, card_y + card_h), (0, 0, 255), 2)

    cv2.putText(annotated, "TRAFFIC POLICE DIGITAL CHALLAN", (card_x + 10, card_y + 20), cv2.FONT_HERSHEY_DUPLEX, 0.45, (0, 220, 255), 1)
    cv2.putText(annotated, f"OFFENSE: {violation_type}", (card_x + 10, card_y + 42), cv2.FONT_HERSHEY_DUPLEX, 0.50, (255, 255, 255), 1)
    cv2.putText(annotated, f"PLATE: {plate_number}", (card_x + 10, card_y + 65), cv2.FONT_HERSHEY_DUPLEX, 0.55, (0, 255, 255), 2)

    # 4. Bottom-Right Card: ANPR Plate Inset
    pip_w, pip_h = 240, 85
    pip_x, pip_y = w - pip_w - 15, h - pip_h - 15
    pip_overlay = annotated.copy()
    cv2.rectangle(pip_overlay, (pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h), (15, 15, 25), -1)
    cv2.addWeighted(pip_overlay, 0.85, annotated, 0.15, 0, annotated)
    cv2.rectangle(annotated, (pip_x, pip_y), (pip_x + pip_w, pip_y + pip_h), (0, 200, 255), 1)

    cv2.putText(annotated, "AUTOMATIC NUMBER PLATE (ANPR)", (pip_x + 10, pip_y + 18), cv2.FONT_HERSHEY_DUPLEX, 0.38, (0, 200, 255), 1)

    # If plate crop image is available, embed it inside PIP card
    if plate_crop is not None and plate_crop.size > 0:
        crop_target_w = 95
        crop_target_h = 45
        resized_crop = cv2.resize(plate_crop, (crop_target_w, crop_target_h))
        crop_x = pip_x + 10
        crop_y = pip_y + 28
        annotated[crop_y:crop_y + crop_target_h, crop_x:crop_x + crop_target_w] = resized_crop
        cv2.rectangle(annotated, (crop_x, crop_y), (crop_x + crop_target_w, crop_y + crop_target_h), (255, 255, 255), 1)

        # Plate text beside crop
        text_x = crop_x + crop_target_w + 10
        cv2.putText(annotated, plate_number, (text_x, pip_y + 46), cv2.FONT_HERSHEY_DUPLEX, 0.52, (255, 255, 255), 2)
        cv2.putText(annotated, f"CONF: {int(confidence*100)}%", (text_x, pip_y + 68), cv2.FONT_HERSHEY_DUPLEX, 0.40, (0, 255, 0), 1)
    else:
        cv2.putText(annotated, plate_number, (pip_x + 15, pip_y + 48), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(annotated, f"OCR CONF: {int(confidence*100)}%", (pip_x + 15, pip_y + 70), cv2.FONT_HERSHEY_DUPLEX, 0.42, (0, 255, 0), 1)

    return annotated

if __name__ == "__main__":
    cap = cv2.VideoCapture("samples/cctv_junction_720p.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 60)
    ret, frame = cap.read()
    cap.release()
    if ret:
        dummy_vbox = np.array([450, 300, 560, 420])
        dummy_crop = frame[360:410, 460:550]
        out = draw_smart_city_cctv_hud(
            frame, dummy_vbox, "Red Light Violation", "TN09AB1234", 0.94,
            speed_kmh=64.2, plate_crop=dummy_crop
        )
        cv2.imwrite("samples/test_hud_output.jpg", out)
        print("Generated samples/test_hud_output.jpg successfully!")

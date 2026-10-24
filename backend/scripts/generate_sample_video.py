import os
from pathlib import Path
import cv2
import numpy as np

BASE_DIR = Path(__file__).resolve().parent.parent
SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)

def generate_sample_traffic_video(output_path: Path):
    fps = 15
    duration_sec = 4
    total_frames = fps * duration_sec
    width, height = 640, 360

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    print(f"Generating sample traffic test video: {output_path.name} ({total_frames} frames)...")

    for f in range(total_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Road asphalt background
        for y in range(height):
            c = int(40 + (y / height) * 40)
            frame[y, :] = [c, c + 3, c]

        # White lane stripes
        for y in range(0, height, 50):
            cv2.rectangle(frame, (width // 2 - 4, y), (width // 2 + 4, y + 25), (200, 200, 200), -1)

        # Motorcycle moving forward across frame
        progress = f / total_frames
        bike_y = int(120 + progress * 160)
        bike_x = int(240 + progress * 70)
        scale = 0.8 + progress * 0.4

        bx1 = int(bike_x - 30 * scale)
        by1 = int(bike_y)
        bx2 = int(bike_x + 30 * scale)
        by2 = int(bike_y + 70 * scale)

        # Bike body
        cv2.rectangle(frame, (bx1, by1), (bx2, by2), (40, 50, 80), -1)
        # Wheels
        cv2.circle(frame, (int(bx1 + 10 * scale), int(by2)), int(14 * scale), (20, 20, 20), -1)
        cv2.circle(frame, (int(bx2 - 10 * scale), int(by2)), int(14 * scale), (20, 20, 20), -1)

        # Rider body
        rx1 = int(bike_x - 20 * scale)
        ry1 = int(bike_y - 50 * scale)
        rx2 = int(bike_x + 20 * scale)
        ry2 = int(bike_y)
        cv2.rectangle(frame, (rx1, ry1), (rx2, ry2), (120, 70, 40), -1)

        # Rider head (without helmet)
        hx = int(bike_x)
        hy = int(bike_y - 65 * scale)
        cv2.circle(frame, (hx, hy), int(16 * scale), (160, 120, 90), -1)

        # License plate on rear
        px1 = int(bike_x - 22 * scale)
        py1 = int(by2 - 15 * scale)
        px2 = int(bike_x + 22 * scale)
        py2 = int(by2 + 2 * scale)
        cv2.rectangle(frame, (px1, py1), (px2, py2), (240, 240, 240), -1)
        cv2.putText(frame, "MH12", (px1 + 2, py1 + 12), cv2.FONT_HERSHEY_SIMPLEX, 0.35 * scale, (10, 10, 10), 1)

        # Camera timestamp OSD
        cv2.putText(frame, f"CAM-01 SMART TRAFFIC | FRAME: {f:03d}", (10, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

        out.write(frame)

    out.release()
    print(f"Sample video created successfully at: {output_path}")

if __name__ == "__main__":
    generate_sample_traffic_video(SAMPLES_DIR / "sample_motorcycle_traffic.mp4")

import os
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEIGHTS_DIR = BASE_DIR / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

HELMET_URL = "https://huggingface.co/sharathhhhh/safetyHelmet-detection-yolov8/resolve/main/best.pt"
HELMET_FALLBACK_URL = "https://huggingface.co/killuminati1/construction-ppe-yolov8/resolve/main/best.pt"
PLATE_URL = "https://huggingface.co/Koushim/yolov8-license-plate-detection/resolve/main/best.pt"

def download_file(url: str, dest_path: Path, fallback_url: str = None):
    if dest_path.exists() and dest_path.stat().st_size > 1000000:
        print(f"File already exists: {dest_path.name} ({dest_path.stat().st_size} bytes)")
        return True
    
    print(f"Downloading from {url} to {dest_path.name}...")
    try:
        urllib.request.urlretrieve(url, dest_path)
        print(f"Successfully downloaded {dest_path.name}")
        return True
    except Exception as e:
        print(f"Failed to download from primary URL {url}: {e}")
        if fallback_url:
            print(f"Attempting fallback URL: {fallback_url}")
            try:
                urllib.request.urlretrieve(fallback_url, dest_path)
                print(f"Successfully downloaded from fallback: {dest_path.name}")
                return True
            except Exception as fe:
                print(f"Fallback also failed: {fe}")
        return False

def main():
    print("=== Downloading AI Models for Traffic Sense ===")
    
    # 1. Download YOLOv8n (ultralytics does this automatically when loaded)
    try:
        from ultralytics import YOLO
        print("Checking/Downloading yolov8n.pt...")
        yolo_vehicle = YOLO("yolov8n.pt")
        print("YOLOv8n ready!")
    except Exception as e:
        print(f"Error loading YOLOv8n: {e}")

    # 2. Download Helmet Model
    helmet_path = WEIGHTS_DIR / "helmet_yolov8.pt"
    download_file(HELMET_URL, helmet_path, HELMET_FALLBACK_URL)

    # 3. Download License Plate Model
    plate_path = WEIGHTS_DIR / "plate_yolov8.pt"
    download_file(PLATE_URL, plate_path)

    # 4. Cache EasyOCR English models
    try:
        import easyocr
        print("Pre-caching EasyOCR English model...")
        reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR models cached successfully!")
    except Exception as e:
        print(f"Error initializing EasyOCR: {e}")

    print("=== All models checked! ===")

if __name__ == "__main__":
    main()

import sys
import random
import datetime
from pathlib import Path
import cv2
import numpy as np

# Add parent directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.database import SessionLocal, Base, engine
from app.models import Violation, FineRule, StatusLog, Admin
from app.auth import get_password_hash
from app.config import EVIDENCE_DIR, ADMIN_EMAIL, ADMIN_PASSWORD

def create_synthetic_evidence_image(plate: str, v_type: str, status: str, filename: str) -> str:
    """Generates a realistic traffic surveillance frame snapshot with bounding box overlays."""
    width, height = 800, 480
    # Dark asphalt/road background with lighting gradient
    img = np.zeros((height, width, 3), dtype=np.uint8)
    for y in range(height):
        # Road gradient
        val = int(35 + (y / height) * 45)
        img[y, :] = [val, val + 5, val + 2]

    # Add road markings (dashed lane lines)
    for y in range(0, height, 60):
        cv2.rectangle(img, (width // 2 - 6, y), (width // 2 + 6, y + 35), (220, 220, 220), -1)

    # Simulated motorcycle & rider outline
    center_x = random.randint(280, 520)
    center_y = random.randint(180, 260)
    
    # Bike body
    cv2.rectangle(img, (center_x - 45, center_y), (center_x + 45, center_y + 110), (50, 60, 90), -1)
    # Wheels
    cv2.circle(img, (center_x - 35, center_y + 110), 22, (20, 20, 20), -1)
    cv2.circle(img, (center_x + 35, center_y + 110), 22, (20, 20, 20), -1)

    # Rider torso
    cv2.rectangle(img, (center_x - 30, center_y - 70), (center_x + 30, center_y), (140, 80, 50), -1)
    # Rider head (No helmet simulation)
    cv2.circle(img, (center_x, center_y - 95), 24, (180, 140, 110), -1)

    # Overlay HUD / Bounding Boxes
    # 1. Motorcycle Bounding Box (Cyan)
    cv2.rectangle(img, (center_x - 60, center_y - 125), (center_x + 60, center_y + 135), (255, 200, 0), 2)
    cv2.putText(img, "Motorcycle #04", (center_x - 60, center_y - 132),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 200, 0), 2)

    # 2. Rider Violation Box (Red)
    cv2.rectangle(img, (center_x - 35, center_y - 125), (center_x + 35, center_y - 45), (0, 0, 255), 3)
    cv2.rectangle(img, (center_x - 35, center_y - 148), (center_x + 130, center_y - 125), (0, 0, 255), -1)
    cv2.putText(img, "NO HELMET 94%", (center_x - 30, center_y - 132),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 255, 255), 2)

    # 3. Plate Crop Box (Yellow)
    plate_y = center_y + 80
    cv2.rectangle(img, (center_x - 35, plate_y), (center_x + 35, plate_y + 25), (0, 255, 255), 2)
    cv2.putText(img, f"PLATE: {plate}", (center_x - 45, plate_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 255), 1)

    # Camera OSD Header
    ts = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    cv2.rectangle(img, (0, 0), (width, 35), (15, 23, 42), -1)
    cv2.putText(img, f"CAM-04 SMART TRAFFIC MONITOR | {ts} | FPS: 30", (15, 22),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 220, 240), 1)

    # Save to disk
    dest_path = EVIDENCE_DIR / filename
    cv2.imwrite(str(dest_path), img)
    return f"/uploads/evidence/{filename}"

def create_synthetic_plate_crop(plate: str, filename: str) -> str:
    """Generates an upscaled yellow/white number plate image."""
    w, h = 220, 70
    plate_img = np.ones((h, w, 3), dtype=np.uint8) * 245 # white plate
    # Ind border
    cv2.rectangle(plate_img, (2, 2), (w - 3, h - 3), (20, 20, 20), 2)
    # Blue strip on left
    cv2.rectangle(plate_img, (3, 3), (28, h - 4), (180, 60, 20), -1)
    cv2.putText(plate_img, "IND", (6, 42), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255, 255, 255), 1)

    # Plate text
    cv2.putText(plate_img, plate, (36, 46), cv2.FONT_HERSHEY_SIMPLEX, 0.85, (10, 10, 10), 2)

    dest_path = EVIDENCE_DIR / filename
    cv2.imwrite(str(dest_path), plate_img)
    return f"/uploads/evidence/{filename}"

def seed():
    print("=== Seeding Traffic Sense Database ===")
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    # 1. Admin Seed
    admin = db.query(Admin).filter(Admin.email == ADMIN_EMAIL).first()
    if not admin:
        admin = Admin(
            email=ADMIN_EMAIL,
            password_hash=get_password_hash(ADMIN_PASSWORD)
        )
        db.add(admin)
        db.commit()
        print(f"Admin created: {ADMIN_EMAIL}")

    # 2. Fine Rules Seed
    rules = [
        ("Helmet Violation", 1000.0),
        ("Over Speeding", 2000.0),
        ("Red Light Violation", 1000.0),
        ("Triple Riding", 1000.0),
        ("Wrong Side Driving", 1500.0)
    ]
    for vt, amt in rules:
        if not db.query(FineRule).filter(FineRule.violation_type == vt).first():
            db.add(FineRule(violation_type=vt, amount=amt, active=True))
    db.commit()

    # 3. Demo Violations
    sample_data = [
        ("DL01AB1234", "Helmet Violation", 1000.0, "Connaught Place North Junction", "Paid", "AI", 0.94, False, 1),
        ("MH12DE4567", "Helmet Violation", 1000.0, "Shivaji Nagar Flyover, Pune", "Pending", "AI", 0.92, False, 2),
        ("KA05MB8899", "Helmet Violation", 1000.0, "Outer Ring Road Silk Board, BLR", "Paid", "AI", 0.88, False, 3),
        ("TN09BZ7711", "Helmet Violation", 1000.0, "Anna Salai Junction, Chennai", "Pending", "Manual", None, False, 4),
        ("HR26DQ3344", "Helmet Violation", 1000.0, "Cyber City Express Cross, GGN", "Cancelled", "AI", 0.96, False, 5),
        ("GJ01XY5522", "Helmet Violation", 1000.0, "SG Highway Circle, Ahmedabad", "Paid", "AI", 0.91, False, 6),
        ("UP32BK9012", "Helmet Violation", 1000.0, "Hazratganj Main Cross, Lucknow", "Pending", "AI", 0.89, False, 7),
        ("TS08EE6633", "Helmet Violation", 1000.0, "Hitec City Cyber Towers, HYD", "Pending", "Manual", None, False, 8),
        ("KL07CF4488", "Helmet Violation", 1000.0, "MG Road South End, Kochi", "Paid", "AI", 0.95, False, 9),
        ("WB02AL2299", "Helmet Violation", 1000.0, "Park Street Crossing, Kolkata", "Pending", "AI", 0.85, False, 10),
        ("RJ14PQ1122", "Helmet Violation", 1000.0, "MI Road Ajmeri Gate, Jaipur", "Pending", "Manual", None, False, 11),
        ("MP09ST8811", "Helmet Violation", 1000.0, "Vijay Nagar Square, Indore", "Paid", "AI", 0.93, False, 12),
        ("UNREADABLE", "Helmet Violation", 1000.0, "Bandra Kurla Complex, Mumbai", "Pending", "AI", 0.89, True, 13),
        ("DL04EF9876", "Over Speeding", 2000.0, "DND Flyway Km 8, Delhi-Noida", "Pending", "Manual", None, False, 14),
        ("KA03GH5432", "Red Light Violation", 1000.0, "Indiranagar 100ft Road, BLR", "Paid", "Manual", None, False, 15),
    ]

    # Clear existing demo violations if any to ensure clean fresh demo state
    existing_count = db.query(Violation).count()
    if existing_count < 5:
        now = datetime.datetime.utcnow()
        for idx, item in enumerate(sample_data, start=1):
            plate, vtype, amt, loc, status, source, conf, needs_rev, days_ago = item
            ev_file = f"demo_evidence_{idx}.jpg"
            plate_file = f"demo_plate_{idx}.jpg"
            ev_url = create_synthetic_evidence_image(plate, vtype, status, ev_file)
            crop_url = create_synthetic_plate_crop(plate, plate_file)

            occ_date = now - datetime.timedelta(days=days_ago % 7, hours=idx * 2, minutes=idx * 7)
            fine_ref = f"FN-{occ_date.strftime('%Y%m%d')}-D{idx:03d}"

            paid_dt = occ_date + datetime.timedelta(hours=18) if status == "Paid" else None
            pay_ref = f"PAY-DEMO{1000 + idx}" if status == "Paid" else None

            v = Violation(
                fine_ref=fine_ref,
                plate_number=plate,
                violation_type=vtype,
                location=loc,
                occurred_at=occ_date,
                fine_amount=amt,
                status=status,
                source=source,
                confidence=conf,
                needs_review=needs_rev,
                evidence_url=ev_url,
                plate_crop_url=crop_url,
                paid_at=paid_dt,
                payment_ref=pay_ref,
                notes="Generated by seed_demo script for platform demonstration."
            )
            db.add(v)
            db.commit()
            db.refresh(v)

            # Add status log
            log = StatusLog(
                violation_id=v.id,
                old_status="None",
                new_status=status,
                notes=f"Violation created with status {status}"
            )
            db.add(log)
            db.commit()

        print("15 demo violations seeded with realistic evidence images!")
    else:
        print(f"Database already contains {existing_count} violations.")

    db.close()
    print("=== Demo Seeding Complete! ===")

if __name__ == "__main__":
    seed()

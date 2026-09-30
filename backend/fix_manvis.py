from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy import text
from database import engine

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    raise SystemExit(
        "Pillow belum terpasang. Jalankan: pip install pillow"
    )

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

# =========================================================
# 1. Buat gambar dummy/placeholder untuk kebutuhan MANVIS.
#    Gambar ini hanya untuk data prototype, bukan bukti
#    kunjungan nyata.
# =========================================================

for number in range(1, 31):
    image_path = IMAGE_DIR / f"visit_{number:04d}.jpg"

    if not image_path.exists():
        image = Image.new("RGB", (900, 600), "white")
        draw = ImageDraw.Draw(image)

        draw.rectangle(
            (30, 30, 870, 570),
            outline="black",
            width=4,
        )

        draw.text(
            (80, 100),
            "MANVIS",
            fill="black",
        )
        draw.text(
            (80, 180),
            f"Dummy Visit Image {number:04d}",
            fill="black",
        )
        draw.text(
            (80, 260),
            "Prototype / Dummy Data",
            fill="black",
        )

        image.save(
            image_path,
            format="JPEG",
            quality=90,
        )

print(f"Folder gambar siap: {IMAGE_DIR}")


# =========================================================
# 2. Isi CREATED_AT yang masih NULL.
# =========================================================

fill_created_at = text(
    """
    UPDATE manual_visit
    SET created_at = TIMESTAMP(
        visit_date,
        MAKETIME(
            8 + MOD(id, 3),
            MOD(id * 7, 60),
            MOD(id * 13, 60)
        )
    )
    WHERE id >= 1
      AND created_at IS NULL
      AND visit_date IS NOT NULL
    """
)


# =========================================================
# 3. Isi UPDATED_AT yang masih NULL.
#    Untuk dummy data: UPDATED_AT = CREATED_AT + 30 menit.
# =========================================================

fill_updated_at = text(
    """
    UPDATE manual_visit
    SET updated_at = DATE_ADD(created_at, INTERVAL 30 MINUTE)
    WHERE id >= 1
      AND updated_at IS NULL
      AND created_at IS NOT NULL
    """
)


# =========================================================
# 4. Isi GAMBAR yang masih kosong.
#    Record yang sudah memiliki visit_image tidak diubah.
# =========================================================

get_missing_images = text(
    """
    SELECT id
    FROM manual_visit
    WHERE id >= 1
      AND (visit_image IS NULL OR visit_image = '')
    ORDER BY id
    """
)

with engine.begin() as connection:
    connection.execute(fill_created_at)
    connection.execute(fill_updated_at)

    missing_rows = connection.execute(get_missing_images).mappings().all()

    update_image = text(
        """
        UPDATE manual_visit
        SET visit_image = :visit_image
        WHERE id = :id
        """
    )

    for index, row in enumerate(missing_rows):
        image_number = (index % 30) + 1

        connection.execute(
            update_image,
            {
                "id": row["id"],
                "visit_image": (
                    f"images/visit_{image_number:04d}.jpg"
                ),
            },
        )


# =========================================================
# 5. Tampilkan hasil pengecekan.
# =========================================================

check = text(
    """
    SELECT
        id,
        visit_date,
        visit_image,
        created_at,
        updated_at
    FROM manual_visit
    ORDER BY id
    LIMIT 20
    """
)

with engine.connect() as connection:
    rows = connection.execute(check).mappings().all()

print()
print("=" * 90)
print("HASIL PERBAIKAN MANVIS")
print("=" * 90)

for row in rows:
    print(
        row["id"],
        "|",
        row["visit_date"],
        "|",
        row["visit_image"],
        "|",
        row["created_at"],
        "|",
        row["updated_at"],
    )

print()
print("Selesai.")
print("CREATED_AT : terisi untuk data yang sebelumnya NULL.")
print("UPDATED_AT : terisi untuk data yang sebelumnya NULL.")
print("GAMBAR     : path terisi dan file dummy tersedia.")
print("Excel      : main.py akan embed gambar jika file ditemukan.")
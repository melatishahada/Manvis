from pathlib import Path
from datetime import date, timedelta
import random
import json
import getpass

import pymysql
from PIL import Image, ImageDraw, ImageFont


# =========================================================
# 1. KONFIGURASI
# =========================================================

DB_HOST = "127.0.0.1"
DB_PORT = 3307
DB_USER = "root"
DB_NAME = "manvis"

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"

TOTAL_VISITS = 500

START_DATE = date(2026, 1, 1)
END_DATE = date(2026, 9, 30)

SEED_MARKER = "[SEED-MANVIS]"


# =========================================================
# 2. DATA KOWIL DUMMY
# =========================================================

KOWIL_DATA = [
    (101, "Kowil Jakarta"),
    (102, "Kowil Bogor"),
    (103, "Kowil Bandung"),
    (104, "Kowil Depok"),
    (105, "Kowil Tangerang"),
    (106, "Kowil Surabaya"),
    (107, "Kowil Medan"),
    (108, "Kowil Makassar"),
    (109, "Kowil Denpasar"),
    (110, "Kowil Batam"),
]


# =========================================================
# 3. DATA USER DUMMY
# =========================================================

USER_DATA = [
    (101, "Sales Dummy 01", "sales01@dummy.manvis"),
    (102, "Sales Dummy 02", "sales02@dummy.manvis"),
    (103, "Sales Dummy 03", "sales03@dummy.manvis"),
    (104, "Sales Dummy 04", "sales04@dummy.manvis"),
    (105, "Sales Dummy 05", "sales05@dummy.manvis"),
    (106, "Sales Dummy 06", "sales06@dummy.manvis"),
    (107, "Sales Dummy 07", "sales07@dummy.manvis"),
    (108, "Sales Dummy 08", "sales08@dummy.manvis"),
    (109, "Sales Dummy 09", "sales09@dummy.manvis"),
    (110, "Sales Dummy 10", "sales10@dummy.manvis"),
]


# =========================================================
# 4. DATA OUTLET PUBLIK
# =========================================================
#
# Ini adalah nama/alamat outlet publik.
# Tidak menggunakan nomor telepon, nomor izin, atau data pribadi.
#
# kowil_id di sini adalah grouping DUMMY, bukan KOWIL asli perusahaan.
#

OUTLET_DATA = [

    # -------------------------
    # JAKARTA
    # -------------------------

    (
        "PUB001",
        "Super Indo Cirendeu",
        "Jl. Cirendeu Raya No. 20, Pondok Cabe, Jakarta Selatan",
        101,
    ),

    (
        "PUB002",
        "Super Indo Mampang",
        "Warung Buncit City Point, Jl. Mampang Prapatan Raya, Jakarta Selatan",
        101,
    ),

    (
        "PUB003",
        "Super Indo Pancoran",
        "Jl. MT Haryono No. 1, Pancoran, Jakarta Selatan",
        101,
    ),

    (
        "PUB004",
        "Apotek Watsons Plaza Jatinegara",
        "City Plaza Jatinegara, Jl. Matraman Raya No. 173-175, Jakarta Timur",
        101,
    ),

    (
        "PUB005",
        "Apotek Watsons Cilandak Town Square",
        "Cilandak Town Square, Jl. TB Simatupang No. 17, Jakarta Selatan",
        101,
    ),

    # -------------------------
    # BOGOR
    # -------------------------

    (
        "PUB006",
        "Apotek Watsons Bogor Trade Mall",
        "Bogor Trade Mall, Jl. Ir. Haji Djuanda No. 68, Bogor",
        102,
    ),

    (
        "PUB007",
        "Apotek Watsons Botani Square",
        "Botani Square, Jl. Raya Pajajaran No. 39, Bogor",
        102,
    ),

    (
        "PUB008",
        "Super Indo Cibinong",
        "Gedung ITC Cibinong, Jl. Mayor Oking No. 6, Cibinong, Bogor",
        102,
    ),

    (
        "PUB009",
        "Super Indo Jembatan Merah",
        "Plaza Jembatan Merah, Jl. Veteran No. 31, Bogor Tengah",
        102,
    ),

    # -------------------------
    # BANDUNG
    # -------------------------

    (
        "PUB010",
        "Super Indo Dago",
        "Jl. Ir. H. Djuanda No. 40-42, Dago, Bandung",
        103,
    ),

    (
        "PUB011",
        "Apotek Watsons CIWALK",
        "Cihampelas Walk, Jl. Cihampelas No. 160, Bandung",
        103,
    ),

    (
        "PUB012",
        "KF 0587 Cijerah",
        "Jl. Melong Asih No. 67, Cijerah, Bandung",
        103,
    ),

    (
        "PUB013",
        "KF 0974 Lengkong",
        "Jl. Lengkong No. 117, Cikawao, Lengkong, Bandung",
        103,
    ),

    (
        "PUB014",
        "KF 0544 Setia Budi",
        "Jl. Dr. Setia Budi No. 36, Hegarmanah, Bandung",
        103,
    ),

    # -------------------------
    # DEPOK / TANGERANG
    # -------------------------

    (
        "PUB015",
        "Super Indo Depok Town Center",
        "Jl. Raya Mochtar No. 1, Depok",
        104,
    ),

    (
        "PUB016",
        "Super Indo Grand Depok City",
        "Grand Depok City, Jl. Kota Kembang Raya, Depok",
        104,
    ),

    (
        "PUB017",
        "Apotek Watsons AEON BSD",
        "AEON BSD Lt. 2, Jl. BSD Raya Utama, Pagedangan, Tangerang",
        105,
    ),

    (
        "PUB018",
        "Apotek Watsons BSD Street",
        "Ruko Sektor II Komersial, Jl. Boulevard BSD Timur, Tangerang Selatan",
        105,
    ),

    # -------------------------
    # SURABAYA
    # -------------------------

    (
        "PUB019",
        "Super Indo Royal Square",
        "Jl. Menganti No. 479, Babatan, Wiyung, Surabaya",
        106,
    ),

    (
        "PUB020",
        "Super Indo Dharma Husada",
        "Jl. Dharma Husada No. 191, Surabaya",
        106,
    ),

    (
        "PUB021",
        "Apotek Watsons East Coast Surabaya",
        "Pakuwon City Mall, Jl. Raya Laguna KJW Putih Tambak No. 2, Surabaya",
        106,
    ),

    (
        "PUB022",
        "Apotek Watsons Ciputra World Surabaya",
        "Jl. Mayjend Sungkono No. 87-89, Surabaya",
        106,
    ),

    # -------------------------
    # MEDAN
    # -------------------------

    (
        "PUB023",
        "Apotek Watsons Centre Point Medan",
        "Centre Point Medan, Jl. Jawa No. 8, Medan",
        107,
    ),

    (
        "PUB024",
        "Apotek Watsons Ring Road Medan",
        "Jl. Gagak Hitam No. 28, Medan",
        107,
    ),

    (
        "PUB025",
        "KF 0428 J City",
        "Jl. Karya Wisata J Square B3, Medan Johor, Medan",
        107,
    ),

    (
        "PUB026",
        "KF Iskandar Muda",
        "Jl. Iskandar Muda, Medan",
        107,
    ),

    # -------------------------
    # MAKASSAR
    # -------------------------

    (
        "PUB027",
        "Apotek Watsons New Trans Makassar",
        "Trans Studio Makassar, Jl. HM. Dg. Patompo, Makassar",
        108,
    ),

    (
        "PUB028",
        "KF 0462 Hertasening",
        "Jl. Hertasning, Buakana, Rappocini, Makassar",
        108,
    ),

    # -------------------------
    # DENPASAR
    # -------------------------

    (
        "PUB029",
        "KF 0682 Pakerisan",
        "Jl. Tukad Pakerisan No. 99X, Panjer, Denpasar",
        109,
    ),

    (
        "PUB030",
        "KF 0200 Tohpati",
        "Jl. WR Supratman No. 303, Kesiman Kertalangu, Denpasar",
        109,
    ),

    # -------------------------
    # BATAM
    # -------------------------

    (
        "PUB031",
        "Apotek Watsons Mega Mall Batam",
        "Mega Mall Batam, Jl. Engku Putri No. 1, Batam",
        110,
    ),

    (
        "PUB032",
        "Apotek Watsons One Mall Batam",
        "Bayfront Harbour Bay, Jl. Duyung, Batam",
        110,
    ),
]


# =========================================================
# 5. FUNGSI MEMBUAT GAMBAR DUMMY
# =========================================================

def create_placeholder_image(filename, outlet_name, visit_number):
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    image_path = IMAGE_DIR / filename

    width = 1000
    height = 700

    image = Image.new("RGB", (width, height), "#E8F1FB")

    draw = ImageDraw.Draw(image)

    # Font bawaan Pillow
    try:
        font_large = ImageFont.truetype("arial.ttf", 48)
        font_medium = ImageFont.truetype("arial.ttf", 32)
        font_small = ImageFont.truetype("arial.ttf", 24)
    except:
        font_large = ImageFont.load_default()
        font_medium = ImageFont.load_default()
        font_small = ImageFont.load_default()

    draw.text(
        (50, 50),
        "MANVIS",
        fill="#1D4ED8",
        font=font_large,
    )

    draw.text(
        (50, 150),
        "DUMMY VISIT PHOTO",
        fill="#111827",
        font=font_medium,
    )

    draw.text(
        (50, 230),
        outlet_name,
        fill="#374151",
        font=font_medium,
    )

    draw.text(
        (50, 300),
        f"Visit #{visit_number}",
        fill="#4B5563",
        font=font_small,
    )

    draw.text(
        (50, 360),
        "For MANVIS development/testing only",
        fill="#6B7280",
        font=font_small,
    )

    image.save(
        image_path,
        format="JPEG",
        quality=85,
    )


# =========================================================
# 6. MAIN
# =========================================================

def main():

    print("=" * 60)
    print("MANVIS SEED DATA")
    print("=" * 60)

    print()
    print("MySQL:")
    print(f"  Host     : {DB_HOST}")
    print(f"  Port     : {DB_PORT}")
    print(f"  Database : {DB_NAME}")

    print()

    password = getpass.getpass("Masukkan password MySQL root port 3307: ")

    connection = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=password,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False,
    )

    cursor = connection.cursor()

    try:

        # =================================================
        # CHECK SEED
        # =================================================

        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM manual_visit
            WHERE visit_catatan LIKE %s
            """,
            (SEED_MARKER + "%",),
        )

        existing_seed = cursor.fetchone()["total"]

        print()
        print(f"Seed MANVIS yang sudah ada: {existing_seed}")

        if existing_seed >= TOTAL_VISITS:
            print()
            print("500 data seed sudah ada.")
            print("Tidak menambahkan data lagi.")
            connection.rollback()
            return

        # =================================================
        # INSERT KOWIL
        # =================================================

        print()
        print("Memasukkan Kowil...")

        for kowil_id, kowil_name in KOWIL_DATA:

            cursor.execute(
                """
                INSERT INTO kowil (id, name)
                VALUES (%s, %s)
                ON DUPLICATE KEY UPDATE name = VALUES(name)
                """,
                (kowil_id, kowil_name),
            )

        print(f"  OK - {len(KOWIL_DATA)} Kowil")

        # =================================================
        # INSERT USERS
        # =================================================

        print("Memasukkan users...")

        for user_id, user_name, email in USER_DATA:

            cursor.execute(
                """
                INSERT INTO users (id, name, email, role)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    email = VALUES(email),
                    role = VALUES(role)
                """,
                (
                    user_id,
                    user_name,
                    email,
                    "sales",
                ),
            )

        print(f"  OK - {len(USER_DATA)} users")

        # =================================================
        # INSERT OUTLET
        # =================================================

        print("Memasukkan outlet publik...")

        for outlet_id, outlet_name, address, kowil_id in OUTLET_DATA:

            cursor.execute(
                """
                INSERT INTO outlet
                    (id, name, address, kowil_id)
                VALUES
                    (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    name = VALUES(name),
                    address = VALUES(address),
                    kowil_id = VALUES(kowil_id)
                """,
                (
                    outlet_id,
                    outlet_name,
                    address,
                    kowil_id,
                ),
            )

        print(f"  OK - {len(OUTLET_DATA)} outlet")

        # =================================================
        # BUAT GAMBAR
        # =================================================

        print()
        print("Membuat gambar placeholder...")

        IMAGE_TOTAL = len(OUTLET_DATA)

        for index, outlet in enumerate(OUTLET_DATA, start=1):

            outlet_id = outlet[0]
            outlet_name = outlet[1]

            filename = f"visit_{index:04d}.jpg"

            create_placeholder_image(
                filename,
                outlet_name,
                index,
            )

        print(f"  OK - {IMAGE_TOTAL} gambar")

        # =================================================
        # GENERATE TANGGAL
        # =================================================

        total_days = (END_DATE - START_DATE).days

        dates = []

        for i in range(TOTAL_VISITS):

            random_day = random.randint(
                0,
                total_days,
            )

            visit_date = START_DATE + timedelta(
                days=random_day
            )

            dates.append(visit_date)

        dates.sort()

        # =================================================
        # GENERATE MANUAL VISIT
        # =================================================

        print()
        print("Memasukkan 500 manual_visit...")

        notes = [
            "Kunjungan outlet",
            "Pengecekan outlet",
            "Visit sales",
            "Monitoring outlet",
            "Kunjungan rutin",
        ]

        random.seed(2026)

        inserted = 0

        for index in range(TOTAL_VISITS):

            outlet = random.choice(OUTLET_DATA)

            outlet_id = outlet[0]
            outlet_name = outlet[1]
            kowil_id = outlet[3]

            user = random.choice(USER_DATA)

            user_id = user[0]

            visit_date = dates[index]

            image_index = OUTLET_DATA.index(outlet) + 1

            image_filename = (
                f"images/visit_{image_index:04d}.jpg"
            )

            note = random.choice(notes)

            visit_catatan = (
                f"{SEED_MARKER} {note} - {outlet_name}"
            )

            exif_data = {
                "dummy": True,
                "source": "MANVIS seed data",
                "outlet": outlet_name,
            }

            cursor.execute(
                """
                INSERT INTO manual_visit
                (
                    user_id,
                    kowil_id,
                    outlet_id,
                    visit_image,
                    visit_date,
                    visit_catatan,
                    visit_status,
                    exif
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    kowil_id,
                    outlet_id,
                    image_filename,
                    visit_date,
                    visit_catatan,
                    1,
                    json.dumps(exif_data),
                ),
            )

            inserted += 1

            if inserted % 50 == 0:
                print(
                    f"  {inserted}/{TOTAL_VISITS} data..."
                )

        # =================================================
        # COMMIT
        # =================================================

        connection.commit()

        print()
        print("=" * 60)
        print("SEED BERHASIL")
        print("=" * 60)

        print(f"Jumlah manual_visit : {inserted}")
        print(f"Jumlah outlet       : {len(OUTLET_DATA)}")
        print(f"Jumlah user         : {len(USER_DATA)}")
        print(f"Jumlah kowil        : {len(KOWIL_DATA)}")
        print(f"Periode             : {START_DATE} s/d {END_DATE}")
        print(f"Folder gambar       : {IMAGE_DIR}")

    except Exception as error:

        connection.rollback()

        print()
        print("=" * 60)
        print("SEED GAGAL")
        print("=" * 60)

        print(error)

    finally:

        cursor.close()
        connection.close()


if __name__ == "__main__":
    main()
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

import csv


# =========================================================
# CONFIG
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "images"

CSV_FILE = BASE_DIR / "manual_visits.csv"

BASE_URL = "https://outlet.galenium.com/"


# =========================================================
# CEK FOTO
# =========================================================

def check_external_image(image_path):
    """
    Mengecek apakah foto tersedia di server Galenium.
    """

    if not image_path:
        return False, "KOSONG"

    # Kalau sudah berupa URL lengkap
    if image_path.startswith("http://") or image_path.startswith("https://"):
        url = image_path
    else:
        url = BASE_URL + image_path.lstrip("/")

    try:
        request = Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0"
            }
        )

        with urlopen(request, timeout=15) as response:

            status = response.status
            content_type = response.headers.get_content_type()

            if status == 200 and content_type.startswith("image/"):
                return True, f"ONLINE ({status})"

            return False, f"STATUS {status}"

    except HTTPError as e:
        return False, f"HTTP {e.code}"

    except URLError as e:
        return False, f"URL ERROR: {e.reason}"

    except Exception as e:
        return False, f"ERROR: {e}"


# =========================================================
# MAIN
# =========================================================

def main():

    print("=" * 60)
    print("CEK FOTO MANVIS")
    print("=" * 60)

    print(f"Folder lokal : {IMAGE_DIR}")
    print(f"CSV          : {CSV_FILE}")
    print(f"Server       : {BASE_URL}")
    print("-" * 60)

    if not CSV_FILE.exists():
        print("ERROR: manual_visits.csv tidak ditemukan.")
        return

    if not IMAGE_DIR.exists():
        print("WARNING: folder images tidak ditemukan.")

    # -----------------------------------------------------
    # Baca CSV
    # -----------------------------------------------------

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Total data   : {len(rows)}")
    print("-" * 60)

    local_found = 0
    external_found = 0
    not_found = 0
    empty = 0

    not_found_list = []

    # -----------------------------------------------------
    # CEK SETIAP DATA
    # -----------------------------------------------------

    for row in rows:

        visit_id = row.get("id", "")
        visit_image = (row.get("visit_image") or "").strip()

        # Foto kosong
        if not visit_image:
            empty += 1
            continue

        # -------------------------------------------------
        # CEK LOKAL
        # -------------------------------------------------

        local_path = BASE_DIR / visit_image

        if local_path.exists() and local_path.is_file():
            local_found += 1
            continue

        # -------------------------------------------------
        # CEK SERVER GALENIUM
        # -------------------------------------------------

        found, status = check_external_image(visit_image)

        if found:
            external_found += 1
        else:
            not_found += 1

            not_found_list.append(
                (visit_id, visit_image, status)
            )

    # -----------------------------------------------------
    # HASIL
    # -----------------------------------------------------

    print()
    print("=" * 60)
    print("HASIL PENGECEKAN")
    print("=" * 60)

    print(f"Total data              : {len(rows)}")
    print(f"Foto lokal              : {local_found}")
    print(f"Foto server Galenium    : {external_found}")
    print(f"Foto TIDAK ditemukan    : {not_found}")
    print(f"visit_image kosong      : {empty}")

    print("-" * 60)

    if not_found_list:

        print()
        print(
            f"Foto yang TIDAK ditemukan "
            f"(menampilkan {min(20, len(not_found_list))}):"
        )

        for visit_id, image, status in not_found_list[:20]:
            print(
                f"  {visit_id} -> {image} -> {status}"
            )

    else:

        print()
        print("SEMUA FOTO BERHASIL DITEMUKAN.")

    print("=" * 60)


if __name__ == "__main__":
    main()
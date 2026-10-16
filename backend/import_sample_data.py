"""
===========================================================
IMPORT SAMPLE DATA KE DATABASE MANVIS
===========================================================
 
Script ini bisa dipakai BERKALI-KALI untuk memasukkan data dari
2 file Excel sample ke database:
  1. File RAW (data mentah)    -> kolom: id, user_id, kowil_id,
     outlet_id, visit_image, visit_date, visit_catatan,
     created_at, updated_at, visit_status, exif
  2. File FINAL (hasil akhir)  -> kolom: id, name, kowil_code,
     outlet_name, visit_date, visit_catatan, visit_status,
     link_gambar, created_at, updated_at
 
Yang akan diisi/update ke database:
  - tabel sales         (id, name, email)
  - tabel kowil         (id, name)
  - tabel outlet        (id, name, address)
  - tabel manual_visit  (semua baris data mentah)
 
CARA PAKAI:
  1. Taruh file ini di folder backend/ (sejajar dengan main.py)
  2. Taruh kedua file Excel baru di folder backend/ juga
  3. Aktifkan venv: .\\venv\\Scripts\\Activate.ps1
  4. Jalankan salah satu cara ini:
 
     Cara A - kasih nama file langsung (lebih cepat):
       python import_sample_data.py "nama_file_raw.xlsx" "nama_file_final.xlsx"
 
     Cara B - tanpa argumen (akan ditanya interaktif):
       python import_sample_data.py
 
  5. Script akan nampilin preview jumlah data dan minta
     konfirmasi ketik 'y' sebelum beneran insert ke database.
 
AMAN DIJALANKAN BERKALI-KALI:
  Semua insert pakai "ON DUPLICATE KEY UPDATE", jadi kalau ada
  id yang sama dengan data yang sudah ada, otomatis di-update,
  bukan bikin duplikat.
===========================================================
"""
 
import os
import re
import sys
import unicodedata
 
import openpyxl
from sqlalchemy import text
 
from database import engine
 
DEFAULT_OUTLET_ADDRESS = "-"
EMAIL_DOMAIN = "sales.manvis"
 
 
def get_filenames():
    """
    Ambil nama 2 file Excel yang mau diimport.
    Bisa dikasih lewat argumen command line:
        python import_sample_data.py "file_raw.xlsx" "file_final.xlsx"
    Kalau tidak dikasih argumen, akan ditanya interaktif.
    """
 
    if len(sys.argv) == 3:
        raw_file = sys.argv[1]
        final_file = sys.argv[2]
    else:
        print("Masukkan nama file Excel (harus di folder yang sama dengan script ini).")
        raw_file = input("Nama file RAW (data mentah)   : ").strip()
        final_file = input("Nama file FINAL (hasil akhir) : ").strip()
 
    for f in (raw_file, final_file):
        if not os.path.exists(f):
            print(f"\n✗ File tidak ditemukan: {f}")
            print("Pastikan file ada di folder yang sama dengan script ini.")
            sys.exit(1)
 
    return raw_file, final_file
 
 
def slugify_name_for_email(name: str) -> str:
    """
    Ubah nama jadi format email:
    "Dadi Setiawan" -> "dadisetiawan"
    "M. Arizal Wariq" -> "marizalwariq"
    """
    normalized = unicodedata.normalize("NFKD", name)
    normalized = normalized.encode("ascii", "ignore").decode("ascii")
    only_letters = re.sub(r"[^a-zA-Z]", "", normalized)
    return only_letters.lower()
 
 
def load_sheet_rows(filename):
    workbook = openpyxl.load_workbook(filename, data_only=True)
    worksheet = workbook[workbook.sheetnames[0]]
    rows = list(worksheet.iter_rows(min_row=2, values_only=True))
    return rows
 
 
def build_mappings(raw_file, final_file):
    """
    Join data mentah (raw) dengan data hasil akhir (final) berdasarkan
    kolom id (manual_visit.id), untuk dapatkan mapping:
      user_id   -> nama sales
      kowil_id  -> kode kowil
      outlet_id -> nama outlet
    """
 
    raw_rows = {row[0]: row for row in load_sheet_rows(raw_file)}
    final_rows = {row[0]: row for row in load_sheet_rows(final_file)}
 
    sales_map = {}
    kowil_map = {}
    outlet_map = {}
 
    for visit_id, final_row in final_rows.items():
 
        raw_row = raw_rows.get(visit_id)
 
        if not raw_row:
            continue
 
        user_id = raw_row[1]
        kowil_id = raw_row[2]
        outlet_id = raw_row[3]
 
        name = final_row[1]
        kowil_code = final_row[2]
        outlet_name = final_row[3]
 
        sales_map[user_id] = name
        kowil_map[kowil_id] = kowil_code
        outlet_map[outlet_id] = outlet_name
 
    # Baris yang ada di raw file tapi TIDAK ada di final file
    # (tidak ke-mapping outlet-nya) tetap diisi dengan nama outlet
    # placeholder, supaya tidak melanggar foreign key constraint.
    skipped_count = 0
 
    for visit_id, raw_row in raw_rows.items():
 
        outlet_id = raw_row[3]
 
        if outlet_id not in outlet_map:
            short_id = str(outlet_id)[:8]
            outlet_map[outlet_id] = f"Outlet Belum Diketahui ({short_id})"
            skipped_count += 1
 
    if skipped_count:
        print(
            f"⚠ {skipped_count} baris tidak ketemu pasangannya di file final, "
            f"outlet-nya diisi placeholder."
        )
 
    return sales_map, kowil_map, outlet_map, raw_rows
 
 
def insert_sales(sales_map):
 
    query = text("""
        INSERT INTO sales (id, name, email)
        VALUES (:id, :name, :email)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name),
            email = VALUES(email)
    """)
 
    with engine.begin() as conn:
        for user_id, name in sales_map.items():
            email = f"{slugify_name_for_email(name)}@{EMAIL_DOMAIN}"
            conn.execute(query, {
                "id": user_id,
                "name": name,
                "email": email,
            })
 
    print(f"✓ {len(sales_map)} data sales berhasil diinsert/diupdate.")
 
 
def insert_kowil(kowil_map):
 
    query = text("""
        INSERT INTO kowil (id, name)
        VALUES (:id, :name)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name)
    """)
 
    with engine.begin() as conn:
        for kowil_id, name in kowil_map.items():
            conn.execute(query, {
                "id": kowil_id,
                "name": name,
            })
 
    print(f"✓ {len(kowil_map)} data kowil berhasil diinsert/diupdate.")
 
 
def insert_outlet(outlet_map):
 
    query = text("""
        INSERT INTO outlet (id, name, address)
        VALUES (:id, :name, :address)
        ON DUPLICATE KEY UPDATE
            name = VALUES(name)
    """)
 
    with engine.begin() as conn:
        for outlet_id, name in outlet_map.items():
            conn.execute(query, {
                "id": outlet_id,
                "name": name,
                "address": DEFAULT_OUTLET_ADDRESS,
            })
 
    print(f"✓ {len(outlet_map)} data outlet berhasil diinsert/diupdate.")
 
 
def insert_manual_visit(raw_rows):
 
    query = text("""
        INSERT INTO manual_visit
        (id, user_id, kowil_id, outlet_id, visit_image,
         visit_date, visit_catatan, created_at, updated_at, visit_status)
        VALUES
        (:id, :user_id, :kowil_id, :outlet_id, :visit_image,
         :visit_date, :visit_catatan, :created_at, :updated_at, :visit_status)
        ON DUPLICATE KEY UPDATE
            visit_catatan = VALUES(visit_catatan),
            visit_status = VALUES(visit_status),
            updated_at = VALUES(updated_at)
    """)
 
    inserted = 0
 
    with engine.begin() as conn:
        for visit_id, row in raw_rows.items():
 
            (
                _id, user_id, kowil_id, outlet_id, visit_image,
                visit_date, visit_catatan, created_at, updated_at,
                visit_status, *_rest,
            ) = row
 
            conn.execute(query, {
                "id": visit_id,
                "user_id": user_id,
                "kowil_id": kowil_id,
                "outlet_id": outlet_id,
                "visit_image": visit_image,
                "visit_date": visit_date,
                "visit_catatan": visit_catatan,
                "created_at": created_at,
                "updated_at": updated_at,
                "visit_status": visit_status,
            })
            inserted += 1
 
    print(f"✓ {inserted} data manual_visit berhasil diinsert/diupdate.")
 
 
def main():
 
    raw_file, final_file = get_filenames()
 
    print()
    print("Membaca dan mencocokkan data dari 2 file Excel...")
    sales_map, kowil_map, outlet_map, raw_rows = build_mappings(raw_file, final_file)
 
    print()
    print("Ditemukan:")
    print(f"  - {len(sales_map)} sales unik")
    print(f"  - {len(kowil_map)} kowil unik")
    print(f"  - {len(outlet_map)} outlet unik")
    print(f"  - {len(raw_rows)} baris manual_visit")
    print()
 
    confirm = input("Lanjutkan insert ke database? (y/n): ").strip().lower()
 
    if confirm != "y":
        print("Dibatalkan.")
        return
 
    insert_sales(sales_map)
    insert_kowil(kowil_map)
    insert_outlet(outlet_map)
    insert_manual_visit(raw_rows)
 
    print()
    print("Selesai! Semua data berhasil dimasukkan ke database.")
 
 
if __name__ == "__main__":
    main()
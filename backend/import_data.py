"""Import empat file CSV ke tabel MySQL dengan mencocokkan kolom CSV dan tabel.

Simpan script ini bersama users.csv, kowils.csv, outlets.csv, manual_visits.csv
serta database.py di folder backend. Jalankan: python import_data_fixed.py

Script mengimpor ke tabel bernama users, kowils, outlets, manual_visits.
Kolom dipetakan berdasarkan nama yang sama. Alias dipakai hanya bila kolom tujuan
aslinya tidak tersedia, misalnya kowil_code -> name pada tabel aplikasi lama.
Semua file ditulis dalam satu transaksi dan dibatalkan jika ada error.
"""
import csv
import sys
from pathlib import Path
from sqlalchemy import text
from database import engine

BASE_DIR = Path(__file__).resolve().parent
FILES = [
    ("users.csv", "users"),
    ("kowils.csv", "kowils"),
    ("outlets.csv", "outlets"),
    ("manual_visits.csv", "manual_visits"),
]
# Aliases hanya digunakan jika nama kolom CSV tidak tersedia di tabel tujuan.
ALIASES = {
    "kowils": {"kowil_code": "name"},
    "outlets": {
        "outlet_name": "name",
        "outlet_title": "name",
        "outlet_street_address": "address",
    },
    "manual_visits": {},
    "users": {},
}


def read_csv(path):
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                if not reader.fieldnames:
                    raise ValueError(f"{path.name}: header tidak ditemukan")
                reader.fieldnames = [h.strip().lstrip("\ufeff") if h else "" for h in reader.fieldnames]
                rows = []
                for line_no, raw in enumerate(reader, start=2):
                    row = {str(k).strip().lstrip("\ufeff"): (v.strip() if isinstance(v, str) and v.strip() else None)
                           for k, v in raw.items() if k is not None}
                    if any(v is not None for v in row.values()):
                        row["__line__"] = line_no
                        rows.append(row)
                return rows
        except UnicodeDecodeError as exc:
            last_error = exc
    raise last_error or ValueError(f"Tidak bisa membaca {path.name}")


def table_names(conn):
    return set(conn.execute(text("SHOW TABLES")).scalars().all())


def table_columns(conn, table):
    return [r[0] for r in conn.execute(text(f"SHOW COLUMNS FROM `{table}`")).all()]


def primary_keys(conn, table):
    return [r[4] for r in conn.execute(text(f"SHOW KEYS FROM `{table}` WHERE Key_name='PRIMARY'")).all()]


def transform(filename, table, source_rows, target_cols):
    aliases = ALIASES.get(table, {})
    result_by_id = {}
    no_id_count = 0
    for original in source_rows:
        row = dict(original)
        line_no = row.pop("__line__", "?")
        mapped = {}
        # Prioritaskan kolom yang namanya sama persis dengan target.
        for source_col, value in row.items():
            if source_col in target_cols:
                mapped[source_col] = value
        # Pakai alias hanya jika target tidak punya nama kolom sumber.
        for source_col, target_col in aliases.items():
            if source_col in row and target_col in target_cols and source_col not in target_cols:
                if mapped.get(target_col) in (None, ""):
                    mapped[target_col] = row[source_col]
        if "id" in target_cols:
            if mapped.get("id") in (None, ""):
                raise ValueError(f"{table}: id kosong pada baris CSV {line_no}.")
            result_by_id[str(mapped["id"])] = mapped  # baris terakhir untuk ID yang sama dipakai
        else:
            result_by_id[f"line-{line_no}"] = mapped
    transformed = list(result_by_id.values())
    duplicates = len(source_rows) - len(transformed)
    if source_rows and not transformed:
        raise ValueError(f"{filename}: tidak ada kolom yang cocok dengan tabel {table}.")
    if transformed and not any(r for r in transformed):
        raise ValueError(f"{filename}: tidak ada kolom CSV yang cocok dengan kolom tabel {table}.")
    return transformed, duplicates


def insert_upsert(conn, table, rows, target_cols, pks):
    if not rows:
        return 0
    groups = {}
    for row in rows:
        # Jangan kirim nilai kolom yang tidak ada di tabel.
        row = {k: v for k, v in row.items() if k in target_cols}
        if not row:
            raise ValueError(f"Tidak ada kolom yang cocok untuk tabel {table}.")
        groups.setdefault(tuple(sorted(row.keys())), []).append(row)
    total = 0
    for keys, group in groups.items():
        col_sql = ", ".join(f"`{k}`" for k in keys)
        val_sql = ", ".join(f":{k}" for k in keys)
        update_cols = [k for k in keys if k not in pks]
        if update_cols:
            update_sql = ", ".join(f"`{k}` = VALUES(`{k}`)" for k in update_cols)
            suffix = f" ON DUPLICATE KEY UPDATE {update_sql}"
        elif pks:
            k = pks[0]
            suffix = f" ON DUPLICATE KEY UPDATE `{k}` = VALUES(`{k}`)"
        else:
            suffix = ""
        stmt = text(f"INSERT INTO `{table}` ({col_sql}) VALUES ({val_sql}){suffix}")
        conn.execute(stmt, group)
        total += len(group)
    return total


def main():
    absent = [f for f, _ in FILES if not (BASE_DIR / f).is_file()]
    if absent:
        print("File tidak ditemukan di folder backend:")
        print("\n".join(f" - {f}" for f in absent))
        sys.exit(1)
    try:
        data = [(f, t, read_csv(BASE_DIR / f)) for f, t in FILES]
        print("FILE YANG AKAN DIIMPORT")
        for f, t, rows in data:
            print(f"  {f} -> tabel {t}: {len(rows)} baris sumber")
        with engine.connect() as conn:
            existing = table_names(conn)
            missing = [t for _, t, _ in data if t not in existing]
            if missing:
                raise ValueError(
                    "Tabel tujuan berikut tidak ada di database yang dipakai database.py: " + ", ".join(missing) +
                    ". Script ini menargetkan tabel users, kowils, outlets, manual_visits. Periksa nama tabel database terlebih dahulu."
                )
            plans = []
            for f, t, rows in data:
                cols = table_columns(conn, t)
                mapped, dupes = transform(f, t, rows, cols)
                pks = primary_keys(conn, t)
                all_mapped_cols = sorted({c for r in mapped for c in r})
                if not all_mapped_cols:
                    raise ValueError(f"{f}: tidak ada nama kolom yang cocok dengan tabel {t}. Kolom CSV: {', '.join(rows[0].keys()) if rows else '(kosong)'}; kolom tabel: {', '.join(cols)}")
                plans.append((f, t, mapped, cols, pks, dupes))
                print(f"  {f}: {len(mapped)} baris setelah merangkum ID duplikat; {dupes} duplikat diringkas")
                print(f"    Kolom yang akan diisi: {', '.join(all_mapped_cols)}")
        print("\nPerhatian: users.csv mengandung hash password. Script akan memasukkan hanya kolom yang juga ada di tabel tujuan.")
        print("Buat backup database sebelum lanjut. Belum ada data yang ditulis.")
        if input("Ketik y untuk konfirmasi import: ").strip().lower() != "y":
            print("Import dibatalkan; database tidak diubah.")
            return
        outcomes = []
        with engine.begin() as conn:
            for f, t, rows, cols, pks, dupes in plans:
                n = insert_upsert(conn, t, rows, cols, pks)
                outcomes.append((f, t, n, dupes))
        print("\nIMPORT SELESAI")
        for f, t, n, dupes in outcomes:
            print(f"  OK {f} -> {t}: {n} baris diproses; {dupes} duplikat ID diringkas")
    except Exception as exc:
        print("\nIMPORT GAGAL. Jika error terjadi saat menulis, transaksi dibatalkan.")
        print(f"Detail: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()

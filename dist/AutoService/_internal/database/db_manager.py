import os
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


APP_NAME = "AutoService"
LEGACY_DB_PATH = Path(__file__).resolve().with_name("autoservice.db")


def get_app_data_dir() -> Path:
    custom_dir = os.environ.get("AUTOSERVICE_DATA_DIR")
    if custom_dir:
        return Path(custom_dir)

    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME
    return Path.home() / f".{APP_NAME.lower()}"


def get_database_path() -> Path:
    data_dir = get_app_data_dir()
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        return data_dir / "autoservice.db"
    except OSError:
        LEGACY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        return LEGACY_DB_PATH


DB_PATH = get_database_path()


def ensure_database_file():
    if DB_PATH == LEGACY_DB_PATH:
        return
    if DB_PATH.exists() or not LEGACY_DB_PATH.exists():
        return
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(LEGACY_DB_PATH, DB_PATH)


def get_connection():
    ensure_database_file()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _clean(value) -> str:
    return str(value or "").strip()


def _normalize_name(value: str) -> str:
    value = _clean(value)
    return value if value else "Клієнт"


def _row_id(row):
    return row[0] if row else None


def _column_names(cursor, table_name: str) -> set[str]:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def _add_column_if_missing(cursor, table_name: str, column_name: str, column_def: str):
    if column_name not in _column_names(cursor, table_name):
        cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def init_db():
    ensure_database_file()
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                phone TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_phones (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                label TEXT DEFAULT '',
                phone TEXT NOT NULL,
                is_primary INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vehicles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id INTEGER NOT NULL,
                brand TEXT DEFAULT '',
                model TEXT DEFAULT '',
                vin TEXT DEFAULT '',
                number TEXT DEFAULT '',
                mileage TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                client TEXT,
                phone TEXT DEFAULT '',
                brand TEXT,
                model TEXT,
                vin TEXT,
                number TEXT,
                mileage TEXT,
                client_id INTEGER,
                vehicle_id INTEGER,
                FOREIGN KEY(client_id) REFERENCES clients(id) ON DELETE SET NULL,
                FOREIGN KEY(vehicle_id) REFERENCES vehicles(id) ON DELETE SET NULL
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_materials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                name TEXT,
                qty REAL,
                price REAL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoice_services (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                name TEXT,
                qty REAL,
                price REAL,
                FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
            )
        """)

        _add_column_if_missing(cursor, "clients", "phone", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "clients", "notes", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "clients", "created_at", "TEXT")
        _add_column_if_missing(cursor, "clients", "updated_at", "TEXT")
        _add_column_if_missing(cursor, "vehicles", "notes", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "vehicles", "created_at", "TEXT")
        _add_column_if_missing(cursor, "vehicles", "updated_at", "TEXT")
        _add_column_if_missing(cursor, "invoices", "phone", "TEXT DEFAULT ''")
        _add_column_if_missing(cursor, "invoices", "client_id", "INTEGER")
        _add_column_if_missing(cursor, "invoices", "vehicle_id", "INTEGER")

        now = _now()
        cursor.execute("UPDATE clients SET created_at = COALESCE(created_at, ?), updated_at = COALESCE(updated_at, ?)", (now, now))
        cursor.execute("UPDATE vehicles SET created_at = COALESCE(created_at, ?), updated_at = COALESCE(updated_at, ?)", (now, now))

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_name ON clients(name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_clients_phone ON clients(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_phones_client ON client_phones(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_client_phones_phone ON client_phones(phone)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_client ON vehicles(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_vin ON vehicles(vin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vehicles_number ON vehicles(number)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_client ON invoices(client_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_invoices_vehicle ON invoices(vehicle_id)")

        _backfill_clients_and_vehicles(cursor)
        _backfill_client_phones(cursor)
        conn.commit()


def _find_client(cursor, name: str, phone: str = ""):
    name = _normalize_name(name)
    phone = _clean(phone)

    if phone:
        cursor.execute(
            """
            SELECT id
            FROM clients
            WHERE phone = ?
               OR lower(name) = lower(?)
               OR EXISTS (
                   SELECT 1
                   FROM client_phones
                   WHERE client_phones.client_id = clients.id
                     AND client_phones.phone = ?
               )
            ORDER BY id
            LIMIT 1
            """,
            (phone, name, phone),
        )
    else:
        cursor.execute(
            "SELECT id FROM clients WHERE lower(name) = lower(?) ORDER BY id LIMIT 1",
            (name,),
        )
    return _row_id(cursor.fetchone())


def _get_primary_phone(cursor, client_id) -> str:
    cursor.execute(
        """
        SELECT phone
        FROM client_phones
        WHERE client_id = ?
        ORDER BY is_primary DESC, id ASC
        LIMIT 1
        """,
        (client_id,),
    )
    row = cursor.fetchone()
    return row[0] if row else ""


def _sync_primary_phone(cursor, client_id) -> str:
    now = _now()
    primary_phone = _get_primary_phone(cursor, client_id)
    if primary_phone:
        cursor.execute(
            """
            UPDATE client_phones
            SET is_primary = CASE WHEN phone = ? THEN 1 ELSE 0 END
            WHERE client_id = ?
            """,
            (primary_phone, client_id),
        )
    cursor.execute(
        "UPDATE clients SET phone = ?, updated_at = ? WHERE id = ?",
        (primary_phone, now, client_id),
    )
    return primary_phone


def _ensure_client_phone(cursor, client_id, phone: str, label: str = "", is_primary: bool = False):
    phone = _clean(phone)
    label = _clean(label)
    if not phone:
        return None

    now = _now()
    cursor.execute(
        "SELECT id FROM client_phones WHERE client_id = ? AND phone = ? ORDER BY id LIMIT 1",
        (client_id, phone),
    )
    phone_id = _row_id(cursor.fetchone())

    if is_primary:
        cursor.execute("UPDATE client_phones SET is_primary = 0 WHERE client_id = ?", (client_id,))

    if phone_id:
        cursor.execute(
            """
            UPDATE client_phones
            SET label = CASE WHEN ? != '' THEN ? ELSE label END,
                is_primary = CASE WHEN ? = 1 THEN 1 ELSE is_primary END,
                updated_at = ?
            WHERE id = ?
            """,
            (label, label, 1 if is_primary else 0, now, phone_id),
        )
    else:
        cursor.execute(
            """
            INSERT INTO client_phones (client_id, label, phone, is_primary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (client_id, label, phone, 1 if is_primary else 0, now, now),
        )
        phone_id = cursor.lastrowid

    _sync_primary_phone(cursor, client_id)
    return phone_id


def _set_client_phones(cursor, client_id, phones):
    now = _now()
    existing_ids = {
        row[0]
        for row in cursor.execute("SELECT id FROM client_phones WHERE client_id = ?", (client_id,)).fetchall()
    }

    cleaned_phones = []
    seen_numbers = set()
    for phone in phones:
        number = _clean(phone.get("phone"))
        if not number or number in seen_numbers:
            continue
        seen_numbers.add(number)
        cleaned_phones.append({
            "id": phone.get("id"),
            "label": _clean(phone.get("label")),
            "phone": number,
            "is_primary": bool(phone.get("is_primary")),
        })

    if cleaned_phones and not any(phone["is_primary"] for phone in cleaned_phones):
        cleaned_phones[0]["is_primary"] = True

    kept_ids = set()
    cursor.execute("UPDATE client_phones SET is_primary = 0 WHERE client_id = ?", (client_id,))
    for phone in cleaned_phones:
        phone_id = phone.get("id")
        if phone_id in existing_ids:
            cursor.execute(
                """
                UPDATE client_phones
                SET label = ?, phone = ?, is_primary = ?, updated_at = ?
                WHERE id = ? AND client_id = ?
                """,
                (
                    phone["label"],
                    phone["phone"],
                    1 if phone["is_primary"] else 0,
                    now,
                    phone_id,
                    client_id,
                ),
            )
            kept_ids.add(phone_id)
        else:
            cursor.execute(
                """
                INSERT INTO client_phones (client_id, label, phone, is_primary, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (client_id, phone["label"], phone["phone"], 1 if phone["is_primary"] else 0, now, now),
            )
            kept_ids.add(cursor.lastrowid)

    removed_ids = existing_ids - kept_ids
    if removed_ids:
        placeholders = ", ".join("?" for _ in removed_ids)
        cursor.execute(
            f"DELETE FROM client_phones WHERE client_id = ? AND id IN ({placeholders})",
            (client_id, *removed_ids),
        )

    return _sync_primary_phone(cursor, client_id)


def _find_vehicle(cursor, client_id, brand: str, model: str, vin: str, number: str):
    brand = _clean(brand)
    model = _clean(model)
    vin = _clean(vin).upper()
    number = _clean(number).upper()

    if vin:
        cursor.execute("SELECT id FROM vehicles WHERE lower(vin) = lower(?) ORDER BY id LIMIT 1", (vin,))
        vehicle_id = _row_id(cursor.fetchone())
        if vehicle_id:
            return vehicle_id

    if number:
        cursor.execute("SELECT id FROM vehicles WHERE lower(number) = lower(?) ORDER BY id LIMIT 1", (number,))
        vehicle_id = _row_id(cursor.fetchone())
        if vehicle_id:
            return vehicle_id

    cursor.execute(
        """
        SELECT id
        FROM vehicles
        WHERE client_id = ?
          AND lower(COALESCE(brand, '')) = lower(?)
          AND lower(COALESCE(model, '')) = lower(?)
        ORDER BY id
        LIMIT 1
        """,
        (client_id, brand, model),
    )
    return _row_id(cursor.fetchone())


def _upsert_client(cursor, client_id, name: str, phone: str = "", notes: str = ""):
    name = _normalize_name(name)
    phone = _clean(phone)
    notes = _clean(notes)
    now = _now()

    if client_id:
        cursor.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE clients
                SET name = ?, notes = COALESCE(NULLIF(?, ''), notes), updated_at = ?
                WHERE id = ?
                """,
                (name, notes, now, client_id),
            )
            if phone:
                _ensure_client_phone(cursor, client_id, phone, "Основний", True)
            return client_id

    existing_id = _find_client(cursor, name, phone)
    if existing_id:
        cursor.execute("UPDATE clients SET name = ?, updated_at = ? WHERE id = ?", (name, now, existing_id))
        if phone:
            _ensure_client_phone(cursor, existing_id, phone, "Основний", True)
        return existing_id

    cursor.execute(
        """
        INSERT INTO clients (name, phone, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (name, phone, notes, now, now),
    )
    client_id = cursor.lastrowid
    if phone:
        _ensure_client_phone(cursor, client_id, phone, "Основний", True)
    return client_id


def _upsert_vehicle(cursor, vehicle_id, client_id, brand: str, model: str, vin: str, number: str, mileage: str, notes: str = ""):
    brand = _clean(brand)
    model = _clean(model)
    vin = _clean(vin).upper()
    number = _clean(number).upper()
    mileage = _clean(mileage)
    notes = _clean(notes)
    now = _now()

    if vehicle_id:
        cursor.execute("SELECT id FROM vehicles WHERE id = ?", (vehicle_id,))
        if cursor.fetchone():
            cursor.execute(
                """
                UPDATE vehicles
                SET client_id = ?, brand = ?, model = ?, vin = ?, number = ?,
                    mileage = ?, notes = COALESCE(NULLIF(?, ''), notes), updated_at = ?
                WHERE id = ?
                """,
                (client_id, brand, model, vin, number, mileage, notes, now, vehicle_id),
            )
            return vehicle_id

    existing_id = _find_vehicle(cursor, client_id, brand, model, vin, number)
    if existing_id:
        cursor.execute(
            """
            UPDATE vehicles
            SET client_id = ?, brand = ?, model = ?, vin = ?, number = ?,
                mileage = CASE WHEN ? != '' THEN ? ELSE mileage END,
                updated_at = ?
            WHERE id = ?
            """,
            (client_id, brand, model, vin, number, mileage, mileage, now, existing_id),
        )
        return existing_id

    cursor.execute(
        """
        INSERT INTO vehicles (client_id, brand, model, vin, number, mileage, notes, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (client_id, brand, model, vin, number, mileage, notes, now, now),
    )
    return cursor.lastrowid


def _set_client_vehicles(cursor, client_id, vehicles):
    now = _now()
    existing_ids = {
        row[0]
        for row in cursor.execute("SELECT id FROM vehicles WHERE client_id = ?", (client_id,)).fetchall()
    }

    cleaned_vehicles = []
    for vehicle in vehicles:
        brand = _clean(vehicle.get("brand"))
        model = _clean(vehicle.get("model"))
        vin = _clean(vehicle.get("vin")).upper()
        number = _clean(vehicle.get("number")).upper()
        mileage = _clean(vehicle.get("mileage"))
        notes = _clean(vehicle.get("notes"))
        if not any((brand, model, vin, number, mileage, notes)):
            continue
        cleaned_vehicles.append({
            "id": vehicle.get("id"),
            "brand": brand,
            "model": model,
            "vin": vin,
            "number": number,
            "mileage": mileage,
            "notes": notes,
        })

    kept_ids = set()
    for vehicle in cleaned_vehicles:
        vehicle_id = vehicle.get("id")
        if vehicle_id in existing_ids:
            cursor.execute(
                """
                UPDATE vehicles
                SET brand = ?, model = ?, vin = ?, number = ?, mileage = ?, notes = ?, updated_at = ?
                WHERE id = ? AND client_id = ?
                """,
                (
                    vehicle["brand"],
                    vehicle["model"],
                    vehicle["vin"],
                    vehicle["number"],
                    vehicle["mileage"],
                    vehicle["notes"],
                    now,
                    vehicle_id,
                    client_id,
                ),
            )
            kept_ids.add(vehicle_id)
        else:
            cursor.execute(
                """
                INSERT INTO vehicles (client_id, brand, model, vin, number, mileage, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    client_id,
                    vehicle["brand"],
                    vehicle["model"],
                    vehicle["vin"],
                    vehicle["number"],
                    vehicle["mileage"],
                    vehicle["notes"],
                    now,
                    now,
                ),
            )
            vehicle_id = cursor.lastrowid
            kept_ids.add(vehicle_id)

        cursor.execute(
            """
            UPDATE invoices
            SET brand = ?, model = ?, vin = ?, number = ?, mileage = ?
            WHERE vehicle_id = ?
            """,
            (vehicle["brand"], vehicle["model"], vehicle["vin"], vehicle["number"], vehicle["mileage"], vehicle_id),
        )

    removed_ids = existing_ids - kept_ids
    if removed_ids:
        placeholders = ", ".join("?" for _ in removed_ids)
        cursor.execute(
            f"UPDATE invoices SET vehicle_id = NULL WHERE client_id = ? AND vehicle_id IN ({placeholders})",
            (client_id, *removed_ids),
        )
        cursor.execute(
            f"DELETE FROM vehicles WHERE client_id = ? AND id IN ({placeholders})",
            (client_id, *removed_ids),
        )


def _backfill_clients_and_vehicles(cursor):
    cursor.execute("""
        SELECT id, client, phone, brand, model, vin, number, mileage, client_id, vehicle_id
        FROM invoices
        WHERE client_id IS NULL OR vehicle_id IS NULL
        ORDER BY id
    """)
    invoices = cursor.fetchall()

    for invoice in invoices:
        (
            invoice_id,
            client,
            phone,
            brand,
            model,
            vin,
            number,
            mileage,
            client_id,
            vehicle_id,
        ) = invoice
        client_id = client_id or _upsert_client(cursor, None, client, phone)
        vehicle_id = vehicle_id or _upsert_vehicle(cursor, None, client_id, brand, model, vin, number, mileage)
        cursor.execute(
            "UPDATE invoices SET client_id = ?, vehicle_id = ? WHERE id = ?",
            (client_id, vehicle_id, invoice_id),
        )


def _backfill_client_phones(cursor):
    cursor.execute("SELECT id, phone FROM clients WHERE COALESCE(phone, '') != ''")
    for client_id, phone in cursor.fetchall():
        _ensure_client_phone(cursor, client_id, phone, "Основний", True)

    cursor.execute("""
        SELECT DISTINCT client_id, phone
        FROM invoices
        WHERE client_id IS NOT NULL AND COALESCE(phone, '') != ''
    """)
    for client_id, phone in cursor.fetchall():
        _ensure_client_phone(cursor, client_id, phone, "З акту", False)

    cursor.execute("SELECT id FROM clients")
    for (client_id,) in cursor.fetchall():
        _sync_primary_phone(cursor, client_id)


def save_invoice(vehicle, materials, works, invoice_id=None):
    with get_connection() as conn:
        cursor = conn.cursor()

        client_id = _upsert_client(
            cursor,
            vehicle.get("client_id"),
            vehicle.get("client"),
            vehicle.get("phone", ""),
        )
        vehicle_id = _upsert_vehicle(
            cursor,
            vehicle.get("vehicle_id"),
            client_id,
            vehicle.get("brand"),
            vehicle.get("model"),
            vehicle.get("vin"),
            vehicle.get("number"),
            vehicle.get("mileage"),
        )
        primary_phone = _clean(vehicle.get("phone")) or _get_primary_phone(cursor, client_id)

        payload = (
            vehicle.get("date"),
            _normalize_name(vehicle.get("client")),
            primary_phone,
            _clean(vehicle.get("brand")),
            _clean(vehicle.get("model")),
            _clean(vehicle.get("vin")).upper(),
            _clean(vehicle.get("number")).upper(),
            _clean(vehicle.get("mileage")),
            client_id,
            vehicle_id,
        )

        if invoice_id:
            cursor.execute(
                """
                UPDATE invoices
                SET date = ?, client = ?, phone = ?, brand = ?, model = ?, vin = ?,
                    number = ?, mileage = ?, client_id = ?, vehicle_id = ?
                WHERE id = ?
                """,
                (*payload, invoice_id),
            )
            if cursor.rowcount == 0:
                raise ValueError(f"Акт №{invoice_id} не знайдено")

            cursor.execute("DELETE FROM invoice_materials WHERE invoice_id = ?", (invoice_id,))
            cursor.execute("DELETE FROM invoice_services WHERE invoice_id = ?", (invoice_id,))
        else:
            cursor.execute(
                """
                INSERT INTO invoices
                    (date, client, phone, brand, model, vin, number, mileage, client_id, vehicle_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                payload,
            )
            invoice_id = cursor.lastrowid

        for item in materials:
            cursor.execute(
                """
                INSERT INTO invoice_materials (invoice_id, name, qty, price)
                VALUES (?, ?, ?, ?)
                """,
                (invoice_id, _clean(item.get("name")), item.get("qty", 0), item.get("price", 0)),
            )

        for item in works:
            cursor.execute(
                """
                INSERT INTO invoice_services (invoice_id, name, qty, price)
                VALUES (?, ?, ?, ?)
                """,
                (invoice_id, _clean(item.get("name")), item.get("qty", 0), item.get("price", 0)),
            )

        conn.commit()
        return invoice_id


def get_all_invoices(search_text: str = ""):
    query = f"%{_clean(search_text).lower()}%"
    where = ""
    params = []
    if _clean(search_text):
        where = """
            WHERE lower(COALESCE(i.client, '')) LIKE ?
               OR lower(COALESCE(i.phone, '')) LIKE ?
               OR lower(COALESCE(c.phone, '')) LIKE ?
               OR EXISTS (
                    SELECT 1
                    FROM client_phones cp
                    WHERE cp.client_id = c.id AND lower(cp.phone) LIKE ?
               )
               OR lower(COALESCE(i.brand, '')) LIKE ?
               OR lower(COALESCE(i.model, '')) LIKE ?
               OR lower(COALESCE(i.vin, '')) LIKE ?
               OR lower(COALESCE(i.number, '')) LIKE ?
               OR lower(COALESCE(i.date, '')) LIKE ?
        """
        params = [query] * 9

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                i.id,
                i.date,
                i.client,
                COALESCE(NULLIF(i.phone, ''), c.phone, '') AS phone,
                i.brand,
                i.model,
                i.number,
                i.vin,
                COALESCE(materials.total, 0) + COALESCE(services.total, 0) AS total
            FROM invoices i
            LEFT JOIN clients c ON c.id = i.client_id
            LEFT JOIN (
                SELECT invoice_id, SUM(qty * price) AS total
                FROM invoice_materials
                GROUP BY invoice_id
            ) materials ON materials.invoice_id = i.id
            LEFT JOIN (
                SELECT invoice_id, SUM(qty * price) AS total
                FROM invoice_services
                GROUP BY invoice_id
            ) services ON services.invoice_id = i.id
            {where}
            ORDER BY i.id DESC
            """,
            params,
        )
        return cursor.fetchall()


def search_customer_records(search_text: str = "", limit: int = 25):
    search_text = _clean(search_text)
    query = f"%{search_text.lower()}%"
    where = ""
    params = []
    if search_text:
        where = """
            WHERE lower(COALESCE(c.name, '')) LIKE ?
               OR lower(COALESCE(c.phone, '')) LIKE ?
               OR EXISTS (
                    SELECT 1
                    FROM client_phones cp
                    WHERE cp.client_id = c.id AND lower(cp.phone) LIKE ?
               )
               OR lower(COALESCE(v.brand, '')) LIKE ?
               OR lower(COALESCE(v.model, '')) LIKE ?
               OR lower(COALESCE(v.vin, '')) LIKE ?
               OR lower(COALESCE(v.number, '')) LIKE ?
        """
        params.extend([query] * 7)

    params.append(limit)

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                c.id AS client_id,
                c.name AS client,
                c.phone AS phone,
                v.id AS vehicle_id,
                v.brand AS brand,
                v.model AS model,
                v.vin AS vin,
                v.number AS number,
                v.mileage AS mileage,
                COALESCE(last_invoices.last_invoice_id, 0) AS last_invoice_id
            FROM clients c
            LEFT JOIN vehicles v ON v.client_id = c.id
            LEFT JOIN (
                SELECT vehicle_id, MAX(id) AS last_invoice_id
                FROM invoices
                GROUP BY vehicle_id
            ) last_invoices ON last_invoices.vehicle_id = v.id
            {where}
            ORDER BY last_invoice_id DESC, c.updated_at DESC, c.name ASC
            LIMIT ?
            """,
            params,
        )
        records = [dict(row) for row in cursor.fetchall()]

    for record in records:
        car = f"{record.get('brand') or ''} {record.get('model') or ''}".strip()
        identifiers = [value for value in (record.get("number"), record.get("vin")) if value]
        parts = [record.get("client") or "Клієнт"]
        if record.get("phone"):
            parts.append(record["phone"])
        if car:
            parts.append(car)
        if identifiers:
            parts.append(" / ".join(identifiers))
        record["label"] = " | ".join(parts)
    return records


def get_clients(search_text: str = ""):
    search_text = _clean(search_text)
    query = f"%{search_text.lower()}%"
    where = ""
    params = []
    if search_text:
        where = """
            WHERE lower(COALESCE(c.name, '')) LIKE ?
               OR lower(COALESCE(c.phone, '')) LIKE ?
               OR EXISTS (
                    SELECT 1
                    FROM client_phones cp
                    WHERE cp.client_id = c.id AND lower(cp.phone) LIKE ?
               )
               OR EXISTS (
                    SELECT 1
                    FROM vehicles v
                    WHERE v.client_id = c.id
                      AND (
                        lower(COALESCE(v.brand, '')) LIKE ?
                        OR lower(COALESCE(v.model, '')) LIKE ?
                        OR lower(COALESCE(v.vin, '')) LIKE ?
                        OR lower(COALESCE(v.number, '')) LIKE ?
                      )
               )
        """
        params = [query] * 7

    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            f"""
            SELECT
                c.id,
                c.name,
                c.phone AS primary_phone,
                COALESCE(phone_summary.phones, '') AS phones,
                COALESCE(vehicle_summary.vehicles, '') AS vehicles,
                COALESCE(vehicle_summary.vehicle_count, 0) AS vehicle_count,
                COALESCE(invoice_summary.invoice_count, 0) AS invoice_count,
                c.updated_at
            FROM clients c
            LEFT JOIN (
                SELECT client_id, GROUP_CONCAT(phone, ', ') AS phones
                FROM client_phones
                GROUP BY client_id
            ) phone_summary ON phone_summary.client_id = c.id
            LEFT JOIN (
                SELECT
                    client_id,
                    COUNT(*) AS vehicle_count,
                    GROUP_CONCAT(TRIM(brand || ' ' || model || ' ' || number), '; ') AS vehicles
                FROM vehicles
                GROUP BY client_id
            ) vehicle_summary ON vehicle_summary.client_id = c.id
            LEFT JOIN (
                SELECT client_id, COUNT(*) AS invoice_count
                FROM invoices
                GROUP BY client_id
            ) invoice_summary ON invoice_summary.client_id = c.id
            {where}
            ORDER BY c.updated_at DESC, c.name ASC
            """,
            params,
        )
        return [dict(row) for row in cursor.fetchall()]


def get_client_card(client_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM clients WHERE id = ?", (client_id,))
        client_row = cursor.fetchone()
        if client_row is None:
            raise ValueError(f"Клієнта №{client_id} не знайдено")

        cursor.execute(
            """
            SELECT id, label, phone, is_primary
            FROM client_phones
            WHERE client_id = ?
            ORDER BY is_primary DESC, id ASC
            """,
            (client_id,),
        )
        phones = [dict(row) for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT id, brand, model, vin, number, mileage, notes
            FROM vehicles
            WHERE client_id = ?
            ORDER BY id ASC
            """,
            (client_id,),
        )
        vehicles = [dict(row) for row in cursor.fetchall()]

        return {"client": dict(client_row), "phones": phones, "vehicles": vehicles}


def save_client_card(client, phones, vehicles):
    with get_connection() as conn:
        cursor = conn.cursor()
        now = _now()

        client_id = client.get("id")
        name = _normalize_name(client.get("name"))
        notes = _clean(client.get("notes"))

        if client_id:
            cursor.execute("SELECT id FROM clients WHERE id = ?", (client_id,))
            if cursor.fetchone() is None:
                raise ValueError(f"Клієнта №{client_id} не знайдено")
            cursor.execute(
                "UPDATE clients SET name = ?, notes = ?, updated_at = ? WHERE id = ?",
                (name, notes, now, client_id),
            )
        else:
            cursor.execute(
                "INSERT INTO clients (name, notes, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, notes, now, now),
            )
            client_id = cursor.lastrowid

        primary_phone = _set_client_phones(cursor, client_id, phones)
        _set_client_vehicles(cursor, client_id, vehicles)

        cursor.execute(
            "UPDATE invoices SET client = ?, phone = ? WHERE client_id = ?",
            (name, primary_phone, client_id),
        )
        conn.commit()
        return client_id


def delete_client(client_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE invoices SET client_id = NULL, vehicle_id = NULL WHERE client_id = ?", (client_id,))
        cursor.execute("DELETE FROM clients WHERE id = ?", (client_id,))
        conn.commit()


def get_invoice_by_id(invoice_id):
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT
                i.*,
                COALESCE(NULLIF(i.phone, ''), c.phone, '') AS resolved_phone
            FROM invoices i
            LEFT JOIN clients c ON c.id = i.client_id
            WHERE i.id = ?
            """,
            (invoice_id,),
        )
        row = cursor.fetchone()
        if row is None:
            raise ValueError(f"Акт №{invoice_id} не знайдено")

        vehicle = dict(row)
        vehicle["phone"] = vehicle.pop("resolved_phone", "") or vehicle.get("phone", "")

        cursor.execute("SELECT name, qty, price FROM invoice_materials WHERE invoice_id = ?", (invoice_id,))
        materials = [dict(item) for item in cursor.fetchall()]
        for item in materials:
            item["sum"] = item["qty"] * item["price"]

        cursor.execute("SELECT name, qty, price FROM invoice_services WHERE invoice_id = ?", (invoice_id,))
        works = [dict(item) for item in cursor.fetchall()]
        for item in works:
            item["sum"] = item["qty"] * item["price"]

        return vehicle, materials, works


def delete_invoice(invoice_id):
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
        conn.commit()


init_db()

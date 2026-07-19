import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "autoservice.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    """Створює таблиці, якщо їх немає"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Таблиця накладних / автомобілів
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                client TEXT,
                brand TEXT,
                model TEXT,
                vin TEXT,
                number TEXT,
                mileage TEXT
            )
        """)
        
        # Таблиця матеріалів (пов'язана з накладною)
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
        
        # Таблиця послуг (пов'язана з накладною)
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
        conn.commit()

# Ініціалізуємо бази даних при імпорті
init_db()

# --- ФУНКЦІЇ ДЛЯ РОБОТИ З ДАНИМИ (CRUD) ---

def save_invoice(vehicle, materials, works, invoice_id=None):
    """Зберігає нову або оновлює існуючу накладну"""
    with get_connection() as conn:
        cursor = conn.cursor()
        
        if invoice_id:
            # Редагування існуючої
            cursor.execute("""
                UPDATE invoices 
                SET date=?, client=?, brand=?, model=?, vin=?, number=?, mileage=?
                WHERE id=?
            """, (vehicle['date'], vehicle['client'], vehicle['brand'], vehicle['model'], 
                  vehicle['vin'], vehicle['number'], vehicle['mileage'], invoice_id))
            
            # Видаляємо старі матеріали та послуги, щоб записати оновлені
            cursor.execute("DELETE FROM invoice_materials WHERE invoice_id=?", (invoice_id,))
            cursor.execute("DELETE FROM invoice_services WHERE invoice_id=?", (invoice_id,))
        else:
            # Створення нової накладної
            cursor.execute("""
                INSERT INTO invoices (date, client, brand, model, vin, number, mileage)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (vehicle['date'], vehicle['client'], vehicle['brand'], vehicle['model'], 
                  vehicle['vin'], vehicle['number'], vehicle['mileage']))
            invoice_id = cursor.lastrowid
            
        # Записуємо матеріали
        for m in materials:
            cursor.execute("""
                INSERT INTO invoice_materials (invoice_id, name, qty, price)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, m['name'], m['qty'], m['price']))
            
        # Записуємо послуги
        for w in works:
            cursor.execute("""
                INSERT INTO invoice_services (invoice_id, name, qty, price)
                VALUES (?, ?, ?, ?)
            """, (invoice_id, w['name'], w['qty'], w['price']))
            
        conn.commit()
        return invoice_id

def get_all_invoices():
    """Повертає список усіх накладних для журналу"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, date, client, brand, model, number FROM invoices ORDER BY id DESC")
        return cursor.fetchall()

def get_invoice_by_id(invoice_id):
    """Завантажує повні дані однієї накладної для редагування"""
    with get_connection() as conn:
        conn.row_factory = sqlite3.Row  # Щоб звертатися за назвами колонок
        cursor = conn.cursor()
        
        # Дані авто
        cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
        vehicle = dict(cursor.fetchone())
        
        # Матеріали
        cursor.execute("SELECT name, qty, price FROM invoice_materials WHERE invoice_id = ?", (invoice_id,))
        materials = [dict(row) for row in cursor.fetchall()]
        for m in materials:
            m['sum'] = m['qty'] * m['price']
            
        # Послуги
        cursor.execute("SELECT name, qty, price FROM invoice_services WHERE invoice_id = ?", (invoice_id,))
        works = [dict(row) for row in cursor.fetchall()]
        for w in works:
            w['sum'] = w['qty'] * w['price']
            
        return vehicle, materials, works

def delete_invoice(invoice_id):
    """Видаляє накладну та пов'язані записи"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM invoice_materials WHERE invoice_id=?", (invoice_id,))
        cursor.execute("DELETE FROM invoice_services WHERE invoice_id=?", (invoice_id,))
        cursor.execute("DELETE FROM invoices WHERE id=?", (invoice_id,))
        conn.commit()
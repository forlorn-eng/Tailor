import json
import sqlite3
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "tailor.db"


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            address TEXT,
            registration_date TEXT,
            notes TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL UNIQUE,
            neck REAL,
            chest REAL,
            shoulder REAL,
            sleeve_length REAL,
            shirt_length REAL,
            waist REAL,
            hip REAL,
            trouser_length REAL,
            additional_notes TEXT,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            dress_type TEXT NOT NULL,
            delivery_date TEXT,
            price REAL DEFAULT 0,
            advance_payment REAL DEFAULT 0,
            remaining_payment REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Pending',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            note TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE
        );
        """
    )
    conn.commit()
    conn.close()


def json_bytes(payload):
    return json.dumps(payload).encode("utf-8")


class TailorHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.serve_file(BASE_DIR / "templates" / "index.html", "text/html")
        if path.startswith("/static/"):
            file_path = BASE_DIR / path.strip("/")
            content_type = "text/plain"
            if file_path.suffix == ".css":
                content_type = "text/css"
            elif file_path.suffix == ".js":
                content_type = "application/javascript"
            return self.serve_file(file_path, content_type)

        if path == "/api/customers":
            return self.list_customers()

        parts = path.strip("/").split("/")
        if len(parts) == 3 and parts[0] == "api" and parts[1] == "customers":
            return self.customer_detail(int(parts[2]))

        self.send_error(404, "Not Found")

    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/api/customers":
            return self.create_customer()

        parts = path.strip("/").split("/")
        if len(parts) == 4 and parts[:3] == ["api", "customers", parts[2]] and parts[3] == "orders":
            return self.add_order(int(parts[2]))
        if len(parts) == 4 and parts[:2] == ["api", "orders"] and parts[3] == "payments":
            return self.add_payment(int(parts[2]))

        self.send_error(404, "Not Found")

    def do_PUT(self):
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        if len(parts) == 3 and parts[:2] == ["api", "customers"]:
            return self.update_customer(int(parts[2]))
        if len(parts) == 4 and parts[:2] == ["api", "customers"] and parts[3] == "measurements":
            return self.update_measurements(int(parts[2]))
        if len(parts) == 3 and parts[:2] == ["api", "orders"]:
            return self.update_order(int(parts[2]))

        self.send_error(404, "Not Found")

    def read_json(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        return json.loads(body.decode("utf-8"))

    def respond_json(self, data, status=200):
        payload = json_bytes(data)
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def serve_file(self, path: Path, content_type: str):
        if not path.exists() or not path.is_file():
            return self.send_error(404, "File not found")
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def list_customers(self):
        query = parse_qs(urlparse(self.path).query)
        search = (query.get("search", [""])[0] or "").strip()
        conn = get_db_connection()
        if search:
            rows = conn.execute(
                "SELECT id, name, phone, address, registration_date, notes FROM customers WHERE name LIKE ? OR phone LIKE ? ORDER BY id DESC",
                (f"%{search}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT id, name, phone, address, registration_date, notes FROM customers ORDER BY id DESC"
            ).fetchall()
        conn.close()
        self.respond_json([dict(row) for row in rows])

    def create_customer(self):
        data = self.read_json()
        required = ["name", "phone", "registration_date"]
        missing = [f for f in required if not data.get(f)]
        if missing:
            return self.respond_json({"error": f"Missing required fields: {', '.join(missing)}"}, 400)

        conn = get_db_connection()
        cur = conn.execute(
            "INSERT INTO customers (name, phone, address, registration_date, notes) VALUES (?, ?, ?, ?, ?)",
            (
                data.get("name"),
                data.get("phone"),
                data.get("address", ""),
                data.get("registration_date"),
                data.get("notes", ""),
            ),
        )
        customer_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO measurements (
              customer_id, neck, chest, shoulder, sleeve_length, shirt_length,
              waist, hip, trouser_length, additional_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                customer_id,
                data.get("neck"),
                data.get("chest"),
                data.get("shoulder"),
                data.get("sleeve_length"),
                data.get("shirt_length"),
                data.get("waist"),
                data.get("hip"),
                data.get("trouser_length"),
                data.get("measurement_notes", ""),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        self.respond_json({"message": "Customer created successfully", "customer_id": customer_id}, 201)

    def customer_detail(self, customer_id: int):
        conn = get_db_connection()
        customer = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not customer:
            conn.close()
            return self.respond_json({"error": "Customer not found"}, 404)

        measurement = conn.execute("SELECT * FROM measurements WHERE customer_id = ?", (customer_id,)).fetchone()
        orders = conn.execute("SELECT * FROM orders WHERE customer_id = ? ORDER BY id DESC", (customer_id,)).fetchall()
        payments = conn.execute(
            "SELECT p.*, o.dress_type FROM payments p JOIN orders o ON o.id = p.order_id WHERE p.customer_id = ? ORDER BY p.payment_date DESC, p.id DESC",
            (customer_id,),
        ).fetchall()
        conn.close()

        self.respond_json(
            {
                "customer": dict(customer),
                "measurements": dict(measurement) if measurement else None,
                "orders": [dict(row) for row in orders],
                "payments": [dict(row) for row in payments],
            }
        )

    def update_customer(self, customer_id: int):
        data = self.read_json()
        conn = get_db_connection()
        exists = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not exists:
            conn.close()
            return self.respond_json({"error": "Customer not found"}, 404)

        conn.execute(
            "UPDATE customers SET name = ?, phone = ?, address = ?, registration_date = ?, notes = ? WHERE id = ?",
            (
                data.get("name"),
                data.get("phone"),
                data.get("address", ""),
                data.get("registration_date"),
                data.get("notes", ""),
                customer_id,
            ),
        )
        conn.commit()
        conn.close()
        self.respond_json({"message": "Customer updated"})

    def update_measurements(self, customer_id: int):
        data = self.read_json()
        conn = get_db_connection()
        exists = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not exists:
            conn.close()
            return self.respond_json({"error": "Customer not found"}, 404)

        conn.execute(
            """
            INSERT INTO measurements (
              customer_id, neck, chest, shoulder, sleeve_length, shirt_length,
              waist, hip, trouser_length, additional_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(customer_id) DO UPDATE SET
              neck=excluded.neck,
              chest=excluded.chest,
              shoulder=excluded.shoulder,
              sleeve_length=excluded.sleeve_length,
              shirt_length=excluded.shirt_length,
              waist=excluded.waist,
              hip=excluded.hip,
              trouser_length=excluded.trouser_length,
              additional_notes=excluded.additional_notes,
              updated_at=excluded.updated_at
            """,
            (
                customer_id,
                data.get("neck"),
                data.get("chest"),
                data.get("shoulder"),
                data.get("sleeve_length"),
                data.get("shirt_length"),
                data.get("waist"),
                data.get("hip"),
                data.get("trouser_length"),
                data.get("additional_notes", ""),
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        conn.close()
        self.respond_json({"message": "Measurements updated"})

    def add_order(self, customer_id: int):
        data = self.read_json()
        if not data.get("dress_type"):
            return self.respond_json({"error": "Dress type is required"}, 400)

        price = float(data.get("price") or 0)
        advance = float(data.get("advance_payment") or 0)
        remaining = max(price - advance, 0)

        conn = get_db_connection()
        exists = conn.execute("SELECT id FROM customers WHERE id = ?", (customer_id,)).fetchone()
        if not exists:
            conn.close()
            return self.respond_json({"error": "Customer not found"}, 404)

        cur = conn.execute(
            "INSERT INTO orders (customer_id, dress_type, delivery_date, price, advance_payment, remaining_payment, status) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                customer_id,
                data.get("dress_type"),
                data.get("delivery_date"),
                price,
                advance,
                remaining,
                data.get("status", "Pending"),
            ),
        )
        order_id = cur.lastrowid
        if advance > 0:
            conn.execute(
                "INSERT INTO payments (customer_id, order_id, amount, payment_date, note) VALUES (?, ?, ?, ?, ?)",
                (customer_id, order_id, advance, date.today().isoformat(), "Advance payment"),
            )

        conn.commit()
        conn.close()
        self.respond_json({"message": "Order added", "order_id": order_id}, 201)

    def update_order(self, order_id: int):
        data = self.read_json()
        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return self.respond_json({"error": "Order not found"}, 404)

        price = float(data.get("price", order["price"]))
        advance = float(data.get("advance_payment", order["advance_payment"]))
        remaining = float(data.get("remaining_payment", max(price - advance, 0)))

        conn.execute(
            "UPDATE orders SET dress_type = ?, delivery_date = ?, price = ?, advance_payment = ?, remaining_payment = ?, status = ? WHERE id = ?",
            (
                data.get("dress_type", order["dress_type"]),
                data.get("delivery_date", order["delivery_date"]),
                price,
                advance,
                remaining,
                data.get("status", order["status"]),
                order_id,
            ),
        )
        conn.commit()
        conn.close()
        self.respond_json({"message": "Order updated"})

    def add_payment(self, order_id: int):
        data = self.read_json()
        amount = float(data.get("amount") or 0)
        if amount <= 0:
            return self.respond_json({"error": "Amount must be greater than zero"}, 400)

        conn = get_db_connection()
        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            conn.close()
            return self.respond_json({"error": "Order not found"}, 404)

        conn.execute(
            "INSERT INTO payments (customer_id, order_id, amount, payment_date, note) VALUES (?, ?, ?, ?, ?)",
            (
                order["customer_id"],
                order_id,
                amount,
                data.get("payment_date", date.today().isoformat()),
                data.get("note", "Payment"),
            ),
        )

        new_remaining = max(float(order["remaining_payment"]) - amount, 0)
        new_status = data.get("status") or ("Delivered" if new_remaining == 0 else order["status"])
        conn.execute("UPDATE orders SET remaining_payment = ?, status = ? WHERE id = ?", (new_remaining, new_status, order_id))
        conn.commit()
        conn.close()
        self.respond_json({"message": "Payment recorded", "remaining_payment": new_remaining})


if __name__ == "__main__":
    init_db()
    server = HTTPServer(("0.0.0.0", 5000), TailorHandler)
    print("Server running on http://localhost:5000")
    server.serve_forever()

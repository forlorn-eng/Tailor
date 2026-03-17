# Tailor Shop Manager (Mobile-Friendly)

A simple web application for tailor shops to manage customer records, measurements, orders, and payment history with permanent SQLite storage.

## Features

- **Customer Registration**
  - Name, phone, address, date, notes
- **Measurements**
  - Neck, chest, shoulder, sleeve length, shirt length, waist, hip, trouser length, additional notes
- **Order Management**
  - Dress type, delivery date, price, advance payment, remaining payment, status
  - Status options: Pending / Ready / Delivered
  - Mark orders delivered
- **Customer Search**
  - Search by name or phone number
- **Customer History**
  - View all past orders, measurements, and payment history per customer
- **Edit & Update**
  - Edit customer information
  - Update measurements
  - Update order status
  - Add order payments
- **Permanent Database**
  - Uses SQLite (`tailor.db`) for persistent storage
- **Mobile UI**
  - Simple, clean layout
  - Large inputs/buttons
  - Responsive for phone browsers

## Technology Stack

- Frontend: HTML, CSS, JavaScript
- Backend: Python (built-in HTTP server)
- Database: SQLite

## Project Structure

- `app.py` - Python HTTP server + API + SQLite initialization
- `templates/index.html` - Main UI
- `static/styles.css` - Mobile-friendly styling
- `static/app.js` - Frontend logic and API calls
- `requirements.txt` - Python dependencies

## Run Locally

### 1) Prerequisites

- Python 3.9+

### 2) Start the app

```bash
python3 app.py
```

The app will run at:

- `http://localhost:5000`

On first run, SQLite database file `tailor.db` is created automatically.

## Deploy Online

You can deploy this Python app on free/low-cost platforms such as **Render**, **Railway**, or **PythonAnywhere**.

### Option A: Render (recommended, with Python runtime)

1. Push this project to a GitHub repository.
2. In Render dashboard, create a new **Web Service** from your repo.
3. Set:
   - **Build Command:** `echo "No build step needed"`
   - **Start Command:** `python app.py`
4. Add environment variable if needed:
   - `PYTHON_VERSION=3.11`
5. Deploy.

> Note: SQLite works, but for production with multiple instances, a managed DB is better. For a single small tailor shop deployment, SQLite can still be acceptable.

### Option B: PythonAnywhere

1. Upload project files.
2. Create a web app configured to run a custom Python script or use an always-on task.
3. Run `python app.py` and map your domain/port through platform settings.

## API Endpoints (Quick Reference)

- `GET /api/customers?search=...`
- `POST /api/customers`
- `GET /api/customers/<id>`
- `PUT /api/customers/<id>`
- `PUT /api/customers/<id>/measurements`
- `POST /api/customers/<id>/orders`
- `PUT /api/orders/<order_id>`
- `POST /api/orders/<order_id>/payments`

## Notes

- Data is stored permanently in `tailor.db`.
- Keep regular backups of `tailor.db`.
- To reset all data, stop server and delete `tailor.db`.

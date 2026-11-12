# Alkhair Order and Reservation System

A full-stack Django web application for Restoran Alkhair (Parit Raja, Batu Pahat, Johor), supporting online food ordering (delivery, takeaway, QR dine-in) and table reservations.

Built for university coursework:
- **BIK11003 Database**: Relational schema design, normalization, join tables, transaction-safe queries, ORM aggregation.
- **BIK20404 Web Development**: Dynamic web app, CRUD operations, role-based access control (RBAC), responsive Bootstrap 5 UI, session management, secure checkout and simulated payment.

---

## 1. Prerequisites

- Python 3.10+ (tested on Python 3.14)
- MySQL 8.0+ (running locally or in Docker)
- `pip` and virtual environment support (`venv`)

> **Note on Database Driver**: This project uses `PyMySQL` with `pymysql.install_as_MySQLdb()` configured in `main/__init__.py` instead of `mysqlclient`. This eliminates the need for C++ build tools and MySQL development headers, allowing smooth installation across Windows, Linux, and macOS.

---

## 2. Local Setup and Installation

### Step 1: Clone the repository and navigate into it
```bash
git clone <repository_url>
cd prototype
```

### Step 2: Create and activate virtual environment
```bash
python3 -m venv venv

# On Linux / macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Environment configuration (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Open `.env` and configure your credentials:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SITE_BASE_URL=http://127.0.0.1:8000

# Database Settings
DB_ENGINE=mysql
DB_NAME=project_alkhair
DB_USER=root
DB_PASSWORD=1234
DB_HOST=127.0.0.1
DB_PORT=3307
```

### Step 5: Database setup (MySQL via Docker or Native)
If using the provided Docker container on port 3307:
```bash
docker start bik11003-mysql
```
Ensure the database `project_alkhair` exists.

### Step 6: Apply migrations
```bash
python main/manage.py migrate
```

### Step 7: Seed demo data
Populate initial categories, menu items, restaurant tables with QR tokens, admin account, and customer accounts:
```bash
python main/manage.py seed_demo
```

### Step 8: Generate table QR codes
Generate QR code PNG images for all active restaurant tables:
```bash
python main/manage.py generate_table_qr
```
QR images are saved in `main/media/qr/`.

### Step 9: Run the development server
```bash
python main/manage.py runserver
```
Visit `http://127.0.0.1:8000/` in your browser.

---

## 3. Demo Credentials

After running `seed_demo`, use these credentials to test:

| Role | Email | Password |
|---|---|---|
| **Admin** | `admin@alkhair.com` | `Admin1234!` |
| **Customer 1** | `customer1@gmail.com` | `Customer1234!` |
| **Customer 2** | `customer2@gmail.com` | `Customer1234!` |

---

## 4. Running Tests

Run the full automated test suite:
```bash
python main/manage.py test
```

---

## 5. Mobile Phone Demo (QR Dine-in)

To test scanning QR codes with a physical mobile phone on the same Wi-Fi network:
1. Find your machine's local IP address (e.g. `192.168.1.50`).
2. Update `.env`:
   ```env
   ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.50
   SITE_BASE_URL=http://192.168.1.50:8000
   ```
3. Regenerate QR codes:
   ```bash
   python main/manage.py generate_table_qr
   ```
4. Start the server binding to `0.0.0.0`:
   ```bash
   python main/manage.py runserver 0.0.0.0:8000
   ```
5. Scan any generated QR code from `main/media/qr/` using your phone camera.

---

## 6. PythonAnywhere Deployment (SQLite Fallback)

On platforms such as PythonAnywhere free tier where external MySQL might not be accessible:
1. Set `DB_ENGINE=sqlite` in `.env` or the web app environment.
2. In `settings.py`, SQLite automatically engages using `db.sqlite3`.
3. Run `python manage.py migrate` and `python manage.py collectstatic`.

---

## 7. Configuration Notice for Group Members

The following items are placeholders and should be verified and finalized by the group:
- **Operating Hours**: Configured to `11:00` to `23:30` in `settings.py` (`OPENING_TIME` and `CLOSING_TIME`).
- **Contact Details & Address**: Restoran Alkhair, Parit Raja, Batu Pahat, Johor.
- **Menu Photos**: Replace placeholders in `static/img/` with genuine photographs taken at the restaurant.
- **Menu Prices**: Seeded from preliminary menu photo; verify with restaurant staff.

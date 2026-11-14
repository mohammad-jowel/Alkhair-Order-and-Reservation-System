# Alkhair Order and Reservation System

A full-stack Django web application for Restoran Alkhair (Parit Raja, Batu Pahat, Johor), supporting online food ordering (delivery, takeaway, QR dine-in) and table reservations.

Built for university coursework:
- **BIK11003 Database**: Relational schema design, normalization (3NF), join tables, transaction-safe queries, ORM aggregation.
- **BIK20404 Web Development**: Dynamic web application (13 pages, full CRUD, role-based access control, responsive Bootstrap 5 UI, session management, secure checkout, and simulated payment).

---

## 1. Prerequisites

- Python 3.10+ (tested on Python 3.14)
- MySQL 8.0+ (running locally or in Docker)
- `pip` and virtual environment support (`venv`)

> **Note on Database Driver**: This project uses `PyMySQL` with `pymysql.install_as_MySQLdb()` configured in `main/main/__init__.py` instead of `mysqlclient`. This eliminates the need for OS-level C++ build tools and MySQL development headers, ensuring trouble-free installation across Windows, Linux, and macOS. `cryptography` is included to support MySQL 8's `caching_sha2_password`.

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

### Step 4: Configure environment variables (`.env`)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Ensure `.env` contains your local database credentials:
```env
SECRET_KEY=django-insecure-dev-key-alkhair-system
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SITE_BASE_URL=http://127.0.0.1:8000

# Database Settings
DB_ENGINE=mysql
DB_NAME=project_alkhair
DB_USER=[db_user]
DB_PASSWORD=[db_password]
DB_HOST=127.0.0.1
DB_PORT=[db_port]
```

### Step 5: Start MySQL
If using the provided Docker container on port 3307:
```bash
docker start bik11003-mysql
```

### Step 6: Apply database migrations
```bash
python main/manage.py migrate
```

### Step 7: Seed demo data
Seed the restaurant setup: categories, 26 menu items, 10 restaurant tables with QR tokens, and the demo admin account:
```bash
python main/manage.py seed_restaurant_demo
```

Seed five numbered demo customers and their orders and reservations. Dates are anchored to the current local date whenever the command runs:
```bash
python main/manage.py seed_customer_demo
```
*(Safe to rerun to refresh dates. Use `python main/manage.py seed_customer_demo --clear` to rebuild the customer activity, or `--delete` to remove the demo activity and customer accounts.)*

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
Visit `http://127.0.0.1:8000/` in your web browser.

---

## 3. Demonstration Accounts & Logins

Run `seed_restaurant_demo` for restaurant data and the admin account. Run `seed_customer_demo` for the five demo customer accounts and their activity:

| Role | Email | Password | Purpose |
|---|---|---|---|
| **Admin** | `admin@alkhair.com` | `Admin1234!`* | Dashboard, menu CRUD, manage orders, confirm reservations, table QR management |
| **Demo Customer 1** | `customer1@demo.com` | `Customer1234!` | Ordering, QR dine-in, reservations, profile editing |
| **Demo Customer 2** | `customer2@demo.com` | `Customer1234!` | Pre-seeded with delivery orders & bookings |
| **Demo Customer 3–5** | `customer3@demo.com` – `customer5@demo.com` | `Customer1234!` | Additional customers with order & reservation history |

\* If an existing superuser is present, `seed_restaurant_demo` reuses it and preserves its password; use that account's email. Otherwise it creates `admin@alkhair.com` with initial password `Admin1234!`. Change the initial password after setup.

---

## 4. Running Automated Tests

Run the complete 51-test automated test suite across all 6 applications:
```bash
python main/manage.py test core accounts menu orders reservations dashboard
```

All 51 tests execute against an isolated test database and verify:
- Registration, password hashing, and generic login error handling
- Role-based access control (`admin_required` blocking customers with 403)
- Ownership security (customers receiving 404 on other customers' orders and bookings)
- Atomic server-side order total computation and unit price freezing
- QR token validation, session persistence, and dine-in table assignment
- Date, operating hours, and party size constraints on reservations
- Deleting ordered menu items being blocked by database protection

---

## 5. Mobile Phone Demo (QR Dine-in over Local Wi-Fi)

To test scanning QR codes with a physical smartphone on the same local network:
1. Find your computer's local IP address (e.g. `192.168.1.50` via `ip a` on Linux or `ipconfig` on Windows).
2. Edit `.env`:
   ```env
   ALLOWED_HOSTS=127.0.0.1,localhost,192.168.1.50
   SITE_BASE_URL=http://192.168.1.50:8000
   ```
3. Regenerate the QR images with the new URL:
   ```bash
   python main/manage.py generate_table_qr
   ```
4. Start the Django server binding to `0.0.0.0`:
   ```bash
   python main/manage.py runserver 0.0.0.0:8000
   ```
5. Scan any generated QR code image in `main/media/qr/` using your phone camera.

---

## 6. PythonAnywhere Deployment Guide (with SQLite Fallback)

On platforms such as PythonAnywhere free tier where external MySQL ports cannot be connected:

### Step 1: Upload and extract code
Open a Bash console on PythonAnywhere and clone your repository into `/home/<username>/prototype`.

### Step 2: Create virtual environment & install requirements
```bash
cd /home/<username>/prototype
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure `.env` with SQLite fallback
Create `/home/<username>/prototype/.env`:
```env
SECRET_KEY=generate-a-strong-secret-key-for-production
DEBUG=False
ALLOWED_HOSTS=<username>.pythonanywhere.com
SITE_BASE_URL=https://<username>.pythonanywhere.com
DB_ENGINE=sqlite
```
*(When `DB_ENGINE=sqlite` is set, `settings.py` automatically uses `db.sqlite3`.)*

### Step 4: Run migrations, seed demo, and collect static files
```bash
python main/manage.py migrate
python main/manage.py seed_restaurant_demo
python main/manage.py seed_customer_demo
python main/manage.py generate_table_qr
python main/manage.py collectstatic --noinput
```

### Step 5: Configure PythonAnywhere Web Tab
1. In the **Web** tab, select **Add a new web app** -> **Manual configuration** -> **Python 3.10**.
2. Set **Source code**: `/home/<username>/prototype/main`
3. Set **Working directory**: `/home/<username>/prototype/main`
4. Set **Virtualenv**: `/home/<username>/prototype/venv`
5. Under **Static files**, configure two mappings:
   - URL: `/static/` -> Directory: `/home/<username>/prototype/main/staticfiles`
   - URL: `/media/` -> Directory: `/home/<username>/prototype/main/media`
6. Edit the **WSGI configuration file**:
   ```python
   import os
   import sys

   path = '/home/<username>/prototype/main'
   if path not in sys.path:
       sys.path.insert(0, path)

   os.environ['DJANGO_SETTINGS_MODULE'] = 'main.settings'

   from django.core.wsgi import get_wsgi_application
   application = get_wsgi_application()
   ```
7. Click the green **Reload <username>.pythonanywhere.com** button.

---

## 7. Placeholder Items to Finalize (For Group Members)

The following items are placeholders and should be confirmed with the restaurant:
- **Operating Hours**: Configured to `11:00` to `23:30` in `settings.py` (`OPENING_TIME` and `CLOSING_TIME`).
- **Contact Details & Address**: Restoran Alkhair, Parit Raja, Batu Pahat, Johor.
- **Menu Photos**: Replace SVG placeholders in `static/img/` with genuine photographs taken at the restaurant.
- **Menu Prices**: Seeded from preliminary menu photo; verify with restaurant staff.
- **Two Unreadable Menu Items**: Marked with `TODO` in `docs/DECISIONS.md`.

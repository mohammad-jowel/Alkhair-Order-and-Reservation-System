# Agent Instructions: Alkhair Order and Reservation System

You are building a Django web application for a university group project. It is submitted to two courses at the same time:

- BIK11003 Database: marked on database design (ERD, normalization, join table) and a working front end and back end.
- BIK20404 Web Development: marked on a working dynamic website (7 to 14 pages, CRUD, security, responsive design, database with 3 or more related tables, localhost deployment).

The group members must be able to explain every part of this code to a lecturer. Write simple, readable code with short comments. Do not use clever abstractions.

An empty Django project already exists in this repository and has been pushed to GitHub. Build everything else.

## 0. Ground rules

1. Read this whole file before writing code.
2. Inspect the repository first: Django version, project name, existing files. Use what is there. Do not recreate the project.
3. Follow the schema in section 3 exactly. The ERD in the report is drawn from it. If you believe a schema change is truly necessary, make the smallest change and record it in `docs/DECISIONS.md` with the reason, and flag it in your final message.
4. Do not add features that are not in this file. Out of scope: inventory, kitchen display, staff management, discounts, table occupancy, delivery-driver tracking, real payment processing.
5. Do not ask questions unless you are completely blocked. For any ambiguity, choose the simplest option and note it in `docs/DECISIONS.md`.
6. Work in the phases of section 9, in order. Phases 1 to 7 are the core. Do not start phase 8 (QR dine-in) until the core works end to end.
7. After each phase: run `python manage.py check`, run migrations, run the tests, run the server and exercise what you built, then commit with a clear message and push. Pull before you start. Never force push and never rewrite history.
8. Never commit secrets, `.env`, the local database file or uploaded media.

## 1. Stack and limits

- Backend: Django (Python), function-based views, Django forms, Django templates.
- Frontend: HTML, CSS, JavaScript and Bootstrap 5 (using the CDN). Bootstrap is allowed for responsive layouts, navigation, forms, buttons, cards, tables and other UI components. Custom CSS can be added in static/css/style.css to customize the design. No React, no Vue, no Django REST Framework. Chart.js is allowed for the dashboard only.
- Database: MySQL for development and the demo. Read the database settings from environment variables so SQLite can be used as a fallback on hosting that has no MySQL.
- Use `PyMySQL` with `pymysql.install_as_MySQLdb()` in the project `__init__.py` instead of `mysqlclient`, because it installs easily on Windows. Mention this in the README.
- Add `cryptography` to `requirements.txt`. MySQL 8 needs it for PyMySQL logins (`caching_sha2_password`).

### Local MySQL connection (already set up)

MySQL runs in a Docker container on this machine. The database already exists and is empty. Do not create it again and do not create other users. Use these values:

| Setting | Value |
|---|---|
| Database name | `project_alkhair` |
| Host | `127.0.0.1` (use this, not `localhost`) |
| Port | `3307` (the host port forwarded to the container's 3306) |
| User | `root` |
| Password | `1234` |

Rules for these credentials:
- Create a local `.env` file with these values, using variables such as `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST` and `DB_PORT`.
- `.env` must be listed in `.gitignore` and must never be committed.
- `.env.example` is committed and contains placeholders only. It must not contain the real password.
- The defaults in `settings.py` must not contain the password. Read it from the environment.
- Use `charset: utf8mb4` in the database `OPTIONS`.
- Django's test runner will create and drop `test_project_alkhair` itself. Root already has permission for this.
- If the connection fails, print a clear error that names the host, port and database, and check that the container is running. Do not change the credentials or fall back silently to SQLite on the local machine. The SQLite fallback is for the PythonAnywhere deployment only, and only when `DB_ENGINE=sqlite` is set in the environment.
- Other allowed packages: `Pillow` (images), `qrcode[pil]` (QR codes), `python-dotenv` (environment file).
- Pin all versions in `requirements.txt`.
- Time zone `Asia/Kuala_Lumpur`. Currency is Malaysian ringgit, shown as `RM 12.00`.

## 2. Project structure

Create these apps (one per module):

| App | Purpose | Models |
|---|---|---|
| `core` | Base template, Home, About and Contact, shared helpers | none |
| `accounts` | Register, login, logout, profile, role checks | Account |
| `menu` | Public menu, admin menu management | MenuCategory, MenuItem |
| `orders` | Cart, checkout, payment simulation, order history, admin order management, restaurant tables and QR | RestaurantTable, Order, OrderItem |
| `reservations` | Customer bookings, admin management | Reservation |
| `dashboard` | Admin dashboard views and queries | none |

Shared files: `templates/base.html`, `static/css/style.css`, `static/js/main.js`.

Settings: split into environment-driven values (`SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, database, `SITE_BASE_URL`). Provide `.env.example`. Add `.gitignore` entries for `.env`, `db.sqlite3`, `media/`, `venv/`, `__pycache__/`, `staticfiles/`.

## 3. Database schema (must match exactly)

Use these exact table names (`Meta.db_table`) and primary key names (declare explicitly, for example `account_id = models.AutoField(primary_key=True)`). Use `DecimalField` for money, never float. Add indexes on foreign keys and on `orders.order_date`.

| Table | Fields |
|---|---|
| `account` | account_id (PK), full_name, email (unique, used to log in), phone, address, password (Django password hash), role, created_at |
| `menu_category` | category_id (PK), category_name |
| `menu_item` | item_id (PK), category_id (FK, PROTECT), item_name, description, price, image (optional), is_available |
| `restaurant_table` | table_id (PK), table_number (unique), qr_token (unique), is_active |
| `orders` | order_id (PK), account_id (FK, PROTECT), table_id (nullable FK), order_type, delivery_address (nullable), order_status, payment_method, payment_status, total_amount, order_date |
| `order_item` | order_id (FK, CASCADE), item_id (FK, PROTECT), quantity, unit_price; one row per dish per order |
| `reservation` | reservation_id (PK), account_id (FK), reservation_date, reservation_time, party_size, status, note |

Choice values:

- `account.role`: `customer`, `admin`
- `orders.order_type`: `delivery`, `takeaway`, `dine_in`
- `orders.order_status`: `pending`, `preparing`, `ready`, `completed`, `cancelled`
- `orders.payment_method`: `cash`, `sim_banking`, `sim_card`, `sim_ewallet`
- `orders.payment_status`: `pending`, `paid`, `failed`, `not_required`
- `reservation.status`: `pending`, `confirmed`, `rejected`, `cancelled`

Notes:

- `order_item` is the join table between `orders` and `menu_item`. Implement the "one row per dish per order" rule with a `UniqueConstraint` on `(order, item)`. Do not use `CompositePrimaryKey` (it breaks the Django admin). The ERD still shows a composite key, so explain this in `docs/DECISIONS.md`.
- `Account` is a custom user model based on `AbstractBaseUser` and `PermissionsMixin` (or `AbstractUser` with `username` removed). Set `USERNAME_FIELD = "email"`. Set `AUTH_USER_MODEL` before the first migration. If default user migrations were already applied to a local database, reset that local database.
- `createsuperuser` must create an account with `role = "admin"`.
- Do not store a cart in the database. The cart lives in the session.

## 4. Business rules to enforce in code

Accounts and roles
- Public pages: Home, Menu, About and Contact, Login, Register.
- Customer pages need a logged-in account. Admin pages need `role == "admin"`.
- A customer can only see and change their own orders, reservations and profile. Accessing someone else's record returns 404.

Menu
- Only items with `is_available = True` can be added to the cart.
- A menu item that has been ordered cannot be deleted (PROTECT). Show a friendly message telling the admin to set it unavailable instead.
- Sizes such as small and large shawarma are separate menu items, not a separate table.

Orders
- `total_amount` is always calculated on the server from current database prices inside `transaction.atomic()`. Never trust prices or totals sent by the browser.
- Copy each item's current price into `order_item.unit_price` at checkout.
- `delivery`: `delivery_address` is required. `takeaway`: no address, no table. `dine_in`: a valid active table is required, taken from the session (see QR flow), and no address.
- A new order starts with `order_status = pending`.
- Admin moves `order_status` through `pending, preparing, ready, completed`, or sets `cancelled`. A customer may cancel only their own order while it is still `pending`.
- A cancelled order that was never paid gets `payment_status = not_required`.

Payment (simulation only)
- Cash: `payment_status` stays `pending`. The admin marks it `paid` in Manage Orders when cash is received.
- Simulated methods (`sim_banking`, `sim_card`, `sim_ewallet`): after checkout the customer sees a payment step with a clear banner: "This is a demonstration. No real payment is made." There are two buttons, "Simulate successful payment" and "Simulate failed payment". They set `payment_status` to `paid` or `failed`. A failed payment lets the customer retry or switch to cash.
- Never show or accept card numbers, CVV, banking passwords or OTPs. No real payment provider is contacted.
- Keep `order_status` and `payment_status` separate.

Reservations
- Fields: date, time, party size (1 to 20), optional note.
- Date cannot be in the past. Time must be inside the confirmed opening hours (`OPENING_TIME = '11:00'` and `CLOSING_TIME = '23:00'`).
- A new reservation is `pending`. Admin sets `confirmed` or `rejected`. A customer can cancel their own future reservation that is `pending` or `confirmed`.

Dashboard figures
- Sales total = sum of `total_amount` for orders with `payment_status = paid` and `order_status != cancelled`. Cash orders count once the admin marks them paid. State this rule on the dashboard page in one line.

## 5. Pages (13)

| Group | Page | Notes |
|---|---|---|
| Public | Home | Restaurant intro, opening hours, one multimedia element (short looping video or CSS animation, muted, with a text fallback) |
| Public | Menu | Items grouped by category, images, price, add-to-cart. Works with or without a table context |
| Public | About and Contact | Confirmed Bandar Universiti, Parit Raja address, opening hours, and phone/WhatsApp contact details |
| Public | Login | Email and password |
| Public | Register | Full name, email, phone, address, password with confirmation |
| Customer | Cart and Checkout | Cart review, quantity update and remove, order type, address if delivery, payment method, payment simulation step |
| Customer | My Orders | List and detail with status and payment status, cancel if pending |
| Customer | Reservations | Booking form and list of own reservations |
| Customer | My Profile | View and edit name, phone, address, change password |
| Admin | Dashboard | See section 7 |
| Admin | Manage Menu | CRUD for categories and items, image upload, availability toggle |
| Admin | Manage Orders | List with filters by status and type, update statuses |
| Admin | Manage Reservations | List with filters, confirm or reject |

The payment simulation is a step inside Cart and Checkout, not an extra page. Keep the total at 13 pages.

Navigation: one consistent navigation system from `base.html`. It shows links appropriate to visitors, customers and admins, includes the table number badge when a table context is active, and collapses to a toggle menu on small screens. For logged-in administrators, use a focused admin sidebar ordered as Dashboard, Manage Menu, Manage Orders, Manage Reservations, and Table QR Codes; hide the public Home, Menu & Order, and About & Contact links in this admin navigation.

## 6. Frontend requirements

- Structure and styling: Use one shared base.html and one static/css/style.css. Load Bootstrap 5 through its CDN in base.html. Use Bootstrap for responsive layouts and common UI components such as navigation bars, forms, buttons, cards and tables. Use custom CSS in style.css to customize colours, typography, spacing and other UI elements. Apply a warm restaurant palette (charcoal neutrals and food-ordering orange, currently `#f97316`), readable typography, and consistent order-status badges. Do not rely entirely on Bootstrap's default appearance. Maintain a consistent design across every page.

- Visual style: Keep the website clean, simple and minimal. Avoid decorative gradients, excessive animations or heavy visual effects.

- Accessibility: Use high-contrast text, a body font size of at least 16px, visible focus outlines, labels for every form field and descriptive alt text for every image.

- Responsive design: Use Bootstrap's responsive grid and utilities together with custom CSS media queries. Design mobile first and test the website at approximately 360px, 768px and 1280px wide. Tables must scroll horizontally inside their own containers on small screens. Buttons and interactive elements must be large enough to tap comfortably.

- Images and multimedia: Include at least five relevant images on the website. Use placeholder images in static/img/ with clear file names and instruct the group to replace them with their own restaurant and menu photos. Do not download or embed copyrighted images. Include the required accessible multimedia element.

- JavaScript: Keep JavaScript small and simple. Use it for the mobile navigation toggle, client-side form checks (server-side validation remains mandatory), cart quantity buttons, a shared confirmation modal, and the dashboard chart. Use Bootstrap's JavaScript bundle through its CDN when required. Destructive or consequential actions should use a shared themed in-app confirmation modal triggered by `data-confirm`, rather than native browser confirmation dialogs. Essential website actions must still work without JavaScript.

- User feedback: Use Django messages to display success and error feedback to users.

## 7. Dashboard (admin)

Calculate everything from the database using the ORM (`aggregate`, `annotate`, `select_related`). Show:

- Summary cards: today's sales, total orders, pending orders, total customers
- Sales trend for the selected period (Chart.js bar or line chart; default to the last 7 days)
- Best-selling menu items (top 5 by quantity, using `order_item` joined to `menu_item`)
- Orders by type (delivery, takeaway, dine-in)
- Recent orders (last 10)
- Pending reservations count

Include at least two queries that join three tables, and add a short comment above each query saying what it does. This supports the "database integration" marks. By default, align headline sales and order cards to today's activity. Add date range filtering (Today, This Week, This Month presets and custom start/end dates) that updates dashboard metrics, the chart, order-type breakdown, best sellers, and recent orders together. Provide a CSV report download for the selected period, encoded with a UTF-8 BOM for spreadsheet compatibility and containing a period summary and itemized order, customer, payment, and fulfillment details.

## 8. Security requirements

- Passwords hashed by Django. Password validators enabled.
- CSRF protection on every form. Never disable it.
- ORM only. No raw SQL built from user input.
- Validate and sanitize all input on the server with Django forms. Do not use `|safe` on user content. Limit field lengths.
- Role checks on every admin view (a decorator such as `admin_required`) and ownership checks on every customer record.
- Image uploads: images only, a maximum size, and a safe file name.
- Validate the `next` redirect parameter after login (no open redirects).
- Sessions: secure cookie flags and `DEBUG = False` behaviour controlled by environment for production.
- Never expose stack traces in production. Provide simple custom 404 and 403 pages.
- Generic login error message that does not reveal whether the email exists.

## 9. Build phases

Work through these in order. Commit after each.

**Phase 1: Setup**
Settings from environment, local `.env` with the MySQL values above, `.env.example` with placeholders, `requirements.txt`, `.gitignore`, MySQL connection (SQLite fallback only for hosting when `DB_ENGINE=sqlite`), `README.md` with localhost setup steps. Run `python manage.py migrate` against `project_alkhair` to confirm the connection works before building models.

**Phase 2: Models**
All apps, all seven models exactly as in section 3, migrations, and Django admin registration (for superuser use). Provide separate demo seed commands: `seed_restaurant_demo` loads menu categories/items, 10 restaurant tables with random `qr_token` values, and a dedicated application admin account; `seed_customer_demo` loads five numbered demo customers with sample orders and reservations whose dates refresh relative to the current local date. Print demo logins when the restaurant seed command finishes. Do not alter unrelated superuser accounts. Export the schema to `docs/schema.sql`.

**Phase 3: Base and core pages**
`base.html`, CSS, Home, About and Contact, custom error pages. Placeholder images.

**Phase 4: Accounts**
Register, login, logout, profile edit, change password, `admin_required` decorator.

**Phase 5: Menu**
Public menu page and the Manage Menu CRUD. Include category filtering in the admin item list (`?category=<id>`) and clickable category item counts that open the corresponding filtered list.

**Phase 6: Cart, checkout and orders (delivery and takeaway)**
Session cart, checkout, server-side totals, My Orders, Manage Orders, cash payment flow. Order type `dine_in` is not enabled yet.

**Phase 7: Reservations**
Customer booking and list, cancel, Manage Reservations.

**Core checkpoint:** register, browse menu, order, view order, admin updates order, book a table, admin confirms. Fix everything here before continuing.

**Phase 8: QR dine-in**
- Route `/t/<qr_token>/`. It validates the token against an active `restaurant_table`, stores `table_id` and table number in the session, and redirects to the Menu. Unknown or inactive tokens show a friendly error.
- With a table in the session, checkout offers `dine_in` and saves `table_id`. The customer must be logged in before checkout. After login they return to the cart.
- Management command `generate_table_qr` writes one PNG per table to `media/qr/` containing `SITE_BASE_URL/t/<qr_token>/`. Document in the README how to use the laptop's local network address for the demo (run on `0.0.0.0:8000`, add the address to `ALLOWED_HOSTS`, set `SITE_BASE_URL`) so a phone can scan the code.
- Show a table badge in the navigation bar, with a link to clear it.
- Add an admin Table QR Codes page at `/orders/tables/` to list tables, create a table with a unique token, toggle active status, regenerate tokens, download QR PNGs, test the table link, and print branded table tent cards. QR previews may be generated in memory for the page; retain the management command for writing PNG files to `media/qr/`.

**Phase 9: Payment simulation**
As described in section 4. Clear "demonstration only" banner.

**Phase 10: Dashboard**
As described in section 7, including default today-first metrics, quick and custom date filters, and CSV report download.

**Phase 11: Hardening and tests**
Write tests with Django's test framework covering at least: registration and login, admin pages blocked for customers, a customer cannot open another customer's order or reservation, order total calculated on the server, unit price copied at checkout, delivery needs an address, dine-in needs a valid table, invalid QR token, reservation date and time validation, deleting an ordered menu item is blocked, payment status changes. All tests must pass. Review section 8 line by line.

**Phase 12: Polish and deployment preparation**
Responsive and accessibility pass at three widths. Check navigation and link consistency across all 13 core pages and the additional admin table management page. Apply the custom warm restaurant visual theme consistently. Prepare for PythonAnywhere: `STATIC_ROOT`, `collectstatic`, media handling, production environment variables, `ALLOWED_HOSTS`, `DEBUG = False`. Write the PythonAnywhere steps in the README, including the SQLite fallback if MySQL is not available on the account.

## 10. Seed data

Seed the menu from the printed menu photographed at Restoran Alkhair. These prices are readable from the photo and are a starting point. The group will verify and correct them against the real menu. Add every item as `is_available = True` with a short description and no image.

BBQ and Kebab
- Plate beef kebab RM20
- Plate chicken kebab RM18
- Plate mixed kebab RM18
- 1/4 chicken barbecue RM9
- Mix barbecue RM22
- 1/4 chicken barbecue with rice RM14
- Kebab mix with rice RM18
- Shawarma beef with rice RM15
- Shawarma chicken with rice RM12
- Lamb shank RM35
- Moffa fish and bread RM25
- Moffa fish and rice RM25

Shawarma and Sandwiches
- Zinger plate with bread RM14
- Falafel plate with bread RM8
- 3 pcs sambosa RM5
- French fries RM5
- Beef sandwich kabab RM9
- Chicken sandwich kabab RM7
- Plate shish tawook RM18
- Beef shawarma (small) RM9
- Beef shawarma (large) RM15
- Chicken shawarma (small) RM7
- Chicken shawarma (large) RM13
- Falafel sandwich RM5
- Sandwich zinger RM8
- Sandwich shish tawook RM7

The photo also shows two plates at RM15 and RM12 whose names are not readable. Leave them out and add a `TODO` line in `docs/DECISIONS.md`. Extra cheese is RM1 on shawarma. Do not model it. Mention it as a possible future option only.

## 11. Prototype additions and UI behavior

The following refinements are part of the current prototype and should be preserved when maintaining or extending it:

- **Table QR administration**: `/orders/tables/` is an administrator page for listing tables, assigning unique table numbers, creating tables, toggling availability, regenerating QR tokens, testing a table URL, downloading QR PNGs, and printing branded tent cards. QR previews can be generated in memory; `generate_table_qr` remains available for writing PNG files into `media/qr/`.
- **Menu filtering**: The Manage Menu page accepts `?category=<id>` to filter items. Category count badges link to the matching filtered view, and filter controls include a compact reset action.
- **Confirmation modal**: A shared Bootstrap modal in `base.html`, controlled by `main.js`, handles actions marked with `data-confirm`. Use it for destructive or consequential actions such as deleting menu/table records, clearing a cart, cancelling orders or reservations, and rejecting reservations. Keep clear action-specific text and buttons.
- **Dashboard date controls**: Provide Today, This Week, and This Month presets plus custom start/end dates. The selected range filters the dashboard's headline figures, sales chart, order-type counts, best sellers, recent orders, and CSV report. The default headline metrics represent today; filtered metrics represent the selected period.
- **CSV report**: The report includes selected-period summary figures and itemized order details, including customer, item, price, payment, and fulfillment data. Include a UTF-8 BOM so common spreadsheet programs open the file cleanly.
- **Seed commands and accounts**: `seed_restaurant_demo` creates menu data, 10 tables, and the dedicated `admin@gmail.com` application administrator (not a Django staff user or superuser). `seed_customer_demo` creates five numbered customers, sample order and reservation activity, and refreshes activity dates relative to the current local date. Do not modify unrelated superuser accounts.
- **Admin navigation and visual style**: Show administrators a focused sidebar with Dashboard, Manage Menu, Manage Orders, Manage Reservations, and Table QR Codes; omit public navigation links in that workspace. Maintain the warm restaurant palette (charcoal and orange, currently `#f97316`), custom status badges, and consistent compact filter controls.

## 12. Documents to produce

Keep these short and in plain language, because the group will use them to learn the code and to write the reports.

- `README.md`: requirements, install, `.env` setup, MySQL setup, migrate, `seed_restaurant_demo`, `seed_customer_demo`, run, demo logins, generate QR codes, run tests, PythonAnywhere steps.
- `docs/CODE_GUIDE.md`: for each app, what each file does and how the main flows work (register and login, ordering, QR dine-in, payment simulation, reservation, dashboard). Include how the join table `order_item` is used.
- `docs/DECISIONS.md`: every assumption or deviation, with the reason.
- `docs/TEST_CHECKLIST.md`: manual test steps for each page and flow, with expected results and a list of screenshots to take for the user manual.
- `docs/SYSTEM_OVERVIEW.md`: a concise general explanation of the system, intended users, and main capabilities.
- `docs/schema.sql`: generated schema.

## 13. Final message

When you finish a phase, say what you built, what you tested and what is left. When everything is finished, list: how to run it locally, the demo logins, the assumptions in `docs/DECISIONS.md`, and anything the group must fill in (opening hours, contact details, real photos, real menu prices, number of tables, restaurant address).

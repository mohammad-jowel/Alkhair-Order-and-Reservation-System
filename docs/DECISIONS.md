# Architectural and Implementation Decisions

This document records technical decisions, assumptions, and design rationale for the Alkhair Order and Reservation System.

---

## 1. Relational Database Schema & Primary Keys

- **Explicit Primary Keys**: Every table explicitly defines its primary key (`account_id`, `category_id`, `item_id`, `table_id`, `order_id`, `reservation_id`) using `models.AutoField(primary_key=True)` matching the project specification and ERD.
- **Order Item Join Table**:
  - The ERD presents `order_item` as a join table between `orders` and `menu_item` with a composite primary key `(order_id, item_id)`.
  - In Django ORM, native composite primary keys complicate admin integration, inline forms, and standard ModelForm conventions.
  - Therefore, `order_item` is implemented with an explicit surrogate auto-increment primary key `order_item_id = models.AutoField(primary_key=True)`, combined with a `UniqueConstraint(fields=['order', 'item'], name='unique_order_item')` and foreign key indexes. This strictly guarantees the "one row per dish per order" business constraint at the database engine level without breaking Django admin or ORM tooling.
- **Monetary Values**: All prices and totals use `DecimalField(max_digits=10, decimal_places=2)`. Floats are strictly prohibited to prevent IEEE-754 rounding inaccuracies in currency calculations.

---

## 2. Database Driver: PyMySQL

- Django defaults to `mysqlclient`, which requires OS-level C++ compilers and MySQL client developer libraries (`libmysqlclient-dev` / Visual Studio C++ Build Tools).
- To ensure students and lecturers on Windows, macOS, and Linux can run `pip install -r requirements.txt` without compiler errors, `PyMySQL` is used in conjunction with `pymysql.install_as_MySQLdb()` in `main/__init__.py`.
- `cryptography` is included in `requirements.txt` to support MySQL 8's default authentication method (`caching_sha2_password`).

---

## 3. Environment Variables & Fallback

- The application uses `python-dotenv` to load `.env`.
- To support both local MySQL (running in Docker or native host on port 3307/3306) and deployment targets without MySQL (such as PythonAnywhere free tier), `DB_ENGINE` can be toggled between `mysql` and `sqlite`.

---

## 4. Partially Obscured Menu Captions and Add-ons

- The supplied shawarma poster identifies the RM15 and RM12 plates as beef shawarma and chicken shawarma; both are included in `seed_restaurant_demo`.
- Captions in the bottom row of shawarma and fresh-juice posters are covered by video controls. Their unclear products are excluded from the active menu pending restaurant confirmation; the two readable bottom-row drinks (Milo ice and Sirap bandung) are included.
- The poster-reading `Lemon ment` is retained. Legacy menu rows were removed from the deployment database and are intentionally not managed by the restaurant seed command.
- Demo cleanup uses durable ownership records rather than image paths, table numbers, or email alone. Existing deployments must opt in to adopt confirmed legacy demo tables and the canonical demo admin before cleanup; this avoids deleting unrelated records that happen to look similar.
- "Extra cheese" (+ RM1) is shown in shawarma descriptions as an add-on note, not a separately orderable item, because the current schema has no menu modifiers.
- Menu descriptions are blank unless the poster contains an add-on note; the public cards do not invent descriptive copy. Menu item images are AI-enhanced restorations and illustrations created from cropped original menu artwork. The Yemeni Specialties prompts use a conservative restoration approach to reduce blur while retaining the source dish's serving style. The page discloses that distinction and `docs/MENU_PHOTO_SOURCES.md` records the provenance. Replace them with verified restaurant photography when available.

---

## 5. Operating Hours and Contact Information

- Confirmed restaurant hours are 11:00 AM – 11:00 PM (`OPENING_TIME = '11:00'`, `CLOSING_TIME = '23:00'`). Public pages render this shared configuration so displayed hours and reservation validation stay aligned.
- Confirmed address: 8, Jalan Universiti 3, Bandar Universiti, Parit Raja, Johor Bahru 85400. Confirmed phone and WhatsApp: +60 11-6830 9514.

---

## 6. Session-based Shopping Cart

- The shopping cart lives exclusively in the HTTP session (`request.session['cart']`).
- Uncompleted carts are not stored in the MySQL database. This prevents database bloat from abandoned customer carts, avoids redundant database writes on every quantity increment, and complies strictly with the project requirement.

---

## 7. Simulated Payment Processing

- No third-party payment gateway SDK or API is installed.
- Simulated payment methods (`sim_banking`, `sim_card`, `sim_ewallet`) route through an educational simulation screen that provides "Simulate Successful Payment" and "Simulate Failed Payment" actions.
- Credit card numbers, CVVs, expiry dates, and banking passwords are never requested or stored.

---

## 8. QR Dine-in Routing

- The QR routing pattern is exposed at the root level `/t/<qr_token>/` as well as `/orders/t/<qr_token>/`.
- This ensures short, clean URLs that encode easily into compact QR code matrices, improving camera readability across mobile devices.

---

## 9. Interactive Table QR Management Section

- The original specification provided only a backend CLI command (`generate_table_qr.py`) to generate static PNG files.
- To provide a complete, standalone administrative system, a dedicated web interface (`orders:manage_tables`) was added.
- The interface renders real-time in-memory Base64 QR code previews, allows administrators to assign custom table numbers, toggle active/inactive dining tables, test dine-in sessions directly, download PNG files, and print physical tent cards using `@media print`.

---

## 10. Universal In-App Confirmation Modal

- Native browser `window.confirm()` dialogs (`127.0.0.1:8000 says...`) were replaced with a centralized Bootstrap confirmation modal (`#universalConfirmModal` in `base.html`).
- An unobtrusive event interceptor in `main.js` listens for `data-confirm` across all forms, buttons, and links.
- Contextual modal dialogs dynamically adapt colors, icons, titles, and confirmation labels for destructive actions (deletions, cancellations, cart clears, reservation rejections).

---

## 11. Category Filtering in Admin Menu Management

- Added a category filter dropdown in `manage_menu.html` (`?category=<id>`) to allow admins to quickly focus on specific dish categories (e.g. Grills, Shawarmas).
- Linked category item count badges in the summary table to instant filtered views.

---

## 12. Specialized Admin Navigation

- Logged-in administrators have public customer links (*Home*, *Menu & Order*, *About & Contact*) hidden from their sidebar navigation.
- The admin workspace starts immediately at **Dashboard**, followed by management sections: **Manage Menu**, **Manage Orders**, **Manage Reservations**, and **Table QR Codes**.

---

## 13. Today-First Dashboard Metrics

- By default, the admin dashboard displays strictly **Today's** figures: "Today's Sales" (paid orders today) and "Today's Orders" (orders placed today), keeping all cards coherent and eliminating confusion between daily, weekly, and monthly numbers.
- When an administrator uses the Date Range filter, the cards dynamically switch to "Period Sales" and "Period Orders" for the selected date span.

---

## 14. Dashboard Date Range Filtering and CSV Report Download

- Added a date range filter (`start_date` and `end_date`) at the top of the admin dashboard.
- Filtering dynamically updates the summary cards, Chart.js sales trend line, best-selling dishes, order distribution by channel, and recent orders table.
- Added a dedicated "Download Report (CSV)" button (`/dashboard/report/download/`) that outputs a detailed CSV file containing executive revenue summaries and itemized order records with customer details, item quantities, and payment statuses.
- Formatted with UTF-8 BOM encoding for direct, artifact-free viewing in Microsoft Excel.




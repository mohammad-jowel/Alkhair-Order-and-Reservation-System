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

## 4. Unreadable Menu Items (TODO)

- The Alkhair menu photograph displayed two plate dishes priced at RM15 and RM12 where the item names were obscured.
- **TODO**: Group members must verify the exact dish names with Restoran Alkhair staff and update `seed_demo` or add them via the Admin Manage Menu interface.
- "Extra cheese" (RM1 on shawarma) is noted as an add-on in the menu, but was excluded from the initial schema to keep the relational model minimal and strictly adhere to project guidelines.

---

## 5. Operating Hours and Contact Information

- Placeholder restaurant hours are set to 11:00 AM – 11:30 PM (`OPENING_TIME = '11:00'`, `CLOSING_TIME = '23:30'`).
- Group members will confirm exact business hours and update the environment or `settings.py`.

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

## 13. Monthly Sales Metric on Dashboard

- The admin dashboard's primary revenue card displays "Today's Sales" paired with "This month's sales" (`order_date__year` and `order_date__month`) instead of an "All-time" total.
- This provides managers with meaningful, actionable monthly revenue tracking rather than lifetime figures that may be skewed or less useful for period-based reviews.



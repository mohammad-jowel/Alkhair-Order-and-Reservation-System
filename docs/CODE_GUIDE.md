# Alkhair Order and Reservation System — Code Guide

This guide explains the project structure, what each file does, and how the core flows function. Group members can use this guide to understand the code, prepare for lecturer presentations, and write their course reports.

---

## 1. Project Architecture Overview

The project is built on Django using function-based views (FBVs), Django templates, standard Django forms, and Bootstrap 5 CDN for styling. No complex third-party abstractions (like Django REST Framework) are used.

```
prototype/
├── .env.example              # Template for environment variables
├── requirements.txt          # Pinned Python package dependencies
├── README.md                 # Setup, credentials, and deployment guide
├── docs/
│   ├── CODE_GUIDE.md         # This document
│   ├── DECISIONS.md          # Architectural decisions & assumptions
│   ├── TEST_CHECKLIST.md     # Manual testing and screenshot checklist
│   └── schema.sql            # MySQL schema DDL export
└── main/
    ├── manage.py             # Django management script
    ├── main/                 # Project configuration root
    │   ├── settings.py       # Configuration (environment-driven)
    │   ├── urls.py           # Top-level URL routing
    │   ├── wsgi.py           # WSGI entry point for web servers
    │   └── asgi.py           # ASGI entry point
    ├── static/               # CSS, JS, and restaurant images
    ├── templates/            # HTML templates (base.html and error pages)
    ├── core/                 # Home, About & Contact, demo seed commands
    ├── accounts/             # User auth, registration, profiles, RBAC
    ├── menu/                 # Menu categories, items, and admin CRUD
    ├── orders/               # Cart, checkout, QR dine-in, order management
    ├── reservations/         # Table booking and admin confirmations
    └── dashboard/            # Admin metrics and Chart.js analytics
```

---

## 2. Breakdown of Apps & Files

### App 1: `core`
- **Purpose**: Public marketing pages and project-wide management commands.
- `views.py`:
  - `home(request)`: Renders the home landing page with restaurant intro, operating hours, and the accessible flame animation multimedia element.
  - `about(request)`: Renders the About & Contact page with restaurant address in Parit Raja, phone numbers, and hours.
  - `custom_404(request, exception)` / `custom_403(request, exception)`: Custom error views returning HTTP 404/403.
- `management/commands/seed_restaurant_demo.py`: Populates the current 78-item menu catalog from the restaurant photos and assigns locally stored AI-enhanced restorations and illustrations based on cropped original menu artwork. Image provenance and the accuracy disclaimer are listed in `docs/MENU_PHOTO_SOURCES.md`. It also creates 10 restaurant tables with QR tokens and the admin account. `--delete` removes unused tracked seed data but preserves history-linked rows by making menu items unavailable, tables inactive, and demo admin accounts inactive as needed. `--adopt-existing` is an explicit one-time migration step for confirmed legacy demo tables 1–10 and the canonical demo admin after a normal seed run.
- `management/commands/seed_customer_demo.py`: Creates 5 numbered demo customers (`customer1@demo.com` – `customer5@demo.com`) and seeds 15 realistic orders across the week plus 8 reservations. Order and reservation dates refresh relative to the current local date when rerun. Supports `--clear` to rebuild activity for the five demo customers and `--delete` to remove those accounts plus all their orders and reservations.

### App 2: `accounts`
- **Purpose**: User registration, authentication, profile editing, and role-based access control.
- `models.py`:
  - `Account`: Custom user model inheriting from `AbstractBaseUser` and `PermissionsMixin`. Uses `email` as the unique username identifier (`USERNAME_FIELD = 'email'`). Primary key is `account_id`.
  - Roles: `customer` and `admin`.
- `decorators.py`:
  - `@admin_required`: Restricts view to authenticated users with `role == 'admin'`. Unauthorized users get 403 Forbidden.
- `forms.py`:
  - `RegisterForm`: Validates email uniqueness, passwords match, and runs Django password validators.
  - `LoginForm`: Authenticates email and password.
  - `ProfileEditForm`: Allows users to update full name, phone number, and delivery address.
  - `ChangePasswordForm`: Validates current password and updates to new password with session security hash refresh.
- `views.py`:
  - `register_view`: Creates new customer accounts and automatically logs them in.
  - `login_view`: Validates credentials, guards against open redirects (`url_has_allowed_host_and_scheme`), and routes admins to `/dashboard/` and customers to `/`.
  - `logout_view`: Clears session and logs user out.
  - `profile_view`: Handles personal profile updates and password changes.

### App 3: `menu`
- **Purpose**: Public digital menu and administrator menu catalog CRUD.
- `models.py`:
  - `MenuCategory`: Category title (e.g. "Yemeni Rice Dishes", "Family Meals", "Shawarma and Sandwiches"). Primary key: `category_id`.
  - `MenuItem`: Individual dish with `category` foreign key (`on_delete=models.PROTECT`), `item_name`, `description`, `price` (Decimal), `image`, and `is_available` boolean.
- `forms.py`:
  - `CategoryForm`: Adds/edits categories.
  - `MenuItemForm`: Adds/edits items with price validation (> 0) and image size limit (5MB).
- `views.py`:
  - `menu_list`: Categorized public menu with category filter pills and Add to Cart forms.
  - `manage_menu`: Admin catalog table displaying all categories and items, with an integrated category dropdown filter (`?category=<id>`) and clickable category count badges.
  - `add_category` / `edit_category` / `delete_category`: Category CRUD.
  - `add_item` / `edit_item` / `delete_item`: Menu item CRUD. Deleting an item with existing orders is caught by `ProtectedError` and blocked with a friendly explanation.
  - `toggle_availability`: One-click button to make items active or inactive.

### App 4: `orders`
- **Purpose**: Shopping cart, checkout, order fulfillment, QR table dine-in, and simulated payment.
- `models.py`:
  - `RestaurantTable`: Dining table number (`table_number`), unique `qr_token`, and `is_active` status.
  - `Order`: Customer order (`account_id`, `table_id`, `order_type`, `delivery_address`, `order_status`, `payment_method`, `payment_status`, `total_amount`, `order_date`).
  - `OrderItem`: Join table between `orders` and `menu_item`.
- `cart.py`:
  - Pure session-based cart (`request.session['cart']`). Cart data is NOT stored in the database.
  - `get_cart_details`: Re-reads item prices directly from MySQL to compute tamper-proof totals.
- `forms.py`:
  - `CheckoutForm`: Validates order type (`delivery`, `takeaway`, or `dine_in`), ensures delivery address is provided if delivery, and accepts simulated payment methods.
  - `OrderUpdateStatusForm`: Admin status update form.
  - `RestaurantTableForm`: Form to assign unique table numbers and create new dining tables with automatic QR token generation.
- `views.py`:
  - `cart_view`: Displays cart dishes, allows updating quantities, and presents checkout options.
  - `checkout`: Wraps order creation in `transaction.atomic()`, computes total from live database prices, copies current item price to `OrderItem.unit_price`, and saves order.
  - `payment_simulation`: Demonstration gateway step for card, banking, and e-wallet payments.
  - `my_orders`: List of orders belonging to the logged-in customer.
  - `order_detail`: Full order breakdown (ownership enforced: other users' orders return 404).
  - `cancel_order`: Allows customer to cancel pending orders. Unpaid cancelled orders get `payment_status = not_required`.
  - `manage_orders`: Admin order dashboard with status/type filters and compact, aligned reset button.
  - `manage_tables`: Admin table QR dashboard displaying all tables with live Base64 QR previews, add table form, metrics, and print sheet.
  - `create_table`: Assigns table number, generates unique `qr_token`, and saves table.
  - `toggle_table_active`: Toggles dining table between active and inactive.
  - `delete_table`: Deletes table record and removes its QR code with confirmation modal.
  - `regenerate_table_qr`: Generates a fresh QR token for an existing table.
  - `qr_table_entry`: `/t/<qr_token>/` route that assigns table to session and redirects to menu.
  - `clear_table`: Clears active table from session.
- `management/commands/generate_table_qr.py`:
  - Generates PNG QR codes for tables and saves them to `media/qr/`.

### App 5: `reservations`
- **Purpose**: Table reservations for customers and booking confirmations for admins.
- `models.py`:
  - `Reservation`: `account_id`, `reservation_date`, `reservation_time`, `party_size` (1-20), `status` (`pending`, `confirmed`, `rejected`, `cancelled`), `note`.
- `forms.py`:
  - `ReservationBookingForm`: Validates party size between 1 and 20, rejects past dates and times, and verifies time falls within restaurant operating hours (11:00 – 23:00).
- `views.py`:
  - `reservation_list`: Booking form and customer's own reservation list.
  - `cancel_reservation`: Customer cancels their future pending or confirmed reservation.
  - `manage_reservations`: Admin view to filter and click "Confirm" or "Reject".

### App 6: `dashboard`
- **Purpose**: Executive admin dashboard with ORM aggregations.
- `views.py`:
  - `dashboard`: Calculates today's sales, this month's sales, order counts, customer counts, 7-day sales trend (or dynamic period sales trend for Chart.js), orders by type, top 5 best-selling dishes, and recent orders. Supports custom date range filtering via `?start_date=YYYY-MM-DD` and `?end_date=YYYY-MM-DD`.
  - `download_report`: Exports a formatted sales and orders CSV report (`alkhair_sales_report_<dates>.csv`) with UTF-8 BOM encoding for direct opening in Microsoft Excel.
  - Contains multi-table join queries with comments explaining database integration.

---

## 3. How the Join Table `order_item` Works

In relational database design (BIK11003), a customer order can contain multiple menu items, and a single menu item can appear across many customer orders. This is a **many-to-many (M:N)** relationship.

To resolve this relationship into Third Normal Form (3NF), the join table `order_item` is introduced:

```
[ orders ] (1) <────── (N) [ order_item ] (N) ──────> (1) [ menu_item ]
```

### Key Attributes of `order_item`:
1. `order_id`: Foreign key referencing `orders.order_id` (`on_delete=models.CASCADE`). If an order is purged, its line items are removed.
2. `item_id`: Foreign key referencing `menu_item.item_id` (`on_delete=models.PROTECT`). A dish cannot be deleted from the database if order history exists for it.
3. `quantity`: Number of portions ordered.
4. `unit_price`: **Price snapshot at the time of order**. This is a critical business rule: if the restaurant later increases the menu price of a kebab from RM20 to RM25, previous orders must preserve the historical price of RM20.
5. `UniqueConstraint(fields=['order', 'item'])`: Guarantees one row per dish per order. If a customer orders 3 beef shawarmas, they are stored as one row with `quantity = 3`, never 3 separate rows.

---

## 4. Main User Workflows

### Flow 1: Registration and Authentication
1. Customer registers via `/accounts/register/`.
2. Password is automatically hashed using PBKDF2 SHA256; role is saved as `customer`.
3. Customer is immediately logged in via Django session framework and redirected to home.
4. When logging in, `url_has_allowed_host_and_scheme` verifies the `next` redirect parameter to prevent open redirect phishing attacks.

### Flow 2: Online Ordering (Delivery & Takeaway)
1. Customer visits `/menu/` and clicks "Add to Cart".
2. Item and quantity are stored in `request.session['cart']`.
3. Customer navigates to `/orders/cart/`.
4. The server queries MySQL for live prices and computes subtotals and total.
5. Customer selects "Delivery" (must input delivery address) or "Takeaway", and selects payment method.
6. Server opens `transaction.atomic()`:
   - Validates item availability.
   - Computes final total from database prices.
   - Inserts row into `orders`.
   - Inserts rows into `order_item` copying current price into `unit_price`.
   - Clears `request.session['cart']`.
7. If Cash: Redirects directly to `/orders/order/<id>/` with instructions to pay on delivery.
8. If Simulated Payment: Redirects to `/orders/payment-simulation/<id>/`.

### Flow 3: QR Code Dine-in
1. Customer sits at Table 4 and scans table QR code: `http://<ip>:8000/t/Lvjyjyspj9jhWR18fpr2_Q/`.
2. View `qr_table_entry` validates `qr_token` against `restaurant_table`.
3. Sets `request.session['table_id']` and `request.session['table_number'] = 4`.
4. Redirects to `/menu/` with a welcome banner and table badge in navbar.
5. At checkout, "Dine-in (Table #4)" is automatically selected and `table_id` is assigned to the `Order`. No delivery address is requested.

### Flow 4: Simulated Payment
1. Customer placing an order via `sim_banking`, `sim_card`, or `sim_ewallet` arrives at the simulation screen.
2. An amber warning states: *"This is a demonstration. No real payment is made."*
3. Clicking **"Simulate Successful Payment"** updates `payment_status = 'paid'`, keeping `order_status = 'pending'`.
4. Clicking **"Simulate Failed Payment"** updates `payment_status = 'failed'` and displays options to retry or switch to cash.
5. No credit card numbers, CVVs, or bank logins are ever accepted or stored.

### Flow 5: Table Reservation
1. Customer visits `/reservations/`.
2. Inputs date, time, party size (1–20), and special requests.
3. Form verifies date is not in the past, time is within operating hours (11:00–23:00), and today's reservations are not in the past.
4. Reservation is created with `status = 'pending'`.
5. Admin visits `/reservations/manage/` and clicks "Confirm" or "Reject".
6. Customer can cancel their own pending or confirmed reservation anytime.

### Flow 6: Executive Dashboard
1. Admin navigates to `/dashboard/`.
2. ORM aggregates live sales: `Order.objects.filter(payment_status='paid').exclude(order_status='cancelled')`.
3. Chart.js visualizes 7-day revenue trend.
4. Three-table join queries identify top-selling dishes and highest-spending patrons.

### Flow 7: Table QR Code Management & Physical Printing
1. Admin navigates to `/orders/tables/`.
2. Live Base64 QR code previews are generated on the fly for all active and inactive dining tables.
3. Admin can input a table number in the "Add New Table" section to generate a new table and unique QR token immediately.
4. Admin clicks "Print All QRs" to invoke `@media print` layout, producing printable tent cards formatted for restaurant tables.
5. Deletion of tables (or categories, items, orders, reservations) triggers the **Universal In-App Confirmation Modal** in `base.html` instead of standard browser popups.

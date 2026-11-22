# Alkhair Order and Reservation System — Manual Test Checklist & Screenshot Guide

This checklist details manual test procedures for each of the 13 pages and end-to-end user flows. It includes expected outcomes and a structured list of screenshots needed for the user manual and academic project report.

---

## 1. Credentials for Testing

| Account | Email | Password | Role |
|---|---|---|---|
| Demo Admin | `admin@gmail.com` | `Admin1234!` | Administrator |
| Customer 1 | `customer1@gmail.com` | `Customer1234!` | Registered Customer |
| Customer 2 | `customer2@gmail.com` | `Customer1234!` | Registered Customer |

---

## 2. Page-by-Page Test Steps (13 Pages)

### Page 1: Home Page (`/`)
- **Step 1**: Visit `http://127.0.0.1:8000/`.
- **Expected Result**: Page loads with 200 OK. Displays restaurant introduction, operating hours (11:00 AM to 11:00 PM), animated charcoal flame element, house specialties cards, and navigation bar.
- **Step 2**: Click "View Menu & Order".
- **Expected Result**: Smoothly navigates to `/menu/`.

### Page 2: Menu Page (`/menu/`)
- **Step 1**: Visit `/menu/`.
- **Expected Result**: Menu items appear grouped by category ("BBQ and Kebab", "Shawarma and Sandwiches"). Prices show in RM format (`RM 20.00`).
- **Step 2**: Click on category filter pill "Shawarma and Sandwiches".
- **Expected Result**: URL updates to `?category=2` and only shawarma dishes appear.
- **Step 3**: Click "All Categories".
- **Expected Result**: Full menu displays again.
- **Step 4**: Set quantity to 2 on "Chicken Shawarma (Large)" and click "Add to Cart".
- **Expected Result**: Success alert: *"Added Chicken Shawarma (Large) to your cart."* Navbar cart badge updates to 2.

### Page 3: About & Contact Page (`/about/`)
- **Step 1**: Click "About & Contact" in navbar.
- **Expected Result**: Displays the Alkhair story, confirmed Bandar Universiti, Parit Raja address, phone/WhatsApp contact, operating hours, and the Yemeni-building hero image.

### Page 4: Login Page (`/accounts/login/`)
- **Step 1**: Click "Login" in navbar.
- **Expected Result**: Sign In form with email and password fields.
- **Step 2**: Input invalid credentials (`wrong@gmail.com` / `WrongPass123`).
- **Expected Result**: Form re-renders with generic error: *"Invalid email or password. Please check your credentials."*
- **Step 3**: Input `customer1@gmail.com` / `Customer1234!`.
- **Expected Result**: Successfully logs in. Navbar displays customer name dropdown and cart badge.

### Page 5: Register Page (`/accounts/register/`)
- **Step 1**: Log out, then click "Register".
- **Expected Result**: Form with Full Name, Email, Phone, Address, Password, Confirm Password.
- **Step 2**: Register with mismatched passwords.
- **Expected Result**: Blocked with *"Passwords do not match."*
- **Step 3**: Register with valid data (`testnew@gmail.com`).
- **Expected Result**: Account created with `role = customer`, automatically signed in and redirected to home.

### Page 6: Cart & Checkout Page (`/orders/cart/`)
- **Step 1**: Add 1x "Plate beef kebab" (RM 20.00) and 2x "French fries" (RM 5.00 each).
- **Step 2**: Visit `/orders/cart/`.
- **Expected Result**: Table displays dishes with unit prices and subtotals (RM 20.00 + RM 10.00 = RM 30.00).
- **Step 3**: Use "+" button to increase french fries to 3 portions and click update.
- **Expected Result**: Total amount recalculates automatically on server to RM 35.00.
- **Step 4 (Delivery)**: Select "Delivery" and leave address blank. Click "Place Order".
- **Expected Result**: Blocked with error: *"Delivery address is required for delivery orders."*
- **Step 5 (Checkout with Cash)**: Enter delivery address `"No. 12 Jalan Universiti"`, select "Cash", click "Place Order".
- **Expected Result**: Cart emptied. Success alert: *"Order #X placed successfully! Please pay RM 35.00 in cash upon receiving your order."* Navigates to Order Detail.

### Page 7: Payment Simulation Step (`/orders/payment-simulation/<id>/`)
- **Step 1**: Add an item to cart and select "Online Banking FPX (Simulated)". Place Order.
- **Expected Result**: Redirects to `/orders/payment-simulation/<id>/`. Amber demonstration banner is visible: *"This is a demonstration. No real payment is made."*
- **Step 2**: Click "Simulate Failed Payment".
- **Expected Result**: Payment status marked "Failed". Option to retry or switch to cash appears.
- **Step 3**: Click "Simulate Successful Payment".
- **Expected Result**: Payment status marked "Paid". Redirects to order detail.

### Page 8: My Orders Page (`/orders/my-orders/`)
- **Step 1**: Click "My Orders" in customer navbar.
- **Expected Result**: Table listing all orders placed by the current customer with Date, Type, Total, Order Status, Payment Status, and Action buttons.
- **Step 2**: On a pending order, click "Cancel".
- **Expected Result**: Order status changes to "Cancelled" and unpaid order payment status changes to "Not Required".
- **Step 3**: Click "View Details".
- **Expected Result**: Navigates to `/orders/order/<id>/` displaying full breakdown.

### Page 9: Table Reservations Page (`/reservations/`)
- **Step 1**: Visit `/reservations/`.
- **Expected Result**: Booking form on left; existing customer reservations list on right.
- **Step 2**: Choose a date in the past (e.g. yesterday). Click "Request Reservation".
- **Expected Result**: Error: *"Reservation date cannot be in the past."*
- **Step 3**: Choose tomorrow's date at 03:00 AM.
- **Expected Result**: Error: *"Reservation time must be within restaurant operating hours (11:00 – 23:00)."*
- **Step 4**: Enter tomorrow's date at 19:30, party size 6, note "Family dinner".
- **Expected Result**: Reservation created with status "Pending". Appears immediately in the right-hand table.
- **Step 5**: Click "Cancel" on the reservation.
- **Expected Result**: Status updates to "Cancelled".

### Page 10: My Profile Page (`/accounts/profile/`)
- **Step 1**: Click user dropdown in navbar -> "My Profile".
- **Expected Result**: Displays account details (Name, Email, Role badge, Join Date).
- **Step 2**: Edit phone number and delivery address, click "Save Changes".
- **Expected Result**: Profile updates with success notification.
- **Step 3**: Change password with correct old password.
- **Expected Result**: Password updated; user session remains securely active.

### Page 11: Admin Dashboard (`/dashboard/`)
- **Step 1**: Log in as `admin@gmail.com`. Click "Dashboard".
- **Expected Result**:
  - Summary cards show Today's Sales (with "This month's sales"), Total Orders, Pending Orders, Total Customers.
  - Date Range Filter bar appears at the top ("From Date", "To Date", "Filter", "Reset", and "Download Report (CSV)" button).
  - Chart.js renders 7-day sales line chart.
  - Best-selling menu items table lists top 5 dishes.
  - Orders by channel summary (Dine-in, Delivery, Takeaway).
  - Recent orders table (last 10).
  - One-line business rule notice displayed at the top.
- **Step 2**: Select a date range (e.g. past 7 days) and click "Filter".
- **Expected Result**:
  - Summary cards update to show "Period Sales" and "Period Orders".
  - Chart.js updates daily sales trend across the selected dates.
  - Recent orders and top items filter to the selected period.
  - "Reset" button appears to clear filters.
- **Step 3**: Click "Download Report (CSV)".
- **Expected Result**: Downloads `alkhair_sales_report_<dates>.csv` containing executive revenue summary and itemized orders breakdown with customer, items, and payment details.

### Page 12: Admin Manage Menu (`/menu/manage/`)
- **Step 1**: Click "Manage Menu" in admin navbar.
- **Expected Result**: Displays Categories table and Menu Items table with status badges and actions.
- **Step 2**: Click "Add Category" -> Create "Beverages & Teas".
- **Step 3**: Click "Add Menu Item" -> Add "Adeni Spiced Tea", price RM 4.50.
- **Step 4**: Click "Make Inactive" toggle on an item.
- **Expected Result**: Status changes to "Unavailable" and item disappears from public customer menu.
- **Step 5**: Attempt to delete an item that was previously ordered.
- **Expected Result**: Deletion is blocked with friendly message: *"Menu item cannot be deleted because it has existing customer order records. Please toggle its availability to Unavailable instead."*

### Page 13: Admin Manage Orders (`/orders/manage/`)
- **Step 1**: Click "Manage Orders" in admin navbar.
- **Expected Result**: All orders listed. Status and Type filter dropdowns are active.
- **Step 2**: On a cash order, change payment status from "Pending" to "Paid", and order status from "Pending" to "Preparing". Click checkmark.
- **Expected Result**: Order record updates immediately. The cash payment now counts toward the dashboard sales total.

### Page 14: Admin Manage Reservations (`/reservations/manage/`)
- **Step 1**: Click "Manage Reservations" in admin navbar.
- **Expected Result**: Table of all customer bookings with status filter.
- **Step 2**: Click "Confirm" on a pending reservation.
- **Expected Result**: Status updates to "Confirmed".
- **Step 3**: Click "Reject" on a pending reservation.
- **Expected Result**: In-app confirmation modal appears ("Confirm Rejection"). Clicking Reject updates status to "Rejected".

### Page 15: Admin Table QR Codes (`/orders/tables/`)
- **Step 1**: Click "Table QR Codes" in admin sidebar.
- **Expected Result**:
  - Displays summary metrics: Total Tables, Active Dine-in, and Inactive Tables.
  - Cards grid displaying all table numbers, active badges, and live Base64 QR code previews.
- **Step 2**: Click "+ Add New Table", enter table number (e.g. 11), and submit.
- **Expected Result**: Table #11 and unique QR token are generated and appear immediately in the grid.
- **Step 3**: Click "Test" button on a table card.
- **Expected Result**: Opens `/t/<qr_token>/` in a new tab, activating the dine-in session for that table.
- **Step 4**: Click "Print All QRs".
- **Expected Result**: Print preview renders table tent cards with restaurant branding and large scannable QR codes.
- **Step 5**: Click the trash icon to delete a table.
- **Expected Result**: In-app confirmation modal appears ("Delete Table QR"). Clicking Delete Table removes the table record.

---

## 3. QR Dine-in End-to-End Test

1. Visit QR URL: `http://127.0.0.1:8000/t/Lvjyjyspj9jhWR18fpr2_Q/` (Table 4).
2. **Expected Result**: Success alert *"Welcome! You are seated at Table #4."* Navbar displays yellow badge: **[Table #4 x]**.
3. Add any dish to cart and navigate to `/orders/cart/`.
4. **Expected Result**: "Dine-in (Served to your table)" is pre-selected. No delivery address is required.
5. Place the order.
6. **Expected Result**: Order is created with `order_type = 'dine_in'` and `table_id` referencing Table 4.
7. Click the `x` on the navbar table badge.
8. **Expected Result**: Table context is cleared from the session.

---

## 4. Screenshot List for Academic Report & User Manual

Take these 17 screenshots for your coursework submission:

1. `01_home_page.png`: Home page showing banner, operating hours, and charcoal grill animation.
2. `02_public_menu.png`: Public menu with category pills and price tags.
3. `03_about_contact.png`: Location and contact details with Parit Raja address.
4. `04_customer_register.png`: Registration form with field validation.
5. `05_customer_login.png`: Sign In form.
6. `06_cart_view.png`: Shopping cart with quantity increment/decrement controls.
7. `07_checkout_delivery.png`: Checkout form with delivery address and payment options.
8. `08_payment_simulation.png`: Demonstration payment simulation gateway with amber banner.
9. `09_order_detail.png`: Order breakdown page showing items, unit prices, subtotal, and status.
10. `10_customer_reservations.png`: Reservation booking form and customer's upcoming bookings table.
11. `11_customer_profile.png`: Profile information and password change section.
12. `12_qr_table_badge.png`: Navbar showing active "Table #X" badge and dine-in welcome banner.
13. `13_admin_dashboard.png`: Executive dashboard showing summary metrics and Chart.js 7-day trend.
14. `14_admin_manage_menu.png`: Menu management table with category filter dropdown and availability toggles.
15. `15_admin_manage_orders.png`: Order fulfillment management with status filters and update controls.
16. `16_admin_manage_reservations.png`: Reservation confirmation interface with Confirm/Reject actions.
17. `17_admin_manage_tables.png`: Table QR management dashboard showing scannable QR cards and print preview.

# Changes and Enhancements from Original Agent Instructions

This document tracks all design refinements, architectural additions, and user interface enhancements introduced to the **Restoran Alkhair Order and Reservation System** compared to the baseline specification in [`AGENT_INSTRUCTIONS.md`](./AGENT_INSTRUCTIONS.md).

---

## 1. Summary of Changes

| Area | Baseline Specification (`AGENT_INSTRUCTIONS.md`) | Current Prototype Implementation | Rationale |
| :--- | :--- | :--- | :--- |
| **Table QR Management** | CLI management command only (`generate_table_qr.py`) generating static PNGs to `media/qr/`. | **Dedicated Admin GUI (`orders:manage_tables`)**: Interactive page to view all table QRs, assign table numbers, create tables, toggle availability, test links, download PNGs, and print table tent cards. | Enables restaurant staff to manage and print physical table cards directly from the browser without server terminal access. |
| **Admin Navigation** | Single shared navigation bar showing both public visitor links (*Home*, *Menu*, *About*) and admin links (*Dashboard*, *Manage...*). | **Specialized Admin Workspace**: Public customer-facing links are hidden for logged-in administrators. The sidebar begins cleanly at **Dashboard** and includes **Table QR Codes**. | Streamlines admin workflows and eliminates visual clutter in administrative back-office mode. |
| **Confirmation Popups** | Browser native `confirm()` alerts (`127.0.0.1:8000 says...`). | **Universal In-App Confirmation Modal (`#universalConfirmModal`)**: Global themed Bootstrap modal replacing all browser popups with contextual icons, messages, and action buttons. | Native alerts look outdated, display raw IP hostnames, block the browser thread, and conflict with modern UI design standards. |
| **Admin Menu Filtering** | Flat table of all categories and items without search or filtering. | **Category Filter Dropdown & Quick Badges**: Category dropdown in `Menu Items` card header (`?category=<id>`) with reset button, plus clickable category counts in the summary table. | Admins can quickly isolate and update items within a single category (e.g. Grills or Shawarmas) in a large menu. |
| **Filter Alignments** | Standard Bootstrap form rows with full-width reset buttons. | **Bottom-Aligned Compact Filter Controls**: Form rows use `align-items-end` with snug `col-auto` reset buttons labeled simply `Reset`. | Fixes vertical misalignment caused by input labels and prevents buttons from stretching awkwardly across the screen. |
| **Dashboard Sales Metric** | Summary card displaying Today's sales with an all-time sales subtotal. | **This Month's Sales Metric**: Displays "This month: RM XX.XX" under Today's Sales instead of all-time sales. | Focuses revenue metrics on current monthly operational cycles rather than lifetime totals. |
| **Date Range Filter & Report Download** | Static dashboard viewing only fixed current-day / 7-day data without export capabilities. | **Custom Date Range Filter & Sales CSV Report Download**: Admin can select `start_date` and `end_date` to filter all metrics, charts, and orders, plus one-click download of a comprehensive CSV sales report with UTF-8 BOM encoding. | Empowers management to generate custom periodic audit reports (e.g. weekly or monthly reviews) and export sales data directly into Excel/Sheets. |
| **Visual Aesthetics** | Generic Bootstrap default styling (blue primary, neon warning/info badges). | **Warm Middle-Eastern Food Theme**: Charcoal darks, warm food-ordering orange (`#f97316`), custom order status badges, Plus Jakarta Sans typography, and styled user profile card. | Creates a professional, appetizing restaurant identity tailored to an authentic Arabic & BBQ establishment. |

---

## 2. Detailed Breakdown of Additions

### A. Table QR Code Management GUI (`orders:manage_tables`)
- **Route**: `/orders/tables/`
- **View**: `orders.views.manage_tables`
- **Key Capabilities**:
  - Live in-memory Base64 QR code generation (`qrcode` library) so previews render instantly without requiring static media directory setup.
  - **Add New Table Form**: Form with `table_number` validation ensuring positive, unique table numbers, prefilled with the next available number.
  - **Availability Toggle**: Admin can pause/deactivate a dining table without deleting it.
  - **Direct Session Test**: One-click "Test" button that opens `/t/<qr_token>/` in a new tab to simulate customer QR scans immediately.
  - **One-Click Download**: Direct PNG download (`table_<num>_qr.png`).
  - **Print Sheet**: Dedicated `@media print` layout that prints ready-to-cut physical table tent cards with restaurant branding, table number, QR code, and customer instructions.

### B. Universal In-App Confirmation Modal
- **Template**: Embedded globally in `templates/base.html` (`#universalConfirmModal`).
- **Script**: Handled centrally in `static/js/main.js`.
- **Mechanism**: Automatically intercepts any element with a `data-confirm` attribute, eliminating native `window.confirm()` and `127.0.0.1:8000 says...` alerts.
- **Coverage**:
  - Delete Menu Item (`manage_menu.html`)
  - Delete Menu Category (`manage_menu.html`)
  - Delete Dining Table & QR (`manage_tables.html`)
  - Clear Shopping Cart (`cart.html`)
  - Cancel Customer Order (`my_orders.html` and `order_detail.html`)
  - Cancel Customer Reservation (`reservation_list.html`)
  - Reject Customer Reservation (`manage_reservations.html`)

### C. Admin Menu Filtering
- **Route**: `/menu/manage/?category=<id>`
- **View**: `menu.views.manage_menu`
- **Mechanism**:
  - Accepts `?category=<id>` GET query parameter.
  - Filters `MenuItem` queryset accordingly while keeping total categories and counts intact.
  - Category count pills in the top table link directly to filtered views.

### D. Specialized Admin Sidebar
- **Template**: `templates/base.html`
- **Rule**: If `user.is_authenticated and user.is_admin`, the top section of the sidebar hides *Home*, *Menu & Order*, and *About & Contact*, displaying:
  1. **Dashboard** (`bi-speedometer2`)
  2. **Manage Menu** (`bi-grid`)
  3. **Manage Orders** (`bi-inbox`)
  4. **Manage Reservations** (`bi-calendar2-range`)
  5. **Table QR Codes** (`bi-qr-code`)

### E. This Month's Sales Metric on Admin Dashboard
- **Route**: `/dashboard/`
- **View**: `dashboard.views.dashboard`
- **Template**: `templates/dashboard/dashboard.html`
- **Mechanism**: Calculates `this_month_sales` by filtering paid orders where `order_date__year=today.year` and `order_date__month=today.month`. The metric card displays `Today's Sales` prominently with a supporting `This month: RM XX.XX` figure below it, replacing the previous `All-time` metric.

### F. Date Range Filtering & Report CSV Download
- **Routes**:
  - `/dashboard/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
  - `/dashboard/report/download/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
- **Views**: `dashboard.views.dashboard` and `dashboard.views.download_report`
- **Template**: `templates/dashboard/dashboard.html`
- **Capabilities**:
  - **Custom Period Filtering**: Admin selects "From" and "To" dates; metrics, 30-day dynamic chart trend, channel breakdowns, best sellers, and recent orders update dynamically.
  - **Quick Reset**: One-click reset button restores default current-day/7-day view.
  - **CSV Report Download**: Generates a downloadable CSV (`alkhair_sales_report_<dates>.csv`) with UTF-8 BOM encoding for seamless opening in Microsoft Excel. Includes executive summary metrics (Period, Total Orders, Paid Revenue) and an itemized breakdown of all orders with items, pricing, customer details, and payment/fulfillment status.

---

## 3. Preserved Baseline Requirements (Unchanged)

All underlying relational database constraints, business rules, and academic criteria from `AGENT_INSTRUCTIONS.md` remain strictly intact:
1. **Database Schema**: 7 exact tables (`account`, `menu_category`, `menu_item`, `restaurant_table`, `orders`, `order_item`, `reservation`) with exact field names and PK/FK configurations.
2. **Join Table Integrity**: `order_item` resolves the M:N relationship with `UniqueConstraint(fields=['order', 'item'])` and price snapshots (`unit_price`).
3. **Atomic Pricing**: Total order calculations occur strictly on the server inside `transaction.atomic()`.
4. **Demonstration Payments**: Simulated gateway banner and test actions with strict separation between `order_status` and `payment_status`.
5. **Automated Test Suite**: Extended from 39 tests to **46 automated tests**, maintaining 100% pass rate.

# Alkhair Order and Reservation System

## Purpose

The Alkhair Order and Reservation System is a web application for Restoran Alkhair in Parit Raja, Johor. It brings the restaurant's menu, customer ordering, table reservations, and day-to-day administrative tasks into one application. Customers use the public website to learn about the restaurant and make requests; restaurant administrators use a protected workspace to maintain information and respond to those requests.

The application is a university project demonstration of a database-backed restaurant workflow. It is built with Django and presents pages through a responsive browser interface. Electronic payment is simulated for demonstration only; the system does not process real payments.

## People who use the system

### Visitors

Visitors can view the home page, restaurant information, and public menu. They can register for a customer account or sign in. An account is required for order checkout, order history, profile management, and reservations.

### Customers

Customers can update their contact details, add available menu items to a cart, select an order method, and view the status and details of their own orders. They can request reservations and review or cancel eligible future bookings. The application limits customer access to their own order and reservation records.

### Administrators

Administrators have access to a separate workspace. They can maintain menu categories and items, mark items available or unavailable, review orders and change their fulfillment status, record receipt of cash payments, confirm or reject reservations, and manage restaurant table QR codes. They can also review dashboard summaries and download a CSV report for a selected date range.

## Customer experience

### Browsing the menu

Menu items are grouped into categories and include a name, description, price, and availability. Administrators can add or edit dishes and categories. When a dish has already appeared in an order, it is protected from deletion so historical order details remain valid; an administrator can make it unavailable instead.

### Placing an order

Customers add available dishes to a shopping cart. Cart contents are kept in the browser session until checkout rather than being saved as a separate database record. At checkout, the customer selects one of three order methods:

- **Delivery** requires a delivery address.
- **Takeaway** is prepared for collection and does not use a delivery address or table.
- **Dine-in** is available when the customer entered through an active restaurant table's QR code. The table context is held for checkout and associated with the resulting order.

The server validates the cart and calculates the total using current menu prices during order creation. This prevents prices submitted by a browser from changing the amount charged in the record. Each order line keeps the price at the time of purchase, so later menu price edits do not rewrite order history. New orders start with a pending fulfillment status.

### Payment demonstration

Customers may select cash or one of the simulated electronic payment choices: online banking, card, or e-wallet. For a simulated method, the customer can mark the example transaction successful or failed. The page clearly states that no real payment is made. No card number, security code, bank password, or one-time passcode is collected. For cash, payment remains pending until an administrator records that cash was received.

Payment status and order fulfillment status are tracked separately. For example, an order can be paid while it is still being prepared. Customers can cancel their own orders only while the order remains pending. An unpaid order that is cancelled is marked as not requiring payment.

### Reserving a table

Signed-in customers submit a requested date, time, party size, and optional note. The party size must be between 1 and 20, and the requested date and time are checked against the configured date and opening-hour rules. Each request begins as pending. An administrator can confirm or reject it. Customers can cancel their own future reservation while it is pending or confirmed.

The opening and closing times in the project configuration are placeholders. The restaurant group should verify them before treating the reservation schedule as operational information.

## Restaurant administration

### Menu, orders, and reservations

The administrator workspace brings common restaurant tasks together. Menu tools support category and dish management, availability changes, and category filtering. Order tools support filtering by order status or type and moving orders through pending, preparing, ready, and completed, or cancelling them. Reservation tools let administrators review requests and record a decision.

### Table QR codes

Each restaurant table has a unique QR token. Scanning a valid code identifies the table in the customer's session so a dine-in order can be attached to it. Administrators can create tables, activate or deactivate them, regenerate QR tokens, preview or download QR images, test the link, and print table cards. Inactive or unknown table links cannot establish an active dine-in context.

### Dashboard and report

The dashboard provides a date-based view of restaurant activity. It includes sales and order summaries, pending order and reservation counts, a sales trend, best-selling dishes, order types, and recent orders. It defaults to today's activity and supports preset or custom date ranges. Sales are counted from orders marked paid, excluding cancelled orders. The administrator can export a CSV with summary and order details for the selected period.

## Information stored by the system

The application uses a relational database to store:

- **Accounts**: customer and administrator identity, contact information, role, and password hash.
- **Menu categories and items**: dish grouping, description, current price, optional image, and availability.
- **Restaurant tables**: table number, unique QR token, and active state.
- **Orders**: customer, optional table, order method, delivery address where relevant, separate fulfillment and payment statuses, total, and date.
- **Order items**: the dishes and quantities in each order, with a purchase-time unit-price snapshot.
- **Reservations**: customer, requested date and time, party size, note, and status.

An order can contain many dishes, and a dish can appear in many orders. The order-item records connect these two sides and store information specific to each dish within each order, such as quantity and purchase-time price.

## Access, security, and interface

Customers authenticate with an email address and password. Django handles password hashing, form validation, sessions, and CSRF protection. Administrative pages check the user's administrator role. Customer record pages enforce ownership so one customer cannot view or change another customer's orders or reservations.

The site uses a shared responsive layout with a mobile-friendly navigation system, Bootstrap components, and custom restaurant styling. Django messages provide feedback after actions. Administrative navigation is focused on the management workspace, while visitors and customers receive links for their public and account tasks.

## Scope and limitations

This project supports the coursework demonstration of restaurant ordering, reservations, relational database design, access control, and reporting. It does not connect to a real payment provider or provide inventory tracking, kitchen display, staff scheduling, discount management, table occupancy planning, or delivery-driver tracking. Menu images, contact information, opening hours, and some restaurant details may be placeholders that the group must verify and replace.

## Project context

This application was developed for the BIK11003 Database and BIK20404 Web Development coursework. For local setup and demonstration accounts, see the repository [README](../README.md). For the application structure, data model, and implementation flows, see the [Code Guide](CODE_GUIDE.md).

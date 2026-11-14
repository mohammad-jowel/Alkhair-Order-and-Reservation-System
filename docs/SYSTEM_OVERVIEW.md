# Alkhair Order and Reservation System

## Overview

The Alkhair Order and Reservation System is a web application for Restoran Alkhair in Parit Raja, Johor. It gives customers one place to browse the restaurant menu, place food orders, and request table reservations. Restaurant administrators use a separate workspace to maintain the menu, manage orders and reservations, and review sales activity.

The application is built with Django and serves pages through a responsive web interface. It is intended for a university project demonstration and models common restaurant workflows; payment options are simulations and do not transfer money.

## Who uses the system

- **Visitors** can view the home and restaurant information pages, browse the menu, and create an account or sign in.
- **Customers** can manage their profile, maintain a shopping cart, place delivery, takeaway, or QR-based dine-in orders, track their orders, and create or cancel eligible reservations.
- **Administrators** can manage menu categories and dishes, update order statuses and payment receipt, handle reservation requests, manage table QR codes, and view dashboard summaries and CSV reports.

## Main capabilities

### Menu and ordering

The menu is organized into categories and displays item descriptions, prices, and availability. Customers add available dishes to a session-based cart and choose delivery, takeaway, or dine-in when checking out. Delivery requires an address. Dine-in orders use the active table selected by scanning its QR code.

The server calculates the order total using current menu prices. Each order line stores a copy of the item's price at purchase time, preserving the order's historical total if the menu price later changes.

### Payments

Customers can choose cash or one of the simulated electronic payment methods. Simulated payments let the customer record a successful or failed demonstration result. No payment provider is contacted, and the system does not request card details, banking passwords, or one-time passcodes. Cash orders remain pending payment until an administrator records receipt.

### Reservations

Signed-in customers can request a reservation by date, time, and party size, with an optional note. Requests begin as pending. Administrators can confirm or reject them, and customers can cancel their own future reservations when their status permits it. The configured opening and closing hours are placeholders that the group should verify.

### Administration and reporting

The administrator workspace supports menu maintenance, order status changes, reservation decisions, and table QR management. The dashboard summarizes sales and order activity, shows trends and best-selling dishes, and provides a downloadable CSV report. Sales totals count paid orders that have not been cancelled.

## Data and access

The system keeps customer accounts, menu data, restaurant tables, orders, order lines, and reservations in a relational database. Customers sign in with email and password. Customer pages show only the signed-in customer's own orders and reservations; administrative tools require an administrator role.

## Project context

This application was developed for the BIK11003 Database and BIK20404 Web Development coursework. It demonstrates a relational data model, database-backed workflows, role-based access, responsive pages, and server-side validation. Setup instructions and demo accounts are in the repository [README](../README.md); the implementation details are in the [Code Guide](CODE_GUIDE.md).

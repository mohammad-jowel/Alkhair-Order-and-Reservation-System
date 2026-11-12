from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import Account
from menu.models import MenuCategory, MenuItem
from orders.models import Order, OrderItem, RestaurantTable


class OrdersTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Account.objects.create_superuser(
            email='admin_orders@alkhair.com',
            password='AdminPassword123!',
            full_name='Orders Admin'
        )
        self.customer1 = Account.objects.create_user(
            email='cust1_orders@alkhair.com',
            password='CustomerPassword123!',
            full_name='Customer One',
            phone='+60111111111',
            address='123 Parit Raja'
        )
        self.customer2 = Account.objects.create_user(
            email='cust2_orders@alkhair.com',
            password='CustomerPassword123!',
            full_name='Customer Two',
            phone='+60222222222',
            address='456 Batu Pahat'
        )
        self.category = MenuCategory.objects.create(category_name='Grills')
        self.item1 = MenuItem.objects.create(
            category=self.category,
            item_name='Beef Shawarma',
            description='Tasty shawarma',
            price=Decimal('15.00'),
            is_available=True
        )
        self.item2 = MenuItem.objects.create(
            category=self.category,
            item_name='Chicken Kebab',
            description='Grilled skewer',
            price=Decimal('18.00'),
            is_available=True
        )

    def test_cart_session_operations(self):
        """Test adding, updating, and clearing items in session cart."""
        # Add item1
        response = self.client.post(reverse('orders:cart_view'), {
            'action': 'add',
            'item_id': self.item1.item_id,
            'quantity': 2,
        })
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart.get(str(self.item1.item_id)), 2)

        # Update item1
        response = self.client.post(reverse('orders:cart_view'), {
            'action': 'update',
            'item_id': self.item1.item_id,
            'quantity': 3,
        })
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get('cart', {})
        self.assertEqual(cart.get(str(self.item1.item_id)), 3)

        # Remove item1
        response = self.client.post(reverse('orders:cart_view'), {
            'action': 'remove',
            'item_id': self.item1.item_id,
        })
        self.assertEqual(response.status_code, 302)
        cart = self.client.session.get('cart', {})
        self.assertNotIn(str(self.item1.item_id), cart)

    def test_checkout_server_side_total_and_unit_price(self):
        """Checkout calculates total on the server and freezes unit_price into order_item."""
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        
        # Put 2 items in cart (2x item1 @ 15.00 = 30.00, 1x item2 @ 18.00 = 18.00, total = 48.00)
        session = self.client.session
        session['cart'] = {str(self.item1.item_id): 2, str(self.item2.item_id): 1}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'order_type': 'takeaway',
            'payment_method': 'cash',
        })
        self.assertEqual(response.status_code, 302)

        order = Order.objects.filter(account=self.customer1).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.total_amount, Decimal('48.00'))
        self.assertEqual(order.order_status, 'pending')
        self.assertEqual(order.payment_status, 'pending')

        # Check OrderItem records and unit prices
        items = order.items.all()
        self.assertEqual(items.count(), 2)
        oi1 = items.get(item=self.item1)
        self.assertEqual(oi1.unit_price, Decimal('15.00'))
        self.assertEqual(oi1.quantity, 2)

    def test_delivery_order_requires_address(self):
        """Delivery orders fail validation if address is blank."""
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        session = self.client.session
        session['cart'] = {str(self.item1.item_id): 1}
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'order_type': 'delivery',
            'delivery_address': '', # empty
            'payment_method': 'cash',
        })
        # Should redirect back with error message and NOT create order
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Order.objects.filter(account=self.customer1).exists())

    def test_customer_cannot_view_another_customer_order(self):
        """Customer receives 404 when trying to view someone else's order."""
        order = Order.objects.create(
            account=self.customer1,
            order_type='takeaway',
            order_status='pending',
            payment_method='cash',
            payment_status='pending',
            total_amount=Decimal('15.00')
        )
        self.client.login(email='cust2_orders@alkhair.com', password='CustomerPassword123!')
        response = self.client.get(reverse('orders:order_detail', args=[order.order_id]))
        self.assertEqual(response.status_code, 404)

    def test_cancel_pending_order_sets_payment_not_required(self):
        """Customer can cancel pending order; unpaid order gets payment_status = not_required."""
        order = Order.objects.create(
            account=self.customer1,
            order_type='takeaway',
            order_status='pending',
            payment_method='cash',
            payment_status='pending',
            total_amount=Decimal('15.00')
        )
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        response = self.client.post(reverse('orders:cancel_order', args=[order.order_id]))
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'cancelled')
        self.assertEqual(order.payment_status, 'not_required')

    def test_admin_manage_orders(self):
        """Admin can view and update order status."""
        order = Order.objects.create(
            account=self.customer1,
            order_type='takeaway',
            order_status='pending',
            payment_method='cash',
            payment_status='pending',
            total_amount=Decimal('15.00')
        )
        self.client.login(email='admin_orders@alkhair.com', password='AdminPassword123!')
        response = self.client.post(reverse('orders:manage_orders'), {
            'order_id': order.order_id,
            'order_status': 'preparing',
            'payment_status': 'paid',
        })
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.order_status, 'preparing')
        self.assertEqual(order.payment_status, 'paid')

    def test_qr_dine_in_valid_token(self):
        """Scanning a valid active table QR sets session and redirects to menu."""
        table = RestaurantTable.objects.create(table_number=99, qr_token='token_table_99', is_active=True)
        response = self.client.get(reverse('orders:qr_table_entry', args=['token_table_99']))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('menu:menu_list'))
        self.assertEqual(self.client.session.get('table_id'), table.table_id)
        self.assertEqual(self.client.session.get('table_number'), 99)

    def test_qr_dine_in_invalid_or_inactive_token(self):
        """Unknown or inactive QR token redirects to menu with friendly error without setting session."""
        inactive_table = RestaurantTable.objects.create(table_number=98, qr_token='token_inactive', is_active=False)
        response = self.client.get(reverse('orders:qr_table_entry', args=['token_inactive']))
        self.assertEqual(response.status_code, 302)
        self.assertIsNone(self.client.session.get('table_id'))

        response_bad = self.client.get(reverse('orders:qr_table_entry', args=['nonexistent_token']))
        self.assertEqual(response_bad.status_code, 302)
        self.assertIsNone(self.client.session.get('table_id'))

    def test_checkout_dine_in_associates_table(self):
        """Dine-in checkout requires active table in session and saves table_id on the order."""
        table = RestaurantTable.objects.create(table_number=50, qr_token='token_table_50', is_active=True)
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        
        session = self.client.session
        session['cart'] = {str(self.item1.item_id): 1}
        session['table_id'] = table.table_id
        session['table_number'] = table.table_number
        session.save()

        response = self.client.post(reverse('orders:checkout'), {
            'order_type': 'dine_in',
            'payment_method': 'cash',
        })
        self.assertEqual(response.status_code, 302)
        order = Order.objects.filter(account=self.customer1, order_type='dine_in').first()
        self.assertIsNotNone(order)
        self.assertEqual(order.table, table)
        self.assertIsNone(order.delivery_address)

    def test_clear_table_removes_session(self):
        """Clearing table removes table_id and table_number from session."""
        session = self.client.session
        session['table_id'] = 1
        session['table_number'] = 1
        session.save()

        response = self.client.get(reverse('orders:clear_table'))
        self.assertEqual(response.status_code, 302)
        self.assertNotIn('table_id', self.client.session)
        self.assertNotIn('table_number', self.client.session)

    def test_payment_simulation_success(self):
        """Simulating success sets payment_status = paid and keeps order_status separate."""
        order = Order.objects.create(
            account=self.customer1,
            order_type='takeaway',
            order_status='pending',
            payment_method='sim_card',
            payment_status='pending',
            total_amount=Decimal('25.00')
        )
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        response = self.client.post(reverse('orders:payment_simulation', args=[order.order_id]), {
            'simulation_result': 'success'
        })
        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'paid')
        self.assertEqual(order.order_status, 'pending')

    def test_payment_simulation_failure_and_switch_to_cash(self):
        """Simulating failure sets payment_status = failed; user can switch to cash."""
        order = Order.objects.create(
            account=self.customer1,
            order_type='delivery',
            delivery_address='Parit Raja',
            order_status='pending',
            payment_method='sim_banking',
            payment_status='pending',
            total_amount=Decimal('30.00')
        )
        self.client.login(email='cust1_orders@alkhair.com', password='CustomerPassword123!')
        
        # Test failure
        response = self.client.post(reverse('orders:payment_simulation', args=[order.order_id]), {
            'simulation_result': 'fail'
        })
        self.assertEqual(response.status_code, 200)
        order.refresh_from_db()
        self.assertEqual(order.payment_status, 'failed')
        self.assertEqual(order.order_status, 'pending')

        # Test switch to cash
        response_cash = self.client.post(reverse('orders:payment_simulation', args=[order.order_id]), {
            'simulation_result': 'switch_to_cash'
        })
        self.assertEqual(response_cash.status_code, 302)
        order.refresh_from_db()
        self.assertEqual(order.payment_method, 'cash')
        self.assertEqual(order.payment_status, 'pending')

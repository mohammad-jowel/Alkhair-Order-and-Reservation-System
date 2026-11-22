from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from accounts.models import Account
from reservations.models import Reservation


class ReservationsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Account.objects.create_superuser(
            email='admin_res@alkhair.com',
            password='AdminPassword123!',
            full_name='Res Admin'
        )
        self.customer1 = Account.objects.create_user(
            email='cust1_res@alkhair.com',
            password='CustomerPassword123!',
            full_name='Customer One',
            phone='+60123456789'
        )
        self.customer2 = Account.objects.create_user(
            email='cust2_res@alkhair.com',
            password='CustomerPassword123!',
            full_name='Customer Two',
            phone='+60987654321'
        )

    def test_customer_can_book_valid_reservation(self):
        """Customer can book reservation with valid future date and time."""
        self.client.login(email='cust1_res@alkhair.com', password='CustomerPassword123!')
        future_date = timezone.localdate() + timedelta(days=2)
        response = self.client.post(reverse('reservations:reservation_list'), {
            'reservation_date': future_date.strftime('%Y-%m-%d'),
            'reservation_time': '19:30',
            'party_size': 4,
            'note': 'Window seat please',
        })
        self.assertEqual(response.status_code, 302)
        res = Reservation.objects.filter(account=self.customer1).first()
        self.assertIsNotNone(res)
        self.assertEqual(res.party_size, 4)
        self.assertEqual(res.status, 'pending')

    def test_past_date_reservation_rejected(self):
        """Booking a table with past date fails validation."""
        self.client.login(email='cust1_res@alkhair.com', password='CustomerPassword123!')
        past_date = timezone.localdate() - timedelta(days=1)
        response = self.client.post(reverse('reservations:reservation_list'), {
            'reservation_date': past_date.strftime('%Y-%m-%d'),
            'reservation_time': '19:30',
            'party_size': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.filter(account=self.customer1).exists())

    def test_invalid_operating_hours_rejected(self):
        """Reservation outside 11:00 to 23:00 fails validation."""
        self.client.login(email='cust1_res@alkhair.com', password='CustomerPassword123!')
        future_date = timezone.localdate() + timedelta(days=2)
        response = self.client.post(reverse('reservations:reservation_list'), {
            'reservation_date': future_date.strftime('%Y-%m-%d'),
            'reservation_time': '03:00', # 3 AM
            'party_size': 2,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.filter(account=self.customer1).exists())

    def test_invalid_party_size_rejected(self):
        """Party size outside 1 to 20 fails validation."""
        self.client.login(email='cust1_res@alkhair.com', password='CustomerPassword123!')
        future_date = timezone.localdate() + timedelta(days=2)
        response = self.client.post(reverse('reservations:reservation_list'), {
            'reservation_date': future_date.strftime('%Y-%m-%d'),
            'reservation_time': '19:00',
            'party_size': 25, # exceeds 20
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Reservation.objects.filter(account=self.customer1).exists())

    def test_customer_can_cancel_own_reservation(self):
        """Customer can cancel their pending reservation."""
        future_date = timezone.localdate() + timedelta(days=2)
        res = Reservation.objects.create(
            account=self.customer1,
            reservation_date=future_date,
            reservation_time='18:00',
            party_size=2,
            status='pending'
        )
        self.client.login(email='cust1_res@alkhair.com', password='CustomerPassword123!')
        response = self.client.post(reverse('reservations:cancel_reservation', args=[res.reservation_id]))
        self.assertEqual(response.status_code, 302)
        res.refresh_from_db()
        self.assertEqual(res.status, 'cancelled')

    def test_customer_cannot_cancel_other_customer_reservation(self):
        """Customer receives 404 when attempting to cancel another customer's reservation."""
        future_date = timezone.localdate() + timedelta(days=2)
        res = Reservation.objects.create(
            account=self.customer1,
            reservation_date=future_date,
            reservation_time='18:00',
            party_size=2,
            status='pending'
        )
        self.client.login(email='cust2_res@alkhair.com', password='CustomerPassword123!')
        response = self.client.post(reverse('reservations:cancel_reservation', args=[res.reservation_id]))
        self.assertEqual(response.status_code, 404)

    def test_admin_confirm_reservation(self):
        """Admin can confirm reservation."""
        future_date = timezone.localdate() + timedelta(days=2)
        res = Reservation.objects.create(
            account=self.customer1,
            reservation_date=future_date,
            reservation_time='18:00',
            party_size=2,
            status='pending'
        )
        self.client.login(email='admin_res@alkhair.com', password='AdminPassword123!')
        response = self.client.post(reverse('reservations:manage_reservations'), {
            'reservation_id': res.reservation_id,
            'action': 'confirm',
        })
        self.assertEqual(response.status_code, 302)
        res.refresh_from_db()
        self.assertEqual(res.status, 'confirmed')

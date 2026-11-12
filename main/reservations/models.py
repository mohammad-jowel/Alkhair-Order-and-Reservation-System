from django.db import models
from django.conf import settings


class Reservation(models.Model):
    """
    Table reservation model matching table 'reservation'.
    Primary key: reservation_id.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ]

    reservation_id = models.AutoField(primary_key=True)
    account = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        db_column='account_id',
        related_name='reservations'
    )
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    party_size = models.PositiveIntegerField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    note = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reservation'
        verbose_name = 'Reservation'
        verbose_name_plural = 'Reservations'
        ordering = ['-reservation_date', '-reservation_time']
        indexes = [
            models.Index(fields=['account']),
            models.Index(fields=['reservation_date']),
        ]

    def __str__(self):
        return f"Reservation #{self.reservation_id} for {self.account.full_name} on {self.reservation_date} at {self.reservation_time} ({self.status})"

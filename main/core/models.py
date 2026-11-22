from django.db import models


class RestaurantDemoSeedRecord(models.Model):
    """Durable ownership record for objects created by the restaurant demo seed."""

    record_id = models.AutoField(primary_key=True)
    seed_key = models.CharField(max_length=64)
    object_type = models.CharField(max_length=32)
    object_id = models.PositiveIntegerField()

    class Meta:
        db_table = 'restaurant_demo_seed_record'
        constraints = [
            models.UniqueConstraint(
                fields=['seed_key', 'object_type', 'object_id'],
                name='unique_restaurant_demo_seed_record',
            ),
        ]
    def __str__(self):
        return f'{self.seed_key}: {self.object_type} #{self.object_id}'

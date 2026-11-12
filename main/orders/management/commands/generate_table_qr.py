import os
import qrcode
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import RestaurantTable


class Command(BaseCommand):
    help = 'Generates QR code PNG images for all active restaurant tables and saves to media/qr/.'

    def handle(self, *args, **options):
        tables = RestaurantTable.objects.filter(is_active=True).order_by('table_number')
        if not tables.exists():
            self.stdout.write(self.style.WARNING('No active restaurant tables found. Run seed_demo first.'))
            return

        # Prepare target output directory: MEDIA_ROOT / qr
        qr_dir = Path(settings.MEDIA_ROOT) / 'qr'
        qr_dir.mkdir(parents=True, exist_ok=True)

        site_base_url = getattr(settings, 'SITE_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')

        self.stdout.write(self.style.NOTICE(f'Generating table QR codes using base URL: {site_base_url}'))

        for table in tables:
            target_url = f"{site_base_url}/t/{table.qr_token}/"
            file_name = f"table_{table.table_number}.png"
            file_path = qr_dir / file_name

            # Generate QR code
            img = qrcode.make(target_url)
            img.save(str(file_path))

            self.stdout.write(
                self.style.SUCCESS(f'Table #{table.table_number:2d} -> {file_path.name} ({target_url})')
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSuccessfully generated {tables.count()} QR codes in: {qr_dir}\n'
                f'Note: For mobile phone scanning over local Wi-Fi, update SITE_BASE_URL in .env to your LAN IP '
                f'(e.g. http://192.168.1.50:8000) and re-run this command.'
            )
        )

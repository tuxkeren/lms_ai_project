from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from lms_app.models import PenilaianAI
from lms_app.tasks import proses_penilaian_ai


class Command(BaseCommand):
    help = "Proses ulang semua penilaian yang masih PENDING atau FAILED."

    def add_arguments(self, parser):
        parser.add_argument(
            '--ids',
            type=int,
            nargs='*',
            help='ID penilaian tertentu. Jika kosong, proses semua PENDING/FAILED.',
        )

    def handle(self, *args, **options):
        ids = options.get('ids')
        if ids:
            daftar = PenilaianAI.objects.filter(id__in=ids)
        else:
            daftar = PenilaianAI.objects.filter(
                Q(status='PENDING') | Q(status='FAILED')
            )

        jumlah = 0
        for penilaian in daftar:
            penilaian.status = 'PENDING'
            penilaian.skor_ai = None
            penilaian.feedback_ai = None
            penilaian.diproses_pada = None
            penilaian.save()
            try:
                proses_penilaian_ai.delay(penilaian.id)
                jumlah += 1
            except Exception as e:
                penilaian.status = 'FAILED'
                penilaian.feedback_ai = f"Gagal antre: {e}"
                penilaian.save()

        self.stdout.write(
            self.style.SUCCESS(f"{jumlah} penilaian diantrekan untuk diproses ulang.")
        )
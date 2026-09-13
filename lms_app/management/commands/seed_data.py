from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

from lms_app.models import Kursus, Ujian, Soal, Enrollmen
from lms_app.services import NAMA_GROUP_STUDENT


class Command(BaseCommand):
    help = "Seed: buat group Student, beberapa user student, kursus, dan enroll."

    def add_arguments(self, parser):
        parser.add_argument('--jumlah-siswa', type=int, default=5,
                            help='Jumlah user student yang dibuat (default: 5)')
        parser.add_argument('--password', default='student123',
                            help='Password default untuk semua user student')
        parser.add_argument('--uji-siswa-pertama', action='store_true',
                            help='Buatkan ujian+soal contoh untuk kursus siswa pertama')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        jumlah = kwargs['jumlah_siswa']
        password = kwargs['password']

        group, _ = Group.objects.get_or_create(name=NAMA_GROUP_STUDENT)

        kursus_data = [
            ('Matematika Dasar', 'MAT101', 'Konsep aljabar, fungsi, dan statistika.'),
            ('Fisika Dasar', 'FIS101', 'Mekanika, energi, dan gerak.'),
            ('Bahasa Inggris', 'BIN101', 'Tata bahasa dan menulis akademik.'),
        ]
        kursus_list = []
        for nama, kode, deskripsi in kursus_data:
            kursus, _ = Kursus.objects.get_or_create(kode=kode, defaults={
                'nama': nama,
                'deskripsi': deskripsi,
            })
            kursus_list.append(kursus)

        for i in range(1, jumlah + 1):
            username = f'student{i:02d}'
            user, created = self._buat_user(username, password)
            user.groups.add(group)
            kursus = kursus_list[i % len(kursus_list)]
            Enrollmen.objects.get_or_create(siswa=user, kursus=kursus)
            if created:
                status = 'dibuat'
            else:
                status = 'sudah ada'
            self.stdout.write(self.style.SUCCESS(f"{status}: {username} -> enroll {kursus.nama}"))

        if kwargs['uji_siswa_pertama']:
            self._buat_ujian_contoh(kursus_list[0])

        self.stdout.write(self.style.WARNING(
            f"Group '{NAMA_GROUP_STUDENT}' siap. Login menggunakan {username} / {password}"
        ))

    def _buat_user(self, username, password):
        from django.contrib.auth.models import User
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'first_name': username,
                'email': f'{username}@contoh.sch.id',
            },
        )
        if created:
            user.set_password(password)
            user.save()
        return user, created

    def _buat_ujian_contoh(self, kursus):
        from django.utils import timezone
        from datetime import timedelta
        if kursus.daftar_ujian.exists():
            self.stdout.write(self.style.WARNING("Ujian contoh sudah ada, dilewati."))
            return

        ujian = Ujian.objects.create(
            judul=f'UTS {kursus.nama}',
            deskripsi='Ujian tengah semester (contoh).',
            kursus=kursus,
            waktu_mulai=timezone.now() - timedelta(hours=1),
            waktu_selesai=timezone.now() + timedelta(hours=2),
        )
        Soal.objects.create(
            ujian=ujian,
            teks_soal='Jelaskan apa yang dimaksud dengan fungsi dalam matematika?',
            kunci_jawaban='Fungsi adalah relasi yang menghubungkan setiap elemen domain dengan tepat satu elemen kodomain.',
        )
        self.stdout.write(self.style.SUCCESS(f"Ujian contoh dibuat: {ujian.judul}"))
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.db import transaction

from lms_app.models import Kursus, Ujian, Soal, Enrollmen, Pengajaran
from lms_app.services import NAMA_GROUP_STUDENT, NAMA_GROUP_TEACHER


class Command(BaseCommand):
    help = "Seed: buat group Student & Teacher, user student/guru, kursus, enroll, dan pengajaran."

    def add_arguments(self, parser):
        parser.add_argument('--jumlah-siswa', type=int, default=5,
                            help='Jumlah user student yang dibuat (default: 5)')
        parser.add_argument('--password', default='student123',
                            help='Password default untuk semua user student')
        parser.add_argument('--jumlah-guru', type=int, default=4,
                            help='Jumlah user guru yang dibuat (default: 4)')
        parser.add_argument('--password-guru', default='teacher123',
                            help='Password default untuk semua user guru')
        parser.add_argument('--uji-siswa-pertama', action='store_true',
                            help='Buatkan ujian+soal contoh untuk kursus siswa pertama')
        parser.add_argument('--uji-contoh', action='store_true',
                            help='Buatkan ujian+soal contoh untuk semua kursus')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        jumlah_siswa = kwargs['jumlah_siswa']
        password_siswa = kwargs['password']
        jumlah_guru = kwargs['jumlah_guru']
        password_guru = kwargs['password_guru']

        group_siswa, _ = Group.objects.get_or_create(name=NAMA_GROUP_STUDENT)
        group_guru, _ = Group.objects.get_or_create(name=NAMA_GROUP_TEACHER)

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

        for i in range(1, jumlah_siswa + 1):
            username = f'student{i:02d}'
            user, created = self._buat_user(username, password_siswa)
            user.groups.add(group_siswa)
            kursus = kursus_list[i % len(kursus_list)]
            Enrollmen.objects.get_or_create(siswa=user, kursus=kursus)
            status = 'dibuat' if created else 'sudah ada'
            self.stdout.write(self.style.SUCCESS(f"{status}: {username} -> enroll {kursus.nama}"))

        for i in range(1, jumlah_guru + 1):
            username = f'guru{i:02d}'
            user, created = self._buat_user(username, password_guru)
            user.groups.add(group_guru)
            kursus = kursus_list[i % len(kursus_list)]
            Pengajaran.objects.get_or_create(guru=user, kursus=kursus)
            status = 'dibuat' if created else 'sudah ada'
            self.stdout.write(self.style.SUCCESS(f"{status}: {username} -> mengajar {kursus.nama}"))

        if kwargs['uji_siswa_pertama']:
            self._buat_ujian_contoh(kursus_list[0])

        if kwargs['uji_contoh']:
            for kursus in kursus_list:
                self._buat_ujian_contoh(kursus)

        self.stdout.write(self.style.WARNING(
            f"Group '{NAMA_GROUP_STUDENT}' & '{NAMA_GROUP_TEACHER}' siap. "
            f"Login student: student01 / {password_siswa}, guru: guru01 / {password_guru}"
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
            self.stdout.write(self.style.WARNING(f"Ujian contoh untuk {kursus.nama} sudah ada, dilewati."))
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
            teks_soal=f'Jelaskan konsep dasar dari {kursus.nama}.',
            kunci_jawaban=f'Konsep dasar {kursus.nama} meliputi prinsip dan penerapannya.',
        )
        self.stdout.write(self.style.SUCCESS(f"Ujian contoh dibuat: {ujian.judul}"))
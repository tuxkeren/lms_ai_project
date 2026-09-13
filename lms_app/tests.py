from django.contrib.auth.models import User, Group
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Ujian, Soal, JawabanSiswa, PenilaianAI, Kursus, Enrollmen, Pengajaran
from .services import group_student, group_teacher, NAMA_GROUP_STUDENT


class ModelTestCase(TestCase):
    def setUp(self):
        self.siswa = User.objects.create_user(username='siswa', password='tes12345')
        self.kursus = Kursus.objects.create(nama='Matematika', kode='MAT101')
        self.ujian = Ujian.objects.create(
            judul='Ujian Tengah Semester',
            kursus=self.kursus,
            waktu_mulai=timezone.now() - timedelta(hours=1),
            waktu_selesai=timezone.now() + timedelta(hours=1),
        )
        self.soal = Soal.objects.create(
            ujian=self.ujian,
            teks_soal='Jelaskan konsep dasar AI.',
            kunci_jawaban='AI adalah kecerdasan buatan.',
        )

    def test_soal_terkait_ke_ujian(self):
        self.assertEqual(self.ujian.daftar_soal.count(), 1)

    def test_satu_siswa_hanya_satu_jawaban_per_soal(self):
        JawabanSiswa.objects.create(soal=self.soal, siswa=self.siswa, teks_jawaban='jawaban 1')
        with self.assertRaises(Exception):
            JawabanSiswa.objects.create(soal=self.soal, siswa=self.siswa, teks_jawaban='jawaban 2')

    def test_penilaian_ai_default_pending(self):
        jawaban = JawabanSiswa.objects.create(soal=self.soal, siswa=self.siswa, teks_jawaban='jawaban')
        penilaian = PenilaianAI.objects.create(jawaban=jawaban)
        self.assertEqual(penilaian.status, 'PENDING')

    def test_enrollmen_unik_per_kursus(self):
        Enrollmen.objects.create(kursus=self.kursus, siswa=self.siswa)
        with self.assertRaises(Exception):
            Enrollmen.objects.create(kursus=self.kursus, siswa=self.siswa)


class ViewTestCase(TestCase):
    def setUp(self):
        self.siswa = User.objects.create_user(username='siswa', password='tes12345')
        group_student().user_set.add(self.siswa)
        self.instruktur = User.objects.create_superuser(username='admin', password='tes12345', email='a@a.com')

        self.kursus = Kursus.objects.create(nama='Matematika', kode='MAT101')
        self.kursus_lain = Kursus.objects.create(nama='Fisika', kode='FIS101')
        Enrollmen.objects.create(kursus=self.kursus, siswa=self.siswa)

        self.ujian = Ujian.objects.create(
            judul='Ujian Tengah Semester',
            kursus=self.kursus,
            waktu_mulai=timezone.now() - timedelta(hours=1),
            waktu_selesai=timezone.now() + timedelta(hours=1),
        )
        self.berakhir = Ujian.objects.create(
            judul='Ujian Lama',
            kursus=self.kursus,
            waktu_mulai=timezone.now() - timedelta(days=2),
            waktu_selesai=timezone.now() - timedelta(days=1),
        )
        self.soal = Soal.objects.create(
            ujian=self.ujian,
            teks_soal='Jelaskan konsep dasar AI.',
            kunci_jawaban='AI adalah kecerdasan buatan.',
        )
        self.soal_berakhir = Soal.objects.create(
            ujian=self.berakhir,
            teks_soal='Soal ujian lama.',
            kunci_jawaban='Kunci ujian lama.',
        )
        self.ujian_bukan_enroll = Ujian.objects.create(
            judul='Ujian Kursus Lain',
            kursus=None,
            waktu_mulai=timezone.now() - timedelta(hours=1),
            waktu_selesai=timezone.now() + timedelta(hours=1),
        )
        self.soal_kursus_lain = Soal.objects.create(
            ujian=self.ujian_bukan_enroll,
            teks_soal='Soal dari kursus lain yang belum di-enroll.',
            kunci_jawaban='Kunci soal kursus lain.',
        )

        self.guru = self._buat_guru('guru')
        group_teacher().user_set.add(self.guru)
        self.guru_lain = self._buat_guru('guru_lain')
        Pengajaran.objects.create(guru=self.guru, kursus=self.kursus)
        Pengajaran.objects.create(guru=self.guru_lain, kursus=self.kursus_lain)

        self.ujian_fisika = Ujian.objects.create(
            judul='Ujian Fisika',
            kursus=self.kursus_lain,
            waktu_mulai=timezone.now() - timedelta(hours=1),
            waktu_selesai=timezone.now() + timedelta(hours=1),
        )
        self.soal_fisika = Soal.objects.create(
            ujian=self.ujian_fisika,
            teks_soal='Soal Fisika.',
            kunci_jawaban='Kunci Fisika.',
        )

    def _buat_guru(self, username):
        return User.objects.create_user(username=username, password='tes12345')

    def test_beranda_terbuka_tanpa_login(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)

    def test_form_jawab_wajib_login(self):
        response = self.client.get(f'/soal/{self.soal.id}/jawab/')
        self.assertEqual(response.status_code, 302)

    def test_logout_melalui_post(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.post('/logout/')
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')
        page = self.client.get('/')
        self.assertNotContains(page, 'siswa')

    def test_login_halaman_tampil(self):
        response = self.client.get('/masuk/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masuk ke LMS AI')

    def test_login_berhasil_redirect_ke_beranda(self):
        response = self.client.post('/masuk/', {
            'username': 'siswa',
            'password': 'tes12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/')

    def test_login_password_salah_menampilkan_error(self):
        response = self.client.post('/masuk/', {
            'username': 'siswa',
            'password': 'salah',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Masuk ke LMS AI')

    def test_login_hormati_next_url(self):
        response = self.client.post('/masuk/?next=/soal/1/jawab/', {
            'username': 'siswa',
            'password': 'tes12345',
            'next': '/soal/1/jawab/',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], '/soal/1/jawab/')

    def test_logout_menolak_get(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get('/logout/')
        self.assertEqual(response.status_code, 405)

    def test_form_jawab_ditampilkan_untuk_siswa_yang_enroll(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get(f'/soal/{self.soal.id}/jawab/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Jelaskan konsep dasar AI.')

    def test_jawaban_ditolak_setelah_ujian_berakhir(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get(f'/soal/{self.soal_berakhir.id}/jawab/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ujian Telah Berakhir')

    def test_student_ditolak_soal_dari_kursus_lain(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get(f'/soal/{self.soal_kursus_lain.id}/jawab/')
        self.assertEqual(response.status_code, 403)

    def test_user_bukan_student_ditolak(self):
        orang = User.objects.create_user(username='orang', password='tes12345')
        self.client.login(username='orang', password='tes12345')
        response = self.client.get(f'/soal/{self.soal.id}/jawab/')
        self.assertEqual(response.status_code, 403)

    def test_instruktur_bisa_akses_semua_soal(self):
        self.client.login(username='admin', password='tes12345')
        response = self.client.get(f'/soal/{self.soal_kursus_lain.id}/jawab/')
        self.assertEqual(response.status_code, 200)

    def test_beranda_student_hanya_lihat_ujian_yang_dienroll(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get('/')
        self.assertContains(response, 'Ujian Tengah Semester')

    def test_dashboard_khusus_instruktur(self):
        self.client.login(username='siswa', password='tes12345')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 302)

        self.client.login(username='admin', password='tes12345')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_dashboard_proses_ulang_penilaian(self):
        from unittest.mock import patch
        from .models import PenilaianAI

        jawaban = JawabanSiswa.objects.create(
            soal=self.soal, siswa=self.siswa, teks_jawaban='jawaban uji')
        penilaian = PenilaianAI.objects.create(jawaban=jawaban)

        self.client.login(username='admin', password='tes12345')
        with patch('lms_app.views.proses_penilaian_ai.delay') as mock_delay:
            response = self.client.post('/dashboard/', {
                'penilaian_id': penilaian.id,
                'aksi': 'proses_ulang',
            })

        self.assertEqual(response.status_code, 302)
        penilaian.refresh_from_db()
        self.assertEqual(penilaian.status, 'PENDING')
        mock_delay.assert_called_once_with(penilaian.id)

    def test_teacher_bisa_akses_dashboard(self):
        self.client.login(username='guru', password='tes12345')
        response = self.client.get('/dashboard/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_hanya_lihat_ujian_dari_kursus_diajar(self):
        self.client.login(username='guru', password='tes12345')
        response = self.client.get('/')
        self.assertContains(response, 'Ujian Tengah Semester')
        self.assertNotContains(response, 'Ujian Fisika')

    def test_teacher_bisa_akses_soal_kursus_diajar(self):
        self.client.login(username='guru', password='tes12345')
        response = self.client.get(f'/soal/{self.soal.id}/jawab/')
        self.assertEqual(response.status_code, 200)

    def test_teacher_ditolak_soal_kursus_bukan_diajar(self):
        self.client.login(username='guru', password='tes12345')
        response = self.client.get(f'/soal/{self.soal_fisika.id}/jawab/')
        self.assertEqual(response.status_code, 403)

    def test_dashboard_teacher_hanya_melihat_penilaian_kursus_diajar(self):
        JawabanSiswa.objects.create(soal=self.soal, siswa=self.siswa, teks_jawaban='jawaban mat')
        PenilaianAI.objects.create(jawaban=JawabanSiswa.objects.get(soal=self.soal, siswa=self.siswa))

        siswa_lain = User.objects.create_user(username='siswa_lain', password='tes12345')
        JawabanSiswa.objects.create(soal=self.soal_fisika, siswa=siswa_lain, teks_jawaban='jawaban fis')
        PenilaianAI.objects.create(jawaban=JawabanSiswa.objects.get(soal=self.soal_fisika, siswa=siswa_lain))

        self.client.login(username='guru', password='tes12345')
        response = self.client.get('/dashboard/')
        self.assertContains(response, 'siswa')
        self.assertNotContains(response, 'siswa_lain')

    def test_teacher_tidak_bisa_proses_ulang_penilaian_kursus_lain(self):
        jawaban = JawabanSiswa.objects.create(
            soal=self.soal_fisika, siswa=self.siswa, teks_jawaban='jawaban fis')
        penilaian = PenilaianAI.objects.create(jawaban=jawaban)

        self.client.login(username='guru', password='tes12345')
        response = self.client.post('/dashboard/', {
            'penilaian_id': penilaian.id,
            'aksi': 'proses_ulang',
        })
        self.assertEqual(response.status_code, 403)
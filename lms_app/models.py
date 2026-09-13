from django.db import models
from django.contrib.auth.models import User

class Ujian(models.Model):
    judul = models.CharField(max_length=255)
    deskripsi = models.TextField(blank=True, null=True)
    waktu_mulai = models.DateTimeField()
    waktu_selesai = models.DateTimeField()
    dibuat_pada = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.judul

class Soal(models.Model):
    ujian = models.ForeignKey(Ujian, on_delete=models.CASCADE, related_name='daftar_soal')
    teks_soal = models.TextField()
    
    # Kunci ini yang akan dibaca oleh model NLP/LLM Anda sebagai perbandingan
    kunci_jawaban = models.TextField(
        help_text="Jawaban ideal untuk acuan AI."
    )
    kriteria_penilaian = models.TextField(
        blank=True, null=True, 
        help_text="Instruksi tambahan untuk AI (misal: 'Harus menyebutkan 3 pilar')."
    )
    skor_maksimal = models.DecimalField(max_digits=5, decimal_places=2, default=100.00)

    def __str__(self):
        return f"Soal: {self.teks_soal[:50]}..."

class JawabanSiswa(models.Model):
    soal = models.ForeignKey(Soal, on_delete=models.CASCADE, related_name='jawaban_siswa')
    siswa = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jawaban')
    teks_jawaban = models.TextField()
    waktu_kumpul = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Mencegah siswa mengirim jawaban berkali-kali untuk soal yang sama
        unique_together = ('soal', 'siswa')

    def __str__(self):
        return f"Jawaban {self.siswa.username} - Soal ID {self.soal.id}"

class PenilaianAI(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Menunggu Antrean'),
        ('PROCESSING', 'Sedang Diproses AI'),
        ('COMPLETED', 'Selesai'),
        ('FAILED', 'Gagal'),
    )
    
    # OneToOneField: Satu jawaban hanya punya satu record penilaian
    jawaban = models.OneToOneField(JawabanSiswa, on_delete=models.CASCADE, related_name='penilaian')
    
    # Skor mentah dari model AI
    skor_ai = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    feedback_ai = models.TextField(null=True, blank=True, help_text="Alasan AI memberikan skor tersebut")
    
    # Skor final yang sudah divalidasi/diubah oleh Anda (Instruktur)
    skor_akhir_instruktur = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    diproses_pada = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Penilaian AI - Jawaban ID {self.jawaban.id} ({self.status})"
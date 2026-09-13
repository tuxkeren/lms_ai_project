from django.contrib import admin
from .models import Ujian, Soal, JawabanSiswa, PenilaianAI

# Fitur Inline: Agar bisa input Soal langsung di halaman pembuatan Ujian
class SoalInline(admin.StackedInline):
    model = Soal
    extra = 1  # Jumlah form kosong soal yang ditampilkan secara default
    fields = ('teks_soal', 'kunci_jawaban', 'kriteria_penilaian', 'skor_maksimal')

@admin.register(Ujian)
class UjianAdmin(admin.ModelAdmin):
    list_display = ('judul', 'waktu_mulai', 'waktu_selesai', 'dibuat_pada')
    search_fields = ('judul',)
    list_filter = ('waktu_mulai',)
    inlines = [SoalInline] # Menyematkan input soal ke dalam form Ujian

@admin.register(Soal)
class SoalAdmin(admin.ModelAdmin):
    list_display = ('id', 'ujian', 'potongan_soal', 'skor_maksimal')
    list_filter = ('ujian',)
    search_fields = ('teks_soal', 'kunci_jawaban')

    # Membuat preview teks soal agar tidak memenuhi tabel
    def potongan_soal(self, obj):
        return obj.teks_soal[:70] + "..." if len(obj.teks_soal) > 70 else obj.teks_soal
    potongan_soal.short_description = 'Teks Soal'

@admin.register(JawabanSiswa)
class JawabanSiswaAdmin(admin.ModelAdmin):
    list_display = ('siswa', 'soal', 'waktu_kumpul')
    list_filter = ('soal__ujian',)
    search_fields = ('siswa__username', 'teks_jawaban')

@admin.register(PenilaianAI)
class PenilaianAIAdmin(admin.ModelAdmin):
    list_display = ('jawaban', 'status', 'skor_ai', 'skor_akhir_instruktur', 'diproses_pada')
    list_filter = ('status',)
    
    # Memudahkan Anda mengedit skor akhir dengan cepat dari halaman list
    list_editable = ('skor_akhir_instruktur',)
    
    # Hanya-baca untuk field yang dikerjakan oleh AI agar tidak terubah manual tanpa sengaja
    readonly_fields = ('jawaban', 'skor_ai', 'feedback_ai', 'status', 'diproses_pada')
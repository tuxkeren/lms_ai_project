from django.contrib import admin
from .models import Ujian, Soal, JawabanSiswa, PenilaianAI, Kursus, Enrollmen, Pengajaran

class EnrollmenInline(admin.TabularInline):
    model = Enrollmen
    extra = 1

class PengajaranInline(admin.TabularInline):
    model = Pengajaran
    extra = 1

@admin.register(Kursus)
class KursusAdmin(admin.ModelAdmin):
    list_display = ('kode', 'nama', 'jumlah_siswa', 'daftar_guru')
    search_fields = ('kode', 'nama')
    inlines = [EnrollmenInline, PengajaranInline]

    def jumlah_siswa(self, obj):
        return obj.daftar_enrollmen.count()
    jumlah_siswa.short_description = 'Jumlah Siswa'

    def daftar_guru(self, obj):
        return ", ".join(p.guru.username for p in obj.daftar_pengajaran.all())
    daftar_guru.short_description = 'Pengajar'

@admin.register(Pengajaran)
class PengajaranAdmin(admin.ModelAdmin):
    list_display = ('guru', 'kursus', 'tanggal_penugasan')
    list_filter = ('kursus',)
    search_fields = ('guru__username', 'kursus__nama')

class SoalInline(admin.StackedInline):
    model = Soal
    extra = 1  # Jumlah form kosong soal yang ditampilkan secara default
    fields = ('teks_soal', 'kunci_jawaban', 'kriteria_penilaian', 'skor_maksimal')

@admin.register(Ujian)
class UjianAdmin(admin.ModelAdmin):
    list_display = ('judul', 'kursus', 'waktu_mulai', 'waktu_selesai', 'dibuat_pada')
    list_filter = ('kursus', 'waktu_mulai')
    search_fields = ('judul',)
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
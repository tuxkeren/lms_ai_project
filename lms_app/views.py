from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Soal, JawabanSiswa, PenilaianAI
from .tasks import proses_penilaian_ai
from django.contrib.auth.decorators import user_passes_test
from .models import PenilaianAI

@login_required(login_url='/admin/login/') # Memastikan hanya user login yang bisa menjawab
def form_jawab_soal(request, soal_id):
    # Ambil data soal berdasarkan ID dari URL
    soal = get_object_or_404(Soal, id=soal_id)

    # Cek apakah siswa sudah pernah menjawab soal ini
    if JawabanSiswa.objects.filter(soal=soal, siswa=request.user).exists():
        return HttpResponse("Anda sudah mengirimkan jawaban untuk soal ini. Sedang menuggu hasil.")

    if request.method == 'POST':
        teks = request.POST.get('teks_jawaban')
        
        if teks:
            # 1. Simpan jawaban siswa ke database
            jawaban_baru = JawabanSiswa.objects.create(
                soal=soal,
                siswa=request.user,
                teks_jawaban=teks
            )
            
            # 2. Buat antrean penilaian awal (Otomatis statusnya 'PENDING')
            penilaian_baru = PenilaianAI.objects.create(jawaban=jawaban_baru)
            
            # =======================================================
            # 3. TRIGGER CELERY TASK! 
            # Gunakan .delay() agar diproses di latar belakang
            # =======================================================
            proses_penilaian_ai.delay(penilaian_baru.id)
            
            # 4. Langsung kembalikan respons ke siswa tanpa menunggu AI selesai
            return HttpResponse("""
                <h2>Berhasil!</h2>
                <p>Jawaban Anda telah tersimpan dan sedang dianalisis oleh AI.</p>
                <a href="/">Kembali</a>
            """)

    # Jika method GET, tampilkan form HTML
    return render(request, 'lms_app/form_jawaban.html', {'soal': soal})


# Pengecekan agar hanya admin/instruktur yang bisa mengakses halaman ini
def is_instructor(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

@user_passes_test(is_instructor, login_url='/admin/login/')
def dashboard_instruktur(request):
    # Jika form dikirim (instruktur mengubah/memvalidasi skor)
    if request.method == 'POST':
        penilaian_id = request.POST.get('penilaian_id')
        skor_baru = request.POST.get('skor_akhir')
        
        penilaian = get_object_or_404(PenilaianAI, id=penilaian_id)
        if skor_baru:
            penilaian.skor_akhir_instruktur = float(skor_baru)
            penilaian.save()
            
        return redirect('dashboard_instruktur')

    # Ambil semua data penilaian beserta relasi ke siswa dan soalnya
    daftar_penilaian = PenilaianAI.objects.select_related(
        'jawaban', 'jawaban__siswa', 'jawaban__soal', 'jawaban__soal__ujian'
    ).order_by('-id')

    context = {
        'daftar_penilaian': daftar_penilaian
    }
    return render(request, 'lms_app/dashboard.html', context)
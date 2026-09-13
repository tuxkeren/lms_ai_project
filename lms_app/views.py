from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponse
from django.utils import timezone
from .models import Ujian, Soal, JawabanSiswa, PenilaianAI
from .tasks import proses_penilaian_ai


def beranda(request):
    sekarang = timezone.now()
    daftar_ujian = []
    for ujian in Ujian.objects.prefetch_related('daftar_soal').order_by('-waktu_mulai'):
        soal_pertama = ujian.daftar_soal.first()
        if sekarang < ujian.waktu_mulai:
            status = 'mendatang'
        elif sekarang > ujian.waktu_selesai:
            status = 'selesai'
        else:
            status = 'aktif'
        daftar_ujian.append({
            'ujian': ujian,
            'status': status,
            'soal_pertama': soal_pertama,
        })
    context = {
        'daftar_ujian': daftar_ujian,
        'waktu_sekarang': sekarang,
    }
    return render(request, 'lms_app/beranda.html', context)


@login_required(login_url='/admin/login/')
def form_jawab_soal(request, soal_id):
    soal = get_object_or_404(Soal, id=soal_id)
    sekarang = timezone.now()

    if sekarang < soal.ujian.waktu_mulai:
        return render(request, 'lms_app/info_ujian.html', {
            'judul': 'Ujian Belum Dimulai',
            'pesan': 'Ujian belum dibuka. Silakan tunggu sampai waktu mulai tiba.',
        })
    if sekarang > soal.ujian.waktu_selesai:
        return render(request, 'lms_app/info_ujian.html', {
            'judul': 'Ujian Telah Berakhir',
            'pesan': 'Waktu ujian sudah habis. Jawaban tidak dapat dikirim lagi.',
        })

    if JawabanSiswa.objects.filter(soal=soal, siswa=request.user).exists():
        return render(request, 'lms_app/info_ujian.html', {
            'judul': 'Jawaban Telah Terkirim',
            'pesan': 'Anda sudah mengirimkan jawaban untuk soal ini. Sedang menunggu hasil.',
        })

    if request.method == 'POST':
        teks = request.POST.get('teks_jawaban')
        if teks:
            jawaban_baru = JawabanSiswa.objects.create(
                soal=soal,
                siswa=request.user,
                teks_jawaban=teks
            )
            penilaian_baru = PenilaianAI.objects.create(jawaban=jawaban_baru)
            try:
                proses_penilaian_ai.delay(penilaian_baru.id)
            except Exception:
                penilaian_baru.status = 'FAILED'
                penilaian_baru.feedback_ai = 'Worker tidak tersedia. Coba beri nilai ulang saat worker aktif.'
                penilaian_baru.save()
            return render(request, 'lms_app/info_ujian.html', {
                'judul': 'Berhasil!',
                'pesan': 'Jawaban Anda telah tersimpan dan sedang dianalisis oleh AI.',
            })

    return render(request, 'lms_app/form_jawaban.html', {'soal': soal})


def is_instructor(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(is_instructor, login_url='/admin/login/')
def dashboard_instruktur(request):
    if request.method == 'POST':
        penilaian_id = request.POST.get('penilaian_id')
        skor_mentah = request.POST.get('skor_akhir')

        penilaian = get_object_or_404(PenilaianAI, id=penilaian_id)
        if skor_mentah is not None and skor_mentah != '':
            skor_batas = penilaian.jawaban.soal.skor_maksimal
            try:
                skor_baru = float(skor_mentah)
                if skor_baru < 0:
                    skor_baru = 0
                if skor_baru > float(skor_batas):
                    skor_baru = float(skor_batas)
            except ValueError:
                return HttpResponse("Skor harus berupa angka.", status=400)
            penilaian.skor_akhir_instruktur = round(skor_baru, 2)
            penilaian.save()

        return redirect('dashboard_instruktur')

    daftar_penilaian = PenilaianAI.objects.select_related(
        'jawaban', 'jawaban__siswa', 'jawaban__soal', 'jawaban__soal__ujian'
    ).order_by('-id')

    context = {
        'daftar_penilaian': daftar_penilaian,
    }
    return render(request, 'lms_app/dashboard.html', context)
from celery import shared_task
from django.utils import timezone
from lms_app.models import PenilaianAI
from ai_grader.engine import get_embedding, hitung_cosine_similarity
from ai_grader.engine import ModelTidakTersedia

@shared_task
def proses_penilaian_ai(penilaian_id):
    try:
        penilaian = PenilaianAI.objects.get(id=penilaian_id)
        penilaian.status = 'PROCESSING'
        penilaian.save()

        teks_jawaban = penilaian.jawaban.teks_jawaban
        kunci_jawaban = penilaian.jawaban.soal.kunci_jawaban

        vektor_kunci = get_embedding(kunci_jawaban)
        vektor_siswa = get_embedding(teks_jawaban)
        kemiripan = hitung_cosine_similarity(vektor_kunci, vektor_siswa)

        skor_final = max(0.0, min(100.0, float(kemiripan) * 100))

        penilaian.skor_ai = round(skor_final, 2)
        penilaian.feedback_ai = "Dinilai menggunakan AI Engine ONNX."
        penilaian.status = 'COMPLETED'
        penilaian.diproses_pada = timezone.now()
        penilaian.save()

        return f"Sukses: Skor {penilaian.skor_ai}"

    except PenilaianAI.DoesNotExist:
        return f"Gagal: Data Penilaian {penilaian_id} tidak ditemukan."
    except ModelTidakTersedia as e:
        if 'penilaian' in locals():
            penilaian.status = 'FAILED'
            penilaian.feedback_ai = str(e)
            penilaian.save()
        return f"Gagal: {e}"
    except Exception as e:
        if 'penilaian' in locals():
            penilaian.status = 'FAILED'
            penilaian.feedback_ai = f"Error: {str(e)}"
            penilaian.save()
        return f"Error: {str(e)}"
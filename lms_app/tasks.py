# from celery import shared_task
# from django.utils import timezone
# import time
# from .models import PenilaianAI

# # ---- SIMULASI DENGAN CELERY TANPA AI ----

# @shared_task
# def proses_penilaian_ai(penilaian_id):
#     """
#     Fungsi ini akan dijalankan di latar belakang oleh Celery Worker.
#     Tidak akan mengganggu loading halaman browser siswa.
#     """
#     try:
#         # 1. Ambil data dari tabel PenilaianAI
#         penilaian = PenilaianAI.objects.get(id=penilaian_id)
        
#         # 2. Ubah status untuk memberi tahu sistem bahwa AI sedang bekerja
#         penilaian.status = 'PROCESSING'
#         penilaian.save()

#         # 3. Ambil data teks yang akan dinilai
#         teks_jawaban = penilaian.jawaban.teks_jawaban
#         kunci_jawaban = penilaian.jawaban.soal.kunci_jawaban
#         kriteria = penilaian.jawaban.soal.kriteria_penilaian

#         # ========================================================
#         # 4. AREA SIMULASI AI
#         # Nanti, di sinilah Anda memasukkan fungsi dari model
#         # HuggingFace, ONNX, atau API pihak ketiga.
#         # ========================================================
#         print(f"Memulai analisis jawaban ID: {penilaian.jawaban.id}...")
        
#         # Menyimulasikan waktu tunggu (delay) komputasi AI selama 8 detik
#         time.sleep(8) 
        
#         # Simulasi hasil prediksi dari AI
#         skor_prediksi = 85.50
#         feedback = "Analisis AI: Siswa telah menjelaskan konsep dengan baik dan mendekati kunci jawaban. Namun, penjelasan mengenai konteks aplikasinya masih kurang mendalam."
#         # ========================================================

#         # 5. Simpan hasil penilaian AI kembali ke database
#         penilaian.skor_ai = skor_prediksi
#         penilaian.feedback_ai = feedback
#         penilaian.status = 'COMPLETED'
#         penilaian.diproses_pada = timezone.now()
#         penilaian.save()

#         return f"Sukses: Jawaban {penilaian.jawaban.id} berhasil dinilai."

#     except PenilaianAI.DoesNotExist:
#         return f"Gagal: Data Penilaian dengan ID {penilaian_id} tidak ditemukan."
    
#     except Exception as e:
#         # Jika terjadi error (misalnya memori VPS penuh / model AI crash)
#         if 'penilaian' in locals():
#             penilaian.status = 'FAILED'
#             penilaian.feedback_ai = f"Sistem Error: {str(e)}"
#             penilaian.save()
#         return f"Error sistem pada Penilaian ID {penilaian_id}: {str(e)}"

# ---- AKHIR SIMULASI ----

# ---- LANGSUNG DIHANDLE AI ----
# ====================================================================
# INISIALISASI MODEL AI (Di-load ke RAM sekali saat Celery dijalankan)
# ====================================================================
# from sentence_transformers import SentenceTransformer, util

# print("Memuat Model NLP ke memori... (Ini mungkin memakan waktu saat pertama kali)")
# # Menggunakan model ringan yang sangat baik untuk bahasa Indonesia
# model_ai = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
# # ====================================================================


# @shared_task
# def proses_penilaian_ai(penilaian_id):
#     try:
#         penilaian = PenilaianAI.objects.get(id=penilaian_id)
#         penilaian.status = 'PROCESSING'
#         penilaian.save()

#         teks_jawaban = penilaian.jawaban.teks_jawaban
#         kunci_jawaban = penilaian.jawaban.soal.kunci_jawaban

#         print(f"Menganalisis jawaban ID: {penilaian.jawaban.id} dengan AI...")

#         # ========================================================
#         # PROSES INTI AI: MENGHITUNG KESAMAAN SEMANTIK
#         # ========================================================
        
#         # 1. Ubah teks menjadi vektor dimensi tinggi (Embeddings)
#         vektor_kunci = model_ai.encode(kunci_jawaban, convert_to_tensor=True)
#         vektor_siswa = model_ai.encode(teks_jawaban, convert_to_tensor=True)

#         # 2. Hitung kemiripan (Cosine Similarity) hasilnya antara -1.0 hingga 1.0
#         kemiripan = util.cos_sim(vektor_kunci, vektor_siswa).item()

#         # 3. Konversi nilai kemiripan menjadi skor 0 - 100
#         # Kadang kemiripan bisa negatif kecil jika sangat berlawanan, kita batasi di 0
#         skor_mentah = kemiripan * 100
#         skor_final = max(0.0, min(100.0, skor_mentah)) # Memastikan skor antara 0-100
        
#         # 4. Buat feedback otomatis berdasarkan range skor
#         if skor_final >= 85:
#             feedback = "Sangat Baik: Jawaban memiliki pemahaman konsep yang sangat relevan dengan kunci jawaban."
#         elif skor_final >= 60:
#             feedback = "Cukup: Jawaban menangkap sebagian ide pokok, namun ada detail krusial yang terlewat atau kurang tepat."
#         else:
#             feedback = "Kurang: Konsep yang dijelaskan melenceng jauh dari substansi kunci jawaban."
#         # ========================================================

#         penilaian.skor_ai = round(skor_final, 2)
#         penilaian.feedback_ai = feedback
#         penilaian.status = 'COMPLETED'
#         penilaian.diproses_pada = timezone.now()
#         penilaian.save()

#         return f"Sukses: Skor {penilaian.skor_ai} untuk Jawaban {penilaian.jawaban.id}"

#     except PenilaianAI.DoesNotExist:
#         return f"Gagal: Data Penilaian {penilaian_id} tidak ditemukan."
#     except Exception as e:fgfgf oookko
#         if 'penilaian' in locals():
#             penilaian.status = 'FAILED'
#             penilaian.feedback_ai = f"Error AI: {str(e)}"
#             penilaian.save()
#         return f"Error pada Penilaian {penilaian_id}: {str(e)}"

# -----live AI ONNX -----
from celery import shared_task
from django.utils import timezone
from lms_app.models import PenilaianAI
from ai_grader.engine import get_embedding, hitung_cosine_similarity
import re

@shared_task
def proses_penilaian_ai(penilaian_id):
    try:
        penilaian = PenilaianAI.objects.get(id=penilaian_id)
        penilaian.status = 'PROCESSING'
        penilaian.save()

        teks_jawaban = penilaian.jawaban.teks_jawaban
        kunci_jawaban = penilaian.jawaban.soal.kunci_jawaban

        # Panggil engine AI yang rapi di folder ai_grader
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

    except Exception as e:
        if 'penilaian' in locals():
            penilaian.status = 'FAILED'
            penilaian.feedback_ai = f"Error: {str(e)}"
            penilaian.save()
        return f"Error: {str(e)}"
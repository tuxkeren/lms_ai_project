from django.urls import path
from . import views

urlpatterns = [
    path('', views.beranda, name='beranda'),
    path('logout/', views.keluar, name='logout'),
    path('soal/<int:soal_id>/jawab/', views.form_jawab_soal, name='jawab_soal'),
    path('dashboard/', views.dashboard_instruktur, name='dashboard_instruktur'),
]
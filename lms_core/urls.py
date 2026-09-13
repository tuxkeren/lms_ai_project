from django.contrib import admin
from django.urls import path, include # Pastikan include diimpor

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('lms_app.urls')), # Menyambungkan route lms_app
]
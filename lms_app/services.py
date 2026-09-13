from django.contrib.auth.models import Group
from .models import Enrollmen

NAMA_GROUP_STUDENT = 'Student'


def group_student():
    return Group.objects.get_or_create(name=NAMA_GROUP_STUDENT)[0]


def is_student(user):
    return user.is_authenticated and group_student().user_set.filter(id=user.id).exists()


def terdaftar_di_kursus(siswa, kursus):
    if kursus is None:
        return False
    return Enrollmen.objects.filter(siswa=siswa, kursus=kursus).exists()
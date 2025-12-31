from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("clinica/", include("clinica.urls")),   
    path("agendamentos/", include("agendamentos.urls")),
]

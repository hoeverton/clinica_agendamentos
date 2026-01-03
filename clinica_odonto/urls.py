from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("clinica/", include("clinica.urls")),   
    path("agendamentos/", include("agendamentos.urls")),
    path("accounts/", include("django.contrib.auth.urls")),

]

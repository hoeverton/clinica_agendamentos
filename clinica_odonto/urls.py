from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import home, demo, cadastro

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home),
    path('demo/', demo, name='demo'),
    path('cadastro/',cadastro, name='cadastro'),
    path("clinica/", include("clinica.urls")),   
    path("agendamentos/", include("agendamentos.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("paciente/", include("pacientes.urls")),    
    path('api/', include('whatsapp.urls')),
    path("whatsapp/", include("whatsapp.urls")),

]

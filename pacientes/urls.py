from django.urls import path
from . import views

urlpatterns = [
    path("login/", views.solicitar_codigo, name="solicitar_codigo"),
    path("login/codigo/", views.validar_codigo, name="validar_codigo"),
    path("dashboard/", views.dashboard_paciente, name="dashboard_paciente"),
]
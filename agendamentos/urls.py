from django.urls import path
from . import views


urlpatterns = [
    path("<slug:clinica_slug>/", views.clinica_home, name="clinica_home"),
    path("<slug:clinica_slug>/telefone/", views.passo1_telefone, name="passo1_telefone"),
    path("<slug:clinica_slug>/servico/", views.passo2_servico, name="passo2_servico"),
    path("<slug:clinica_slug>/profissional/", views.passo3_profissional, name="passo3_profissional"),
    path("<slug:clinica_slug>/data-horario/", views.passo4_data_horario, name="passo4_data_horario"),
    path("<slug:clinica_slug>/confirmar/", views.confirmar, name="confirmar"),
    path("<slug:clinica_slug>/sucesso/", views.sucesso, name="sucesso"),
    #path('clinica/<slug:slug>/dashboard/', views.ClinicaDashboardView.as_view(), name='clinica_dashboard'),
    #path("clinica/dashboard/", views.ClinicaDashboardView.as_view(), name="clinica_dashboard"),
    
]

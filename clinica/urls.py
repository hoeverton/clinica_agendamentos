from django.urls import path
from .views import ClinicaLoginView, clinica_logout, disponibilidade_create, disponibilidade_list, disponibilidade_delete, disponibilidade_edit, agendamento_delete, agendamento_edit
from clinica.views import ClinicaDashboardView, relatorio_agendamentos_csv, relatorio_agendamentos_pdf

urlpatterns = [
    path("login/", ClinicaLoginView.as_view(), name="clinica_login"),
    path("dashboard/", ClinicaDashboardView.as_view(), name="clinica_dashboard"),
    path("logout/", clinica_logout, name="clinica_logout"),
    #path("disponibilidade/", DisponibilidadeCreateView.as_view(), name="disponibilidade_create"),
    path("disponibilidade/", disponibilidade_create, name="disponibilidade_create"),
    path("disponibilidades/", disponibilidade_list, name="disponibilidade_list"),
    #path("disponibilidade/excluir/<int:pk>/", disponibilidade_delete, name="disponibilidade_delete"),
    path("disponibilidade/<int:pk>/excluir/", disponibilidade_delete, name="disponibilidade_delete"),
    path("disponibilidade/<int:pk>/editar/", disponibilidade_edit, name="disponibilidade_edit"),
    path("agendamento/<int:pk>/editar/", agendamento_edit, name="agendamento_edit"),    
    path("agendamento/<int:pk>/excluir/", agendamento_delete,name="agendamento_delete"),
    path("relatorios/agendamentos/csv/",relatorio_agendamentos_csv,name="relatorio_agendamentos_csv"),
    path("relatorios/agendamentos/pdf/",relatorio_agendamentos_pdf,name="relatorio_agendamentos_pdf"),
    
]

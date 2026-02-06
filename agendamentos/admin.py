from django.contrib import admin
from .models import Clinica, Profissional, Servico, Paciente, Agendamento, Prontuario, UsuarioClinica
from .models import WhatsappLog

@admin.register(Clinica)
class ClinicaAdmin(admin.ModelAdmin):
    pass

@admin.register(Profissional)
class ProfissionalAdmin(admin.ModelAdmin):
    pass

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    pass

@admin.register(Paciente)
class PacienteAdmin(admin.ModelAdmin):
    pass

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    pass

@admin.register(Prontuario)
class ProntuarioAdmin(admin.ModelAdmin):
    pass

@admin.register(WhatsappLog)
class WhatsappLogAdmin(admin.ModelAdmin):
    list_display = ("clinica", "telefone", "tipo", "data")
    list_filter = ("tipo", "clinica")
    search_fields = ("telefone",)


admin.site.register(UsuarioClinica)

from django.db import models

class Plano(models.Model):
    nome = models.CharField(max_length=50)

    # permissões do sistema
    pode_ver_paciente = models.BooleanField(default=True)
    pode_usar_prontuario = models.BooleanField(default=False)
    tem_relatorios = models.BooleanField(default=False)
    

    # limites
    max_profissionais = models.IntegerField(null=True, blank=True)
    max_agendamentos_mes = models.IntegerField(null=True, blank=True)
    max_servicos = models.IntegerField(null=True, blank=True)

    # whatsapp (opcional)
    max_whatsapp_mes = models.IntegerField(null=True, blank=True)

    preco = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nome



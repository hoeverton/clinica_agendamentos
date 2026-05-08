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

class Assinatura(models.Model):
    STATUS_CHOICES = (
        ('pendente', 'Pendente'),
        ('ativo', 'Ativo'),
        ('cancelado', 'Cancelado'),
    )

    clinica = models.ForeignKey(
    'agendamentos.Clinica',
    on_delete=models.CASCADE
)

    plano = models.ForeignKey(
    'clinica.Plano',
    on_delete=models.CASCADE
)

    valor = models.DecimalField(
        max_digits=8,
        decimal_places=2
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )

    codigo_pix = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f'{self.clinica} - {self.plano.nome}'

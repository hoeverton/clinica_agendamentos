from django.db import models

class Plano(models.Model):
    nome = models.CharField(max_length=50)

    # 🔐 Permissões
    pode_ver_paciente = models.BooleanField(default=True)
    pode_usar_prontuario = models.BooleanField(default=False)

    # 🔢 Limites do plano
    max_profissionais = models.IntegerField(null=True, blank=True)
    max_servicos = models.IntegerField(null=True, blank=True)
    max_agendamentos_mes = models.IntegerField(null=True, blank=True)

    # 📲 WhatsApp
    max_whatsapp_mes = models.IntegerField(
        null=True,
        blank=True,
        help_text="Quantidade de mensagens WhatsApp incluídas no plano (null = ilimitado)"
    )

    preco = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return self.nome



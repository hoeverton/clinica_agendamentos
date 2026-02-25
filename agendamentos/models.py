from django.db import models
from django.contrib.auth.models import User
from django.utils.text import slugify
from clinica.models import Plano
from django.utils import timezone



class Clinica(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    nome = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    endereco = models.CharField(max_length=200, blank=True, null=True)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp_extra = models.IntegerField(default=0)


    #Permissões
    class Meta:
        permissions = [
            ("ver_dashboard", "Pode ver o dashboard"),
            ("gerenciar_agendamentos", "Pode gerenciar agendamentos"),
            ("gerenciar_servicos", "Pode gerenciar serviços"),
            ("gerenciar_profissionais", "Pode gerenciar profissionais"),
            ("ver_relatorios", "Pode ver relatórios"),
        ]
    # 🔑 NOVO CAMPO
    plano = models.ForeignKey(
        Plano,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.nome)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nome

    

class Profissional(models.Model):
    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name="profissionais"
    )
    nome = models.CharField(max_length=100)
    especialidade = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    servicos = models.ManyToManyField(
        'Servico',
        related_name='profissionais',
        blank=True
    )

    def __str__(self):
        return self.nome
    

class Servico(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE, related_name="servicos")
    nome = models.CharField(max_length=100)
    duracao_minutos = models.PositiveIntegerField(default=30)
    preco = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return self.nome


class Paciente(models.Model):
    nome = models.CharField(max_length=100, blank=True, null=True)
    telefone = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nome if self.nome else self.telefone


class Agendamento(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)
    servico = models.ForeignKey(Servico, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)

    data = models.DateField()
    horario = models.TimeField()

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("profissional", "data", "horario")

    def __str__(self):
        nome = self.paciente.nome if self.paciente.nome else self.paciente.telefone
        return f"{self.data} - {self.horario} - {nome}"

class Disponibilidade(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    profissional = models.ForeignKey(Profissional, on_delete=models.CASCADE)

    DIA_SEMANA = [
        (0, "Segunda"),
        (1, "Terça"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    dia_semana = models.IntegerField(choices=DIA_SEMANA)
    hora_inicio = models.TimeField()
    hora_fim = models.TimeField()

    def __str__(self):
        return f"{self.profissional} - {self.get_dia_semana_display()}"


    def __str__(self):
        return f"{self.profissional} - {self.get_dia_semana_display()} ({self.hora_inicio} às {self.hora_fim})"

class Prontuario(models.Model):
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE)
    profissional = models.ForeignKey(
        Profissional,
        on_delete=models.SET_NULL,
        null=True
    )

    agendamento = models.OneToOneField(
        Agendamento,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="prontuario"
    )

    data = models.DateTimeField(auto_now_add=True)
    anotacoes = models.TextField(blank=True)

    class Meta:
        ordering = ['-data']

class WhatsappLog(models.Model):

    TIPO_CHOICES = (
        ("confirmacao", "Confirmação"),
        ("lembrete", "Lembrete"),
        ("cancelamento", "Cancelamento"),
    )

    clinica = models.ForeignKey(
        Clinica,
        on_delete=models.CASCADE,
        related_name="whatsapp_logs"
    )

    telefone = models.CharField(max_length=20)

    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES
    )

    data = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.clinica.nome} - {self.telefone} - {self.tipo}"
    


class UsuarioClinica(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    clinica = models.ForeignKey(Clinica, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.user.username} - {self.clinica.nome}"
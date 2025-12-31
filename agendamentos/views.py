from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Paciente, Servico, Profissional, Clinica, Agendamento, Disponibilidade
from agendamentos.utils import (pode_enviar_whatsapp,registrar_envio_whatsapp, enviar_whatsapp)
from django.views.generic import TemplateView
from agendamentos.models import WhatsappLog
from datetime import datetime, timedelta
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.utils import timezone

"""class ClinicaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "clinica/dashboard.html"
    login_url = "/clinica/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 🔒 BUSCA APENAS CLÍNICAS DO USUÁRIO
        clinicas_do_usuario = Clinica.objects.filter(user=self.request.user)

        # 🔥 BUSCA AGENDAMENTOS APENAS DESSAS CLÍNICAS
        agendamentos = Agendamento.objects.filter(
            clinica__in=clinicas_do_usuario
        ).select_related(
            "clinica",
            "profissional",
            "paciente",
            "servico"
        ).order_by("data", "horario")

        # ⚠️ Se quiser exibir só UMA clínica (ex: primeira)
        clinica = clinicas_do_usuario.first()

        agora = timezone.now()

        whatsapp_usados = WhatsappLog.objects.filter(
            clinica__in=clinicas_do_usuario,
            data__month=agora.month,
            data__year=agora.year
        ).count()

        context.update({
            "clinica": clinica,
            "agendamentos": agendamentos,
            "today": agora.date(),
            "whatsapp_usados": whatsapp_usados,
        })

        return context

"""
# PASSO 1 - TELEFONE
def passo1_telefone(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)

    if request.method == "POST":
        nome =request.POST.get("nome_paciente")
        telefone = request.POST.get("telefone")

        if not telefone:
            messages.error(request, "Informe o telefone do paciente")
            return redirect("passo_telefone",clinica_slug=clinica_slug)

        paciente, created = Paciente.objects.get_or_create(telefone=telefone)

        if nome:
            paciente.nome = nome
            paciente.save()
        request.session["paciente_id"] = paciente.id
        return redirect("passo2_servico", clinica_slug=clinica_slug)

    return render(request, "agendamentos/passo1_telefone.html", {"clinica": clinica})


# PASSO 2 - ESCOLHER SERVIÇO
def passo2_servico(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)
    servicos = Servico.objects.filter(clinica=clinica)

    if request.method == "POST":
        request.session["servico_id"] = request.POST.get("servico_id")
        return redirect("passo3_profissional", clinica_slug=clinica_slug)

    return render(request, "agendamentos/passo2_servico.html", {
        "clinica": clinica,
        "servicos": servicos
    })


# PASSO 3 - ESCOLHER PROFISSIONAL
def passo3_profissional(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)
    profissionais = Profissional.objects.filter(clinica=clinica)

    if request.method == "POST":
        request.session["profissional_id"] = request.POST.get("profissional_id")
        return redirect("passo4_data_horario", clinica_slug=clinica_slug)

    return render(request, "agendamentos/passo3_profissional.html", {
        "clinica": clinica,
        "profissionais": profissionais
    })


# PASSO 4 - ESCOLHER DATA E HORÁRIO
def passo4_data_horario(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)

    profissional_id = request.session.get("profissional_id")
    profissional = Profissional.objects.get(id=profissional_id)

    servico = Servico.objects.get(id=request.session["servico_id"])
    duracao = servico.duracao_minutos  # 🔑 duração do serviço

    horarios_disponiveis = []
    data = None

    # =========================
    # GET → escolher a data
    # =========================
    if request.method == "GET":
        data = request.GET.get("data")

        if data:
            dia_semana = datetime.strptime(data, "%Y-%m-%d").weekday()

            disponibilidades = Disponibilidade.objects.filter(
                clinica=clinica,
                profissional=profissional,
                dia_semana=dia_semana
            )

            # agendamentos já existentes no dia
            agendamentos = Agendamento.objects.filter(
                profissional=profissional,
                data=data
            )

            for d in disponibilidades:
                # último horário possível considerando a duração
                hora_limite = (
                    datetime.combine(datetime.today(), d.hora_fim)
                    - timedelta(minutes=duracao)
                ).time()

                hora = d.hora_inicio

                while hora <= hora_limite:
                    inicio = datetime.combine(datetime.today(), hora)
                    fim = inicio + timedelta(minutes=duracao)

                    conflito = False
                    for ag in agendamentos:
                        ag_inicio = datetime.combine(datetime.today(), ag.horario)
                        ag_fim = ag_inicio + timedelta(minutes=ag.servico.duracao_minutos)

                        # verifica sobreposição
                        if inicio < ag_fim and fim > ag_inicio:
                            conflito = True
                            break

                    if not conflito:
                        horarios_disponiveis.append(hora)

                    # passo base (30 min)
                    hora = (inicio + timedelta(minutes=30)).time()

    # =========================
    # POST → confirmar horário
    # =========================
    elif request.method == "POST":
        data = request.POST.get("data")
        horario = request.POST.get("horario")

        if not data or not horario:
            return redirect("passo4_data_horario", clinica_slug=clinica_slug)

        request.session["data"] = data
        request.session["horario"] = horario
        return redirect("confirmar", clinica_slug=clinica_slug)

    return render(request, "agendamentos/passo4_data_horario.html", {
        "clinica": clinica,
        "data": data,
        "horarios": horarios_disponiveis
    })
    

# CONFIRMAR AGENDAMENTO
def confirmar(request, clinica_slug):
    clinica = get_object_or_404(Clinica, slug=clinica_slug)

    # 🔹 Dados vindos da sessão
    paciente = get_object_or_404(
        Paciente,
        id=request.session.get("paciente_id")
    )
    servico = get_object_or_404(
        Servico,
        id=request.session.get("servico_id")
    )
    profissional = get_object_or_404(
        Profissional,
        id=request.session.get("profissional_id")
    )

    data = request.session.get("data")       # string
    horario = request.session.get("horario") # string

    # 🔒 Segurança extra
    if not all([paciente, servico, profissional, data, horario]):
        messages.error(
            request,
            "Sessão expirada. Por favor, refaça o agendamento."
        )
        return redirect("passo1_telefone", clinica_slug=clinica.slug)

    if request.method == "POST":

        # 🔥 Converte string → date / time
        try:
            data = datetime.strptime(data, "%Y-%m-%d").date()
            horario = datetime.strptime(horario, "%H:%M").time()
        except ValueError:
            messages.error(request, "Data ou horário inválido.")
            return redirect("passo4_data_horario", clinica_slug=clinica.slug)

        # 🔒 1️⃣ Verifica conflito antes de criar
        conflito = Agendamento.objects.filter(
            profissional=profissional,
            data=data,
            horario=horario
        ).exists()

        if conflito:
            messages.error(
                request,
                "❌ Este horário acabou de ser ocupado. Por favor, escolha outro."
            )
            return redirect("passo4_data_horario", clinica_slug=clinica.slug)

        # 🔒 2️⃣ Cria o agendamento (blindagem extra)
        try:
            agendamento = Agendamento.objects.create(
                paciente=paciente,
                servico=servico,
                profissional=profissional,
                clinica=clinica,
                data=data,
                horario=horario,
            )
        except IntegrityError:
            messages.error(
                request,
                "❌ Este horário acabou de ser ocupado. Por favor, escolha outro."
            )
            return redirect("passo4_data_horario", clinica_slug=clinica.slug)

        # 📲 3️⃣ WhatsApp de confirmação
        if pode_enviar_whatsapp(clinica):
            mensagem = (
                f"Olá {paciente.nome} 👋\n\n"
                f"Seu agendamento foi confirmado!\n\n"
                f"📅 Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                f"⏰ Horário: {agendamento.horario.strftime('%H:%M')}\n"
                f"👨‍⚕️ Profissional: {agendamento.profissional}\n"
                f"🦷 Serviço: {agendamento.servico}\n\n"
                f"Até breve!"
            )

            enviado = enviar_whatsapp(
                paciente.telefone,
                mensagem
            )

            if enviado:
                registrar_envio_whatsapp(
                    clinica=clinica,
                    telefone=paciente.telefone,
                    tipo="confirmacao"
                )
        else:
            messages.warning(
                request,
                "Agendamento confirmado, mas o limite de WhatsApp do seu plano foi atingido."
            )

        # 🧹 4️⃣ Limpa sessão
        request.session.pop("data", None)
        request.session.pop("horario", None)
        request.session.pop("paciente_id", None)
        request.session.pop("servico_id", None)
        request.session.pop("profissional_id", None)

        return redirect("sucesso", clinica_slug=clinica.slug)

    # 🔹 GET (exibe tela de confirmação)
    return render(request, "agendamentos/confirmar.html", {
        "clinica": clinica,
        "paciente": paciente,
        "servico": servico,
        "profissional": profissional,
        "data": data,
        "horario": horario,
    })

def sucesso(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)
    return render(request, "agendamentos/sucesso.html", {"clinica": clinica})




def clinica_home(request, clinica_slug):
    clinica = Clinica.objects.get(slug=clinica_slug)
    return render(request, "agendamentos/clinica_home.html", {"clinica": clinica})


def agendamento_edit(request, pk):
    agendamento = get_object_or_404(Agendamento, pk=pk)

    hoje = timezone.now().date()

    if agendamento.data < hoje:
        messages.error(
            request,
            "❌ Não é possível editar um agendamento já realizado."
        )
        return redirect("clinica_dashboard")

    horarios_disponiveis = []

    if request.method == "POST":
        data = request.POST.get("data")
        horario = request.POST.get("horario")

        if not data or not horario:
            messages.error(request, "Preencha todos os campos.")
            return redirect("agendamento_edit", pk=pk)

        agendamento.data = data
        agendamento.horario = horario
        agendamento.save()

        messages.success(
            request,
            "✅ Agendamento atualizado com sucesso."
        )
        return redirect("clinica_dashboard")

    return render(request, "agendamentos/agendamento_edit.html", {
        "agendamento": agendamento,
        "horarios": horarios_disponiveis
    })
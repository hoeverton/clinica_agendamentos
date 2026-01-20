import csv
from weasyprint import HTML
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from agendamentos.models import Clinica, Agendamento, Disponibilidade, Profissional, Plano
from agendamentos.models import WhatsappLog, Agendamento
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from .forms import ProfissionalForm, ServicoForm
from agendamentos.utils import (
    pode_enviar_whatsapp,
    enviar_whatsapp,
    registrar_envio_whatsapp
)



class ClinicaLoginView(View):
    template_name = "clinica/login.html"

    def get(self, request):
        return render(request, self.template_name)

    def post(self, request):
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect("clinica_dashboard")

        return render(request, self.template_name, {"error": "Credenciais inválidas"})

class ClinicaDashboardView(LoginRequiredMixin, TemplateView):
    template_name = "clinica/dashboard.html"
    login_url = "/clinica/login/"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 1️⃣ Clínicas do usuário
        clinicas_do_usuario = Clinica.objects.filter(user=self.request.user)

        # 2️⃣ Clínica ativa
        clinica = clinicas_do_usuario.first()

        # 3️⃣ Plano
        plano = clinica.plano if clinica else None

        # 4️⃣ Datas
        agora = timezone.now()
        hoje = agora.date()
        amanha = hoje + timedelta(days=1)

        # 5️⃣ WhatsApp usados no mês
        whatsapp_usados = WhatsappLog.objects.filter(
            clinica__in=clinicas_do_usuario,
            data__month=agora.month,
            data__year=agora.year
        ).count()

        # 6️⃣ Limite WhatsApp
        if plano and plano.max_whatsapp_mes is None:
            whatsapp_limite = None
        elif plano:
            whatsapp_limite = plano.max_whatsapp_mes + clinica.whatsapp_extra
        else:
            whatsapp_limite = 0

        # 7️⃣ TODOS os agendamentos
        agendamentos = Agendamento.objects.filter(
            clinica__in=clinicas_do_usuario
        ).select_related(
            "clinica",
            "profissional",
            "paciente",
            "servico"
        ).order_by("data", "horario")

        # 8️⃣ Regra única de edição (APLICA PARA TODOS)
        for a in agendamentos:
            a.pode_editar = a.data >= hoje

        # 9️⃣ Sublistas (herdam a regra acima)
        agendamentos_hoje = [a for a in agendamentos if a.data == hoje]
        agendamentos_amanha = [a for a in agendamentos if a.data == amanha]

        # 🔟 Contexto
        context.update({
            "clinica": clinica,
            "agendamentos": agendamentos,
            "agendamentos_hoje": agendamentos_hoje,
            "agendamentos_amanha": agendamentos_amanha,
            "today": hoje,
            "whatsapp_usados": whatsapp_usados,
            "whatsapp_limite": whatsapp_limite,
        })

        return context




def clinica_logout(request):
    logout(request)
    return redirect("clinica_login")

@login_required
def disponibilidade_create(request):
    clinica = Clinica.objects.get(user=request.user)
    profissionais = Profissional.objects.filter(clinica=clinica)

    dias_semana = [
        (0, "Segunda"),
        (1, "Terça"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    if request.method == "POST":
        profissional_id = request.POST.get("profissional")
        dias = request.POST.getlist("dias_semana")
        hora_inicio = request.POST.get("hora_inicio")
        hora_fim = request.POST.get("hora_fim")

        # 🔴 VALIDAÇÕES BÁSICAS
        if not profissional_id or not dias or not hora_inicio or not hora_fim:
            messages.error(
                request,
                "❌ Preencha todos os campos para cadastrar a disponibilidade."
            )
            return redirect("disponibilidade_create")

        profissional = Profissional.objects.get(id=profissional_id, clinica=clinica)

        criados = 0
        ignorados = 0

        for dia in dias:
            # 🔒 EVITA DUPLICAR DISPONIBILIDADE
            existe = Disponibilidade.objects.filter(
                clinica=clinica,
                profissional=profissional,
                dia_semana=int(dia),
                hora_inicio=hora_inicio,
                hora_fim=hora_fim
            ).exists()

            if existe:
                ignorados += 1
                continue

            Disponibilidade.objects.create(
                clinica=clinica,
                profissional=profissional,
                dia_semana=int(dia),
                hora_inicio=hora_inicio,
                hora_fim=hora_fim
            )
            criados += 1

        # 🔔 MENSAGENS DE FEEDBACK
        if criados:
            messages.success(
                request,
                f"✅ {criados} disponibilidade(s) cadastrada(s) com sucesso."
            )

        if ignorados:
            messages.warning(
                request,
                f"⚠️ {ignorados} disponibilidade(s) já existiam e não foram duplicadas."
            )

        return redirect("disponibilidade_create")

    return render(request, "clinica/disponibilidade.html", {
        "profissionais": profissionais,
        "dias_semana": dias_semana
    })

@login_required
def disponibilidade_list(request):
    clinica = Clinica.objects.get(user=request.user)

    disponibilidades = Disponibilidade.objects.filter(
        clinica=clinica
    ).order_by("profissional", "dia_semana", "hora_inicio")

    dias = {
        0: "Segunda",
        1: "Terça",
        2: "Quarta",
        3: "Quinta",
        4: "Sexta",
        5: "Sábado",
        6: "Domingo",
    }

    return render(request, "clinica/disponibilidade_list.html", {
        "disponibilidades": disponibilidades,
        "dias": dias,
    })

@login_required
def disponibilidade_delete(request, pk):
    if request.method != "POST":
        return redirect("disponibilidade_list")

    clinica = Clinica.objects.get(user=request.user)

    disponibilidade = Disponibilidade.objects.get(
        pk=pk,
        clinica=clinica
    )

    existe_agendamento = Agendamento.objects.filter(
        clinica=clinica,
        profissional=disponibilidade.profissional,
        data__week_day=disponibilidade.dia_semana + 2,
        horario__gte=disponibilidade.hora_inicio,
        horario__lt=disponibilidade.hora_fim
    ).exists()

    if existe_agendamento:
        messages.error(
            request,
            "❌ Não é possível excluir. Já existem agendamentos para esta disponibilidade."
        )
        return redirect("disponibilidade_list")

    disponibilidade.delete()
    messages.success(request, "Disponibilidade excluída com sucesso.")
    return redirect("disponibilidade_list")


@login_required
def disponibilidade_edit(request, pk):
    # 🔐 Clínica logada
    clinica = get_object_or_404(Clinica, user=request.user)

    # 📅 Disponibilidade
    disponibilidade = get_object_or_404(
        Disponibilidade,
        pk=pk,
        clinica=clinica
    )

    profissionais = Profissional.objects.filter(clinica=clinica)

    # 🔒 VERIFICAR CONFLITO REAL DE AGENDAMENTO
    hoje = timezone.now().date()

    # 🔁 MAPEAMENTO CORRETO DO DIA DA SEMANA
    # Disponibilidade:
    # 0=Seg, 1=Ter, 2=Qua, 3=Qui, 4=Sex, 5=Sáb, 6=Dom
    # Django week_day:
    # 1=Dom, 2=Seg, 3=Ter, 4=Qua, 5=Qui, 6=Sex, 7=Sáb
    MAPA_DIA_SEMANA = {
        0: 2,  # Segunda
        1: 3,  # Terça
        2: 4,  # Quarta
        3: 5,  # Quinta
        4: 6,  # Sexta
        5: 7,  # Sábado
        6: 1,  # Domingo
    }

    django_week_day = MAPA_DIA_SEMANA[disponibilidade.dia_semana]

    existe_conflito = Agendamento.objects.filter(
        clinica=clinica,
        profissional=disponibilidade.profissional,
        data__gte=hoje,
        data__week_day=django_week_day,
        horario__gte=disponibilidade.hora_inicio,
        horario__lt=disponibilidade.hora_fim,
    ).exists()

    if existe_conflito:
        messages.error(
            request,
            "❌ Não é possível editar esta disponibilidade pois já existem agendamentos neste dia e horário."
        )
        return redirect("disponibilidade_list")

    # ✏️ SALVAR EDIÇÃO
    if request.method == "POST":
        disponibilidade.profissional_id = request.POST.get("profissional")
        disponibilidade.dia_semana = int(request.POST.get("dia_semana"))
        disponibilidade.hora_inicio = request.POST.get("hora_inicio")
        disponibilidade.hora_fim = request.POST.get("hora_fim")
        disponibilidade.save()

        messages.success(request, "✅ Disponibilidade atualizada com sucesso.")
        return redirect("disponibilidade_list")

    # 📆 Dias da semana (exibição)
    dias_semana = [
        (0, "Segunda"),
        (1, "Terça"),
        (2, "Quarta"),
        (3, "Quinta"),
        (4, "Sexta"),
        (5, "Sábado"),
        (6, "Domingo"),
    ]

    return render(request, "clinica/disponibilidade_edit.html", {
        "disponibilidade": disponibilidade,
        "profissionais": profissionais,
        "dias_semana": dias_semana,
    })

@login_required
def disponibilidade_tem_agendamento(disponibilidade):
    """
    Retorna True se existir agendamento usando essa disponibilidade
    """
    # converte dia da semana em número do Python (segunda=0)
    dia_semana = disponibilidade.dia_semana

    # busca agendamentos do profissional
    agendamentos = Agendamento.objects.filter(
        profissional=disponibilidade.profissional
    )

    for ag in agendamentos:
        if ag.data.weekday() == dia_semana:
            if disponibilidade.hora_inicio <= ag.horario <= disponibilidade.hora_fim:
                return True

    return False

@login_required
def agendamento_delete(request, pk):
    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
        clinica__user=request.user  # 🔒 garante clínica correta
    )

    hoje = timezone.now().date()
    paciente = agendamento.paciente
    clinica = agendamento.clinica

    if agendamento.data < hoje:
        messages.error(
            request,
            "❌ Não é possível excluir um agendamento já realizado."
        )
        return redirect("clinica_dashboard")

    if request.method == "POST":

        # 📲 WHATSAPP DE CANCELAMENTO
        if pode_enviar_whatsapp(clinica):
            mensagem = (
                f"Olá {paciente.nome} 👋\n\n"
                f"Seu agendamento foi cancelado:\n\n"
                f"📅 Data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                f"⏰ Horário: {agendamento.horario.strftime('%H:%M')}\n"
                f"🦷 Serviço: {agendamento.servico}\n\n"
                f"Se precisar reagendar, entre em contato conosco."
            )

            enviado = enviar_whatsapp(
                paciente.telefone,
                mensagem
            )

            if enviado:
                registrar_envio_whatsapp(
                    clinica=clinica,
                    telefone=paciente.telefone,
                    tipo="cancelamento"
                )

        agendamento.delete()

        messages.success(
            request,
            "✅ Agendamento cancelado com sucesso."
        )

        return redirect("clinica_dashboard")

    return redirect("clinica_dashboard")

@login_required
def agendamento_edit(request, pk):
    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
        clinica__user=request.user  # 🔒 segurança
    )

    hoje = timezone.now().date()

    if agendamento.data < hoje:
        messages.error(
            request,
            "❌ Não é possível editar um agendamento já realizado."
        )
        return redirect("clinica_dashboard")

    if request.method == "POST":
        data_nova = request.POST.get("data")
        horario_novo = request.POST.get("horario")

        if not data_nova or not horario_novo:
            messages.error(request, "Preencha todos os campos.")
            return redirect("agendamento_edit", pk=pk)

        # 🔥 converte string → date / time
        data_nova = datetime.strptime(data_nova, "%Y-%m-%d").date()
        horario_novo = datetime.strptime(horario_novo, "%H:%M").time()

        # 🔍 verifica se realmente mudou
        mudou = (
            agendamento.data != data_nova or
            agendamento.horario != horario_novo
        )

        if not mudou:
            messages.info(
                request,
                "Nenhuma alteração foi feita no agendamento."
            )
            return redirect("clinica_dashboard")

        # 🔒 verifica conflito
        conflito = Agendamento.objects.filter(
            profissional=agendamento.profissional,
            data=data_nova,
            horario=horario_novo
        ).exclude(pk=agendamento.pk).exists()

        if conflito:
            messages.error(
                request,
                "❌ Este horário já está ocupado. Escolha outro."
            )
            return redirect("agendamento_edit", pk=pk)

        # ✅ salva alteração
        agendamento.data = data_nova
        agendamento.horario = horario_novo
        agendamento.save()

        # 📲 WHATSAPP DE EDIÇÃO
        clinica = agendamento.clinica
        paciente = agendamento.paciente

        if pode_enviar_whatsapp(clinica):
            mensagem = (
                f"Olá {paciente.nome} 👋\n\n"
                f"Seu agendamento foi ALTERADO:\n\n"
                f"📅 Nova data: {agendamento.data.strftime('%d/%m/%Y')}\n"
                f"⏰ Novo horário: {agendamento.horario.strftime('%H:%M')}\n"
                f"👨‍⚕️ Profissional: {agendamento.profissional}\n"
                f"🦷 Serviço: {agendamento.servico}\n\n"
                f"Se tiver alguma dúvida, entre em contato conosco."
            )

            enviado = enviar_whatsapp(
                paciente.telefone,
                mensagem
            )

            if enviado:
                registrar_envio_whatsapp(
                    clinica=clinica,
                    telefone=paciente.telefone,
                    tipo="edicao"
                )

        messages.success(
            request,
            "✅ Agendamento atualizado com sucesso."
        )

        return redirect("clinica_dashboard")

    # GET
    return render (
    request,
    "clinica/agendamento_edit.html",
    {
        "agendamento": agendamento
    }
)

@login_required
def relatorio_agendamentos_csv(request):
    clinica = Clinica.objects.get(user=request.user)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    agendamentos = Agendamento.objects.filter(
        clinica=clinica
    ).select_related(
        "paciente",
        "profissional",
        "servico"
    ).order_by("data", "horario")

    if data_inicio:
        agendamentos = agendamentos.filter(data__gte=data_inicio)

    if data_fim:
        agendamentos = agendamentos.filter(data__lte=data_fim)

    response = HttpResponse(
        content_type="text/csv"
    )
    response["Content-Disposition"] = 'attachment; filename="agendamentos.csv"'

    writer = csv.writer(response)
    writer.writerow([
        "Data",
        "Horário",
        "Paciente",
        "Telefone",
        "Serviço",
        "Profissional"
    ])

    for a in agendamentos:
        writer.writerow([
            a.data.strftime("%d/%m/%Y"),
            a.horario.strftime("%H:%M"),
            a.paciente.nome,
            a.paciente.telefone,
            a.servico,
            a.profissional
        ])

    return response

@login_required
def relatorio_agendamentos_pdf(request):
    clinica = Clinica.objects.get(user=request.user)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    agendamentos = Agendamento.objects.filter(
        clinica=clinica
    ).select_related(
        "paciente",
        "profissional",
        "servico"
    ).order_by("data", "horario")

    if data_inicio:
        agendamentos = agendamentos.filter(data__gte=data_inicio)

    if data_fim:
        agendamentos = agendamentos.filter(data__lte=data_fim)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'attachment; filename="agendamentos.pdf"'

    pdf = canvas.Canvas(response, pagesize=A4)
    largura, altura = A4

    y = altura - 2 * cm

    # Título
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(2 * cm, y, "Relatório de Agendamentos")
    y -= 1 * cm

    pdf.setFont("Helvetica", 10)
    pdf.drawString(2 * cm, y, f"Clínica: {clinica.nome}")
    y -= 0.7 * cm

    if data_inicio or data_fim:
        pdf.drawString(
            2 * cm,
            y,
            f"Período: {data_inicio or 'Início'} até {data_fim or 'Hoje'}"
        )
        y -= 1 * cm
    else:
        y -= 0.5 * cm

    # Cabeçalho da tabela
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawString(2 * cm, y, "Data")
    pdf.drawString(4 * cm, y, "Hora")
    pdf.drawString(6 * cm, y, "Paciente")
    pdf.drawString(11 * cm, y, "Telefone")
    pdf.drawString(15 * cm, y, "Serviço")
    y -= 0.5 * cm

    pdf.setFont("Helvetica", 9)

    for a in agendamentos:
        if y < 2 * cm:
            pdf.showPage()
            pdf.setFont("Helvetica", 9)
            y = altura - 2 * cm

        pdf.drawString(2 * cm, y, a.data.strftime("%d/%m/%Y"))
        pdf.drawString(4 * cm, y, a.horario.strftime("%H:%M"))
        pdf.drawString(6 * cm, y, a.paciente.nome or "")
        pdf.drawString(11 * cm, y, a.paciente.telefone)
        pdf.drawString(15 * cm, y, str(a.servico))

        y -= 0.4 * cm

    pdf.showPage()
    pdf.save()

    return response

@login_required
def relatorio_agendamentos_html(request):
    clinica = Clinica.objects.get(user=request.user)

    data_inicio = request.GET.get("data_inicio")
    data_fim = request.GET.get("data_fim")

    agendamentos = Agendamento.objects.filter(
        clinica=clinica
    ).select_related(
        "paciente",
        "profissional",
        "servico"
    ).order_by("data", "horario")

    if data_inicio:
        agendamentos = agendamentos.filter(data__gte=data_inicio)

    if data_fim:
        agendamentos = agendamentos.filter(data__lte=data_fim)

    return render(request, "clinica/relatorios/agendamentos.html", {
        "clinica": clinica,
        "agendamentos": agendamentos,
        "data_inicio": data_inicio,
        "data_fim": data_fim,
        "hoje": timezone.now().date()
    })

@login_required
def minha_conta(request):
    clinica = Clinica.objects.filter(user=request.user).first()
    agora = timezone.now()

    # WhatsApp usado no mês atual
    whatsapp_usados = WhatsappLog.objects.filter(
        clinica=clinica,
        data__month=agora.month,
        data__year=agora.year
    ).count() if clinica else 0

    # Limite e percentual
    whatsapp_limite = None
    whatsapp_percentual = 0

    if clinica and clinica.plano and clinica.plano.max_whatsapp_mes is not None:
        whatsapp_limite = clinica.plano.max_whatsapp_mes + clinica.whatsapp_extra
        if whatsapp_limite > 0:
            whatsapp_percentual = int((whatsapp_usados / whatsapp_limite) * 100)

    # 📈 HISTÓRICO MENSAL (últimos 6 meses)
    historico_whatsapp = []

    if clinica:
        historico_whatsapp = (
            WhatsappLog.objects
            .filter(clinica=clinica)
            .annotate(mes=TruncMonth("data"))
            .values("mes")
            .annotate(total=Count("id"))
            .order_by("-mes")[:6]
        )

    return render(request, "clinica/minha_conta.html", {
        "whatsapp_usados": whatsapp_usados,
        "whatsapp_limite": whatsapp_limite,
        "whatsapp_percentual": whatsapp_percentual,
        "historico_whatsapp": historico_whatsapp,
    })


@login_required
def planos(request):
    clinica = Clinica.objects.filter(user=request.user).first()
    planos = Plano.objects.all().order_by("preco")

    return render(request, "clinica/planos.html", {
        "clinica": clinica,
        "planos": planos,
    })

@login_required
def profissional_create(request):
    form = ProfissionalForm(request.POST or None)

    if form.is_valid():
        profissional = form.save(commit=False)
        profissional.clinica = request.user.clinica
        profissional.save()
        return redirect('clinica_dashboard')

    return render(request, 'clinica/profissional_form.html', {'form': form})

@login_required
def servico_create(request):
    form = ServicoForm(request.POST or None)

    if form.is_valid():
        servico = form.save(commit=False)
        servico.clinica = request.user.clinica
        servico.save()
        return redirect('clinica_dashboard')

    return render(request, 'clinica/servico_form.html', {'form': form})
    



import csv
from weasyprint import HTML
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from django.template.loader import render_to_string
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, permission_required
from django.views.generic import TemplateView
from django.http import HttpResponse
from django.contrib import messages
from datetime import datetime
from django.utils import timezone
from django.contrib.auth.mixins import LoginRequiredMixin,PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.views import View
from agendamentos.models import Clinica, Agendamento, Disponibilidade, Profissional, Plano
from agendamentos.models import WhatsappLog, Agendamento
from django.contrib import messages
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.shortcuts import get_object_or_404
from datetime import datetime, timedelta
from agendamentos.models import Profissional, Servico
from django.views.decorators.http import require_POST
from agendamentos.models import Paciente,Prontuario
from django.db.models import Q
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

        # 🔑 Clínica vinculada ao usuário
        #clinica = self.request.user.usuarioclinica.clinica
        clinica = self.request.user.clinica

        # 📅 Datas base
        agora = timezone.now()
        hoje = agora.date()
        amanha = hoje + timedelta(days=1)
        fim_semana = hoje + timedelta(days=7)

        # 📊 WhatsApp usados no mês
        whatsapp_usados = WhatsappLog.objects.filter(
            clinica=clinica,
            data__month=agora.month,
            data__year=agora.year
        ).count()

        # 📅 TODOS os agendamentos da clínica
        agendamentos = Agendamento.objects.filter(
            clinica=clinica
        ).select_related(
            "paciente",
            "profissional",
            "servico"
        ).order_by("data", "horario")

        # 🔒 Regra única de edição
        for a in agendamentos:
            a.pode_editar = a.data >= hoje

        # 📌 Agendamentos de hoje
        agendamentos_hoje = [a for a in agendamentos if a.data == hoje]

        # ⏭️ Agendamentos de amanhã
        agendamentos_amanha = [a for a in agendamentos if a.data == amanha]

        # 📆 Agendamentos da semana (exclui hoje e amanhã)
        agendamentos_semana = Agendamento.objects.filter(
            clinica=clinica,
            data__gt=amanha,
            data__lte=fim_semana
        ).select_related(
            "paciente",
            "profissional",
            "servico"
        ).order_by("data", "horario")

        # 🧠 Contexto final
        context.update({
            "clinica": clinica,
            "agendamentos": agendamentos,
            "agendamentos_hoje": agendamentos_hoje,
            "agendamentos_amanha": agendamentos_amanha,
            "agendamentos_semana": agendamentos_semana,
            "today": hoje,
            "fim_semana": fim_semana,
            "whatsapp_usados": whatsapp_usados,
        })

        return context



@require_POST
@login_required
def clinica_logout(request):
    logout(request)
    return redirect("clinica_login")

@login_required
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def disponibilidade_create(request):
    clinica = request.user.usuarioclinica.clinica
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
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def disponibilidade_list(request):
    clinica = request.user.usuarioclinica.clinica

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

    return render(
        request,
        "clinica/disponibilidade_list.html",
        {
            "disponibilidades": disponibilidades,
            "dias": dias,
        }
    )

@login_required
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
@require_POST
def disponibilidade_delete(request, pk):
    if request.method != "POST":
        return redirect("disponibilidade_list")

    clinica = clinica = request.user.usuarioclinica.clinica

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
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def disponibilidade_edit(request, pk):
    clinica = request.user.usuarioclinica.clinica

    disponibilidade = get_object_or_404(
        Disponibilidade,
        pk=pk,
        clinica=clinica
    )

    profissionais = Profissional.objects.filter(clinica=clinica)
    hoje = timezone.now().date()

    # 🔁 Mapeamento correto do dia da semana
    # Disponibilidade: 0=Seg ... 6=Dom
    # Django week_day: 1=Dom ... 7=Sáb
    MAPA_DIA_SEMANA = {
        0: 2,
        1: 3,
        2: 4,
        3: 5,
        4: 6,
        5: 7,
        6: 1,
    }

    django_week_day = MAPA_DIA_SEMANA[disponibilidade.dia_semana]

    # 🔒 Verifica se já existem agendamentos futuros
    existe_agendamento = Agendamento.objects.filter(
        clinica=clinica,
        profissional=disponibilidade.profissional,
        data__gte=hoje,
        data__week_day=django_week_day,
        horario__gte=disponibilidade.hora_inicio,
        horario__lt=disponibilidade.hora_fim,
    ).exists()

    if existe_agendamento:
        messages.error(
            request,
            "❌ Não é possível editar esta disponibilidade pois já existem agendamentos."
        )
        return redirect("disponibilidade_list")

    if request.method == "POST":
        disponibilidade.profissional_id = request.POST.get("profissional")
        disponibilidade.dia_semana = int(request.POST.get("dia_semana"))
        disponibilidade.hora_inicio = request.POST.get("hora_inicio")
        disponibilidade.hora_fim = request.POST.get("hora_fim")
        disponibilidade.save()

        messages.success(
            request,
            "✅ Disponibilidade atualizada com sucesso."
        )
        return redirect("disponibilidade_list")

    return render(
        request,
        "clinica/disponibilidade_edit.html",
        {
            "disponibilidade": disponibilidade,
            "profissionais": profissionais,
            "dias_semana": Disponibilidade.DIA_SEMANA,
        }
    )

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
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
@require_POST
def agendamento_delete(request, pk):
    clinica = request.user.usuarioclinica.clinica
    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
        clinica=clinica  # 🔒 garante clínica correta
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
                agendamento.clinica,
                agendamento.paciente.telefone,
                mensagem
            )
            print("ENVIANDO CANCELAMENTO...")
            print("CLINICA:", clinica)
            print("TOKEN:", clinica.whatsapp_token) 

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
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def agendamento_edit(request, pk):
    print("******************************")
    print("         Def agenamento edit                  ")
    clinica = request.user.usuarioclinica.clinica
    

    agendamento = get_object_or_404(
        Agendamento,
        pk=pk,
        clinica=clinica
    )

    hoje = timezone.now().date()

    if agendamento.data < hoje:
        messages.error(
            request,
            "❌ Não é possível editar um agendamento já realizado."
        )
        return redirect("clinica_dashboard")

    if request.method == "POST":
        data = request.POST.get("data")
        horario = request.POST.get("horario")

        if not data or not horario:
            messages.error(request, "Preencha todos os campos.")
            return redirect("agendamento_edit", pk=pk)

        data = datetime.strptime(data, "%Y-%m-%d").date()
        horario = datetime.strptime(horario, "%H:%M").time()

        conflito = Agendamento.objects.filter(
            clinica=clinica,
            profissional=agendamento.profissional,
            data=data,
            horario=horario
        ).exclude(pk=agendamento.pk).exists()

        if conflito:
            messages.error(
                request,
                "❌ Este horário já está ocupado."
            )
            return redirect("agendamento_edit", pk=pk)
        
        # verifica se mudou algo
        if agendamento.data == data and agendamento.horario == horario:
            messages.info(request, "Nenhuma alteração foi feita.")
            return redirect("clinica_dashboard")

        agendamento.data = data
        agendamento.horario = horario
        agendamento.save()
        mensagem = (
            f"🔄 Seu agendamento foi ALTERADO\n\n"
            f"📅 Nova data: {agendamento.data.strftime('%d/%m/%Y')}\n"
            f"⏰ Novo horário: {agendamento.horario.strftime('%H:%M')}\n"
            f"👨‍⚕️ Profissional: {agendamento.profissional}\n\n"
            f"Se precisar de algo, estamos à disposição!"
        )

        enviar_whatsapp(
            agendamento.clinica,
            agendamento.paciente.telefone,
            mensagem
        )

        messages.success(
            request,
            "✅ Agendamento atualizado com sucesso."
        )
        return redirect("clinica_dashboard")

    return render(
        request,
        "clinica/agendamento_edit.html",
        {"agendamento": agendamento}
    )

@login_required
@permission_required("agendamentos.ver_relatorios", raise_exception=True)
def relatorio_agendamentos_csv(request):
    clinica = request.user.usuarioclinica.clinica

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
@permission_required("agendamentos.ver_relatorios", raise_exception=True)
def relatorio_agendamentos_pdf(request):
    clinica = request.user.usuarioclinica.clinica

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
@permission_required("agendamentos.ver_relatorios", raise_exception=True)
def relatorio_agendamentos_html(request):
    clinica = request.user.usuarioclinica.clinica

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
        whatsapp_limite = clinica.plano.max_whatsapp_mes #+ clinica.whatsapp_extra
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
@permission_required("clinica.view_plano", raise_exception=True)
def planos(request):
    clinica = request.user.usuarioclinica.clinica
    planos = Plano.objects.all().order_by("preco")

    return render(
        request,
        "clinica/planos.html",
        {
            "clinica": clinica,
            "planos": planos,
        }
    )
@login_required
@permission_required("agendamentos.gerenciar_profissionais", raise_exception=True)
def profissional_create(request):
    clinica = request.user.usuarioclinica.clinica
    form = ProfissionalForm(request.POST or None)

    if form.is_valid():
        profissional = form.save(commit=False)
        profissional.clinica = clinica
        profissional.save()
        form.save_m2m()
        return redirect("profissional_list")

    return render(
        request,
        "clinica/profissional_form.html",
        {"form": form}
    )


@login_required
@permission_required("agendamentos.gerenciar_servicos", raise_exception=True)
def servico_create(request):
    clinica = request.user.usuarioclinica.clinica
    form = ServicoForm(request.POST or None)

    if form.is_valid():
        servico = form.save(commit=False)
        servico.clinica = clinica
        servico.save()
        return redirect('servico_list')

    return render(request, 'clinica/servico_form.html', {'form': form})

@login_required
@permission_required("agendamentos.gerenciar_profissionais", raise_exception=True)
def profissional_update(request, pk):
    clinica = request.user.usuarioclinica.clinica

    profissional = get_object_or_404(
        Profissional,
        pk=pk,
        clinica=clinica
    )

    form = ProfissionalForm(request.POST or None, instance=profissional)

    # garante que só apareçam serviços da clínica
    form.fields["servicos"].queryset = Servico.objects.filter(
        clinica=clinica
    )

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "✅ Profissional atualizado com sucesso."
        )
        return redirect("profissional_list")

    return render(
        request,
        "clinica/profissional_form.html",
        {"form": form}
    )

@login_required
@permission_required("agendamentos.gerenciar_servicos", raise_exception=True)
def servico_update(request, pk):
    clinica = request.user.usuarioclinica.clinica

    servico = get_object_or_404(
        Servico,
        pk=pk,
        clinica=clinica
    )

    form = ServicoForm(request.POST or None, instance=servico)

    if form.is_valid():
        form.save()
        messages.success(
            request,
            "✅ Serviço atualizado com sucesso."
        )
        return redirect("servico_list")

    return render(
        request,
        "clinica/servico_form.html",
        {"form": form}
    )

@login_required
@permission_required("agendamentos.gerenciar_servicos", raise_exception=True)
def servico_list(request):
    clinica = request.user.usuarioclinica.clinica
    servicos = Servico.objects.filter(clinica=clinica)
    return render(request, "clinica/servico_list.html", {"servicos": servicos})
    
@login_required
@permission_required("agendamentos.gerenciar_profissionais", raise_exception=True)
def profissional_list(request):
    clinica = request.user.usuarioclinica.clinica
    profissionais = Profissional.objects.filter(clinica=clinica)
    return render(
        request,
        "clinica/profissional_list.html",
        {"profissionais": profissionais}
    )

@login_required
@permission_required("agendamentos.gerenciar_profissionais", raise_exception=True)
@require_POST
def profissional_delete(request, pk):
    clinica = request.user.usuarioclinica.clinica

    profissional = get_object_or_404(
        Profissional,
        pk=pk,
        clinica=clinica
    )

    profissional.delete()

    messages.success(
        request,
        "🗑️ Profissional excluído com sucesso."
    )

    return redirect("profissional_list")

@login_required
@permission_required("agendamentos.gerenciar_servicos", raise_exception=True)
@require_POST
def servico_delete(request, pk):
    clinica = request.user.usuarioclinica.clinica

    servico = get_object_or_404(
        Servico,
        pk=pk,
        clinica=clinica
    )

    servico.delete()

    messages.success(
        request,
        "🗑️ Serviço excluído com sucesso."
    )

    return redirect("servico_list")

@login_required
def agenda_semana(request):
    clinica = request.user.usuarioclinica.clinica

    hoje = timezone.now().date()
    fim_semana = hoje + timedelta(days=7)

    agendamentos = Agendamento.objects.filter(
        clinica=clinica,
        data__gte=hoje,
        data__lte=fim_semana
    ).select_related(
        "paciente", "profissional", "servico"
    ).order_by("data", "horario")

    return render(
        request,
        "clinica/agenda_semana.html",
        {
            "agendamentos": agendamentos,
            "hoje": hoje,
            "fim_semana": fim_semana,
        }
    )

    
@login_required
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def prontuario_paciente(request, paciente_id):
    clinica = request.user.usuarioclinica.clinica

    paciente = get_object_or_404(
        Paciente.objects.filter(
            Q(agendamento__clinica=clinica) |
            Q(prontuario__clinica=clinica)
        ).distinct(),
        pk=paciente_id
    )

    profissionais = Profissional.objects.filter(
        clinica=clinica
    ).order_by("nome")

    if request.method == "POST":
        anotacoes = request.POST.get("anotacoes", "").strip()
        profissional_id = request.POST.get("profissional")

        if not anotacoes:
            messages.error(request, "❌ Descreva o atendimento realizado.")
            return redirect("prontuario_paciente", paciente_id=paciente.id)

        profissional = None
        if profissional_id:
            profissional = get_object_or_404(
                Profissional,
                pk=profissional_id,
                clinica=clinica
            )

        Prontuario.objects.create(
            clinica=clinica,
            paciente=paciente,
            profissional=profissional,
            anotacoes=anotacoes
        )

        messages.success(request, "✅ Prontuário salvo com sucesso.")
        return redirect("prontuario_paciente", paciente_id=paciente.id)

    prontuarios = Prontuario.objects.filter(
        clinica=clinica,
        paciente=paciente
    ).select_related("profissional")

    return render(
        request,
        "clinica/prontuario_paciente.html",
        {
            "paciente": paciente,
            "prontuarios": prontuarios,
            "profissionais": profissionais,
        }
    )

@login_required
@permission_required("agendamentos.gerenciar_agendamentos", raise_exception=True)
def prontuario_busca(request):
    clinica = request.user.usuarioclinica.clinica
    termo = request.GET.get("q", "").strip()

    pacientes_ids = set(
        Agendamento.objects.filter(clinica=clinica).values_list("paciente_id", flat=True)
    )
    pacientes_ids.update(
        Prontuario.objects.filter(clinica=clinica).values_list("paciente_id", flat=True)
    )

    pacientes = Paciente.objects.filter(id__in=pacientes_ids)

    if termo:
        pacientes = pacientes.filter(nome__icontains=termo)

    pacientes = pacientes.order_by("nome", "telefone")

    return render(
        request,
        "clinica/prontuario_busca.html",
        {
            "pacientes": pacientes,
            "termo": termo,
        }
    )

@login_required
def pagina_conectar_whatsapp(request):
    return render(request, "clinica/conectar_whatsapp.html")

from django.shortcuts import render, redirect
from django.utils import timezone
import re
from .decorators import paciente_logado
from agendamentos.utils import normalizar_telefone
from agendamentos.models import Paciente, Agendamento, Clinica
from functools import wraps
from pacientes.services import enviar_codigo_login

def solicitar_codigo(request):

    print("##################################")
    print("solicitar codigo")
    print("-----------------------")
    print("METHOD:", request.method)

    if request.method == "POST":

        # normaliza telefone
        telefone = normalizar_telefone(
            request.POST.get("telefone")
        )

        print("Telefone recebido:", telefone)

        paciente = Paciente.objects.filter(
            telefone=telefone
        ).first()

        print("Paciente encontrado:", paciente)
        print("-----------------------")

        if paciente:

            # 📌 pega clínica da sessão
            clinica_slug = request.session.get("clinica_slug")

            clinica = None
            if clinica_slug:
                clinica = Clinica.objects.filter(
                    slug=clinica_slug
                ).first()

            # 📌 salva telefone na sessão (IMPORTANTE)
            request.session["telefone_login"] = telefone

            # 🔐 remove login antigo (mantém clínica)
            request.session.pop("paciente_id", None)

            # 🔢 gera código (MODEL)
            paciente.gerar_codigo()

            # 📲 envia código (SERVICE)
            if clinica:
                enviar_codigo_login(paciente, clinica)
            else:
                print("⚠️ Clínica não encontrada — código não enviado")

            print("##### Código gerado:", paciente.codigo_login)

        # sempre vai para validar
        return redirect("validar_codigo")

    return render(request, "pacientes/solicitar_codigo.html")

def validar_codigo(request):
    print("********** DEF Validar_ codigo*******")
    if request.method == "POST":
        telefone = normalizar_telefone(request.POST.get("telefone"))
        codigo = request.POST.get("codigo")
        print("TELEFONE11", telefone)
        paciente = Paciente.objects.filter(
            telefone=telefone,
            codigo_login=codigo,
            codigo_expira_em__gte=timezone.now()
        ).first()

        if paciente:
            request.session["paciente_id"] = paciente.id

            paciente.codigo_login = None
            paciente.codigo_expira_em = None
            paciente.tentativas_codigo = 0
            paciente.save()

            return redirect("dashboard_paciente")

        else:
            paciente = Paciente.objects.filter(telefone=telefone).first()
            if paciente:
                paciente.tentativas_codigo += 1
                paciente.save()

    return render(request, "pacientes/validar_codigo.html")



@paciente_logado
def dashboard_paciente(request):

    print("+++++++ Def dashboard paciente ++++++++")

    paciente = Paciente.objects.get(
        id=request.session["paciente_id"]
    )

    clinica = None

    # tenta pegar da sessão
    clinica_slug = request.session.get("clinica_slug")

    if clinica_slug:
        clinica = Clinica.objects.filter(
            slug=clinica_slug
        ).first()

    # ✅ fallback automático
    if not clinica:
        ultimo_agendamento = (
            Agendamento.objects
            .filter(paciente=paciente)
            .select_related("clinica")
            .order_by("-id")
            .first()
        )

        if ultimo_agendamento:
            clinica = ultimo_agendamento.clinica

            # salva novamente na sessão
            request.session["clinica_slug"] = clinica.slug

    print("SESSION:", request.session)

    agendamentos = (
        Agendamento.objects
        .filter(paciente=paciente)
        .select_related("servico", "profissional")
        .order_by("-data", "-horario")
    )

    return render(
        request,
        "pacientes/dashboard.html",
        {
            "paciente": paciente,
            "clinica": clinica,
            "agendamentos": agendamentos,
        }
    )
@paciente_logado
def agendar_logado(request, clinica_slug):
    print("########################")
    print("  DEF AGENDAR LOGADO")
    # pega clínica da sessão
    clinica_slug = request.session.get("clinica_slug")
    print("Clinica = ", clinica_slug)

    if not clinica_slug:
        print(" NOT CLINICA")
        return redirect("dashboard_paciente")

    # vai direto para passo 2
    return redirect(
        "passo2_servico",
        clinica_slug=clinica_slug
    )

def logout_paciente(request):
    request.session.flush()  # apaga toda a sessão
    return redirect("solicitar_codigo")


"""def paciente_logado(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        # verifica se paciente está logado
        if not request.session.get("paciente_id"):
            return redirect("solicitar_codigo")

        # continua para a view
        return view_func(request, *args, **kwargs)

    return wrapper"""
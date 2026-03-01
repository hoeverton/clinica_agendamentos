from django.shortcuts import render, redirect
from django.utils import timezone
import re
from .decorators import paciente_logado
from agendamentos.utils import normalizar_telefone
from agendamentos.models import Paciente

def solicitar_codigo(request):

    print("##################################")
    print("solicitar codigo")
    print("-----------------------")
    print("METHOD:", request.method)

    if request.method == "POST":

        # normaliza telefone
        #telefone = re.sub(r"\D", "", request.POST.get("telefone", ""))
        telefone = normalizar_telefone(
    request.POST.get("telefone")
)

        print("Telefone recebido:", telefone)

        paciente = Paciente.objects.filter(telefone=telefone).first()

        print("Paciente encontrado:", paciente)
        print("-----------------------")

        if paciente:
            # 🔐 limpa sessão antiga (login seguro)
            request.session.flush()

            # gera novo código OTP
            paciente.gerar_codigo()

            # simulação envio (depois vira WhatsApp)
            print("##### Código enviado:", paciente.codigo_login)

        # sempre vai para validar código
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
    paciente = Paciente.objects.get(id=request.session["paciente_id"])
    return render(request, "pacientes/dashboard.html", {"paciente": paciente})
# Create your views here.

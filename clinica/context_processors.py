from agendamentos.models import Clinica,WhatsappLog
from django.utils import timezone


def clinica_ativa(request):
    if request.user.is_authenticated:
        clinica = Clinica.objects.filter(user=request.user).first()
        return {"clinica": clinica}
    return {}

def whatsapp_status(request):
    if not request.user.is_authenticated:
        return {}

    clinica = Clinica.objects.filter(user=request.user).first()
    if not clinica or not clinica.plano:
        return {}

    agora = timezone.now()

    usados = WhatsappLog.objects.filter(
        clinica=clinica,
        data__month=agora.month,
        data__year=agora.year
    ).count()

    limite = None
    percentual = 0

    if clinica.plano.max_whatsapp_mes is not None:
        limite = clinica.plano.max_whatsapp_mes + clinica.whatsapp_extra
        if limite > 0:
            percentual = int((usados / limite) * 100)

    return {
        "whatsapp_usados": usados,
        "whatsapp_limite": limite,
        "whatsapp_percentual": percentual,
    }
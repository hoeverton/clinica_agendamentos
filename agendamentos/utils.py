from django.utils import timezone
from .models import WhatsappLog

def pode_enviar_whatsapp(clinica):
    plano = clinica.plano

    # plano ilimitado
    if plano.max_whatsapp_mes is None:
        return True

    usados = WhatsappLog.objects.filter(
        clinica=clinica,
        data__month=timezone.now().month,
        data__year=timezone.now().year
    ).count()

    limite_total = plano.max_whatsapp_mes + clinica.whatsapp_extra
    return usados < limite_total


def registrar_envio_whatsapp(clinica, telefone, tipo):
    WhatsappLog.objects.create(
        clinica=clinica,
        telefone=telefone,
        tipo=tipo
    )

def enviar_whatsapp(telefone, mensagem):
    """
    Simulação de envio de WhatsApp.
    Aqui futuramente entra API real (Twilio, Z-API, Meta, etc)
    """
    print("📲 WhatsApp enviado para:", telefone)
    print("Mensagem:", mensagem)
    return True

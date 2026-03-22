from django.utils import timezone
from .models import WhatsappLog
import re
import requests

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

def enviar_whatsapp(numero, mensagem):
    url = "https://api.w-api.app/v1/message/send-text?instanceId=LITE-WT27X1-TCQBZE"

    headers = {
        "Authorization": "Bearer bhLTUq7lDpb98Gm26skyFLUqTYPg7Wnrq",
        "Content-Type": "application/json"
    }

    payload = {
        "phone": numero,
        "message": mensagem
    }

    try:
        response = requests.post(url, json=payload, headers=headers)

        print("STATUS:", response.status_code)
        print("RESPOSTA:", response.text)

        return response.status_code == 200

    except Exception as e:
        print("Erro:", e)
        return False



def normalizar_telefone(numero):
    numero = re.sub(r"\D", "", numero)

    # adiciona 55 se não tiver
    if not numero.startswith("55"):
        numero = "55" + numero

    return numero
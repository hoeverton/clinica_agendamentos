from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["POST"])
def whatsapp_webhook(request):

    numero = request.data.get("number")
    mensagem = request.data.get("message")

    print(numero, mensagem)

    if mensagem.lower() == "oi":
        return Response({
            "reply": "Olá! 👋 Bem-vindo à clínica. Deseja agendar consulta?"
        })

    return Response({
        "reply": "Não entendi. Digite *oi* para iniciar."
    })

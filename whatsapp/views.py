from rest_framework.decorators import api_view
from rest_framework.response import Response
from agendamentos.models import ConversaWhatsapp, Servico, Agendamento, Paciente, Profissional, Clinica
from agendamentos.utils import enviar_whatsapp
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.http import JsonResponse
from whatsapp.utils import buscar_horarios_disponiveis
import requests 

@api_view(["POST"])
def whatsapp_webhook(request):

    numero = request.data.get("number")
    mensagem = request.data.get("message", "").lower()

    print("Mensagem recebida:", numero, mensagem)

    conversa, _ = ConversaWhatsapp.objects.get_or_create(telefone=numero)

    # =========================
    # INÍCIO
    # =========================
    if mensagem == "oi" or conversa.etapa == "inicio":
        conversa.etapa = "menu"
        conversa.save()

        resposta = (
            "Olá 👋\n\n"
            "1️⃣ Agendar consulta\n"
            "2️⃣ Cancelar agendamento"
        )

        enviar_whatsapp(numero, resposta)
        return Response({"reply": resposta})

    # =========================
    # MENU
    # =========================
    if conversa.etapa == "menu":
        if mensagem == "1":
            servicos = Servico.objects.all()

            texto = "Escolha o serviço:\n\n"
            for i, s in enumerate(servicos, 1):
                texto += f"{i} - {s.nome}\n"

            conversa.etapa = "servico"
            conversa.save()

            enviar_whatsapp(numero, texto)
            return Response({"reply": texto})

        else:
            return Response({"reply": "Digite 1 ou 2"})

    # =========================
    # SERVIÇO
    # =========================
    if conversa.etapa == "servico":
        servicos = list(Servico.objects.all())

        try:
            escolha = int(mensagem) - 1
            servico = servicos[escolha]

            conversa.servico = servico
            conversa.etapa = "data"
            conversa.save()

            resposta = "Digite a data (YYYY-MM-DD):"
            enviar_whatsapp(numero, resposta)

            return Response({"reply": resposta})

        except:
            return Response({"reply": "Opção inválida"})

    # =========================
    # DATA
    # =========================
    if conversa.etapa == "data":
        try:
            data_escolhida = datetime.strptime(mensagem, "%Y-%m-%d").date()

            profissional = Profissional.objects.first()
            clinica = Clinica.objects.first()
            duracao = conversa.servico.duracao_minutos

            horarios = buscar_horarios_disponiveis(
                clinica,
                profissional,
                data_escolhida,
                duracao
            )

            if not horarios:
                return Response({"reply": "❌ Não há horários disponíveis nesse dia."})

            conversa.data = data_escolhida
            conversa.etapa = "horario"
            conversa.save()

            texto = "Horários disponíveis:\n\n"
            for h in horarios:
                texto += f"{h.strftime('%H:%M')}\n"

            enviar_whatsapp(numero, texto)

            return Response({"reply": texto})

        except:
            return Response({"reply": "Formato inválido. Use YYYY-MM-DD"})

    # =========================
    # HORÁRIO
    # =========================
    if conversa.etapa == "horario":
        try:
            horario = datetime.strptime(mensagem, "%H:%M").time()

            paciente, _ = Paciente.objects.get_or_create(telefone=numero)

            agendamento = Agendamento.objects.create(
                paciente=paciente,
                servico=conversa.servico,
                profissional=Profissional.objects.first(),
                clinica=Clinica.objects.first(),
                data=conversa.data,
                horario=horario
            )

            conversa.etapa = "inicio"
            conversa.save()

            resposta = "✅ Agendamento confirmado!"
            enviar_whatsapp(numero, resposta)

            return Response({"reply": resposta})

        except:
            return Response({"reply": "Horário inválido"})

    return Response({"reply": "Digite 'oi' para começar"})

@login_required
def qr_code_whatsapp(request):
    clinica = request.user.usuarioclinica.clinica

    url = f"https://api.w-api.app/v1/instance/qr-code?instanceId={clinica.whatsapp_instance}"
    #url = f"https://api.w-api.app/v1/instance/get-qr-code?instanceId={clinica.whatsapp_instance}"
    
    headers = {
        "Authorization": f"Bearer {clinica.whatsapp_token}"
    }

    response = requests.get(url, headers=headers)

    print("STATUS:", response.status_code)
    print("TEXTO:", response.text)

    try:
        data = response.json()
    except:
        return JsonResponse({
            "erro": "Resposta inválida",
            "texto": response.text
        })

    return JsonResponse(data)


"""@login_required
def conectar_whatsapp(request):
    clinica = request.user.usuarioclinica.clinica

    #url = "https://api.w-api.app/v1/instance/create"
    url = "https://api.w-api.app/v1/instance/init"

    headers = {
        "Authorization": f"Bearer {clinica.whatsapp_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "instanceName": f"clinica_{clinica.id}"
    }

    response = requests.post(url, json=payload, headers=headers)

    print("STATUS:", response.status_code)
    print("TEXTO:", response.text)

    # 🔥 EVITA QUEBRAR
    try:
        data = response.json()
    except:
        return JsonResponse({
            "erro": "Resposta inválida da API",
            "status_code": response.status_code,
            "texto": response.text
        })

    return JsonResponse(data)"""
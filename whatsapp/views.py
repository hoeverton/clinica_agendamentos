from rest_framework.decorators import api_view
from rest_framework.response import Response
from agendamentos.models import ConversaWhatsapp, Servico, Agendamento, Paciente, Profissional, Clinica
from agendamentos.utils import enviar_whatsapp
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.http import JsonResponse
from whatsapp.utils import buscar_horarios_disponiveis
from django.http import JsonResponse
import requests 
from django.views.decorators.csrf import csrf_exempt
import re
import requests
import json


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
            
            servicos = Servico.objects.filter(clinica=clinica)

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
        servicos = list(Servico.objects.filter(clinica=clinica))
        

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

            profissional = Profissional.objects.filter(
                clinica=clinica
            ).first()
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

            paciente, _ = Paciente.objects.get_or_create(clinica=clinica,telefone=numero)

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


@csrf_exempt
def webhook_whatsapp(request):
    print("DEF Webhook_Whatsapp ")
    print(request.body)
    

    if request.method != "POST":
        return JsonResponse({"status": "ok"})

    data = json.loads(request.body)

    telefone = data.get("telefone")
    mensagem = data.get("mensagem", "").strip().lower()

    paciente = Paciente.objects.filter(
        telefone=telefone
    ).first()

    # -----------------------------------
    # NÃO CADASTRADO
    # -----------------------------------
    if not paciente:

        texto = """
            Olá 👋

            Seu número ainda não está cadastrado.

            Digite:

            1️⃣ Quero me cadastrar
            2️⃣ Falar com atendente
        """

        enviar_whatsapp(telefone, texto)
        return JsonResponse({"ok": True})

    # -----------------------------------
    # MENU PRINCIPAL
    # -----------------------------------
    if mensagem in ["oi", "ola", "olá", "menu", "0", "inicio", "início"]:

        texto = f"""
            Olá {paciente.nome} 👋

            Bem-vindo novamente.

            Digite uma opção:

            1️⃣ Agendar Consulta
            2️⃣ Confirmar Consulta
            3️⃣ Cancelar Consulta
            4️⃣ Minhas Consultas
            5️⃣ Falar com Atendente
        """

        enviar_whatsapp(telefone, texto)
        return JsonResponse({"ok": True})

    # -----------------------------------
    # 1 AGENDAR
    # -----------------------------------
    elif mensagem == "1":

        enviar_whatsapp(
            telefone,
            "📅 Para agendar consulta, responda com o dia desejado.\nEx: 28/04"
        )

    # -----------------------------------
    # 2 CONFIRMAR
    # -----------------------------------
    elif mensagem == "2":

        ag = Agendamento.objects.filter(
            paciente=paciente
        ).order_by("data", "horario").first()

        if ag:
            enviar_whatsapp(
                telefone,
                f"✅ Próxima consulta:\n{ag.data.strftime('%d/%m')} às {ag.horario.strftime('%H:%M')}"
            )
        else:
            enviar_whatsapp(
                telefone,
                "Nenhuma consulta encontrada."
            )

    # -----------------------------------
    # 3 CANCELAR
    # -----------------------------------
    elif mensagem == "3":

        enviar_whatsapp(
            telefone,
            "❌ Solicitação de cancelamento recebida.\nNossa equipe irá confirmar."
        )

    # -----------------------------------
    # 4 CONSULTAS
    # -----------------------------------
    elif mensagem == "4":

        consultas = Agendamento.objects.filter(
            paciente=paciente
        ).order_by("data", "horario")[:3]

        if consultas:

            texto = "📋 Suas próximas consultas:\n\n"

            for c in consultas:
                texto += f"{c.data.strftime('%d/%m')} às {c.horario.strftime('%H:%M')}\n"

            enviar_whatsapp(telefone, texto)

        else:

            enviar_whatsapp(
                telefone,
                "Nenhuma consulta agendada."
            )

    # -----------------------------------
    # 5 HUMANO
    # -----------------------------------
    elif mensagem == "5":

        enviar_whatsapp(
            telefone,
            "👩‍💼 Um atendente falará com você em breve."
        )

    # -----------------------------------
    # INVÁLIDO
    # -----------------------------------
    else:

        enviar_whatsapp(
            telefone,
            "Opção inválida.\nDigite MENU para ver opções."
        )

    return JsonResponse({"ok": True})
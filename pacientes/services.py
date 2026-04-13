from django.utils import timezone
from datetime import timedelta
from agendamentos.utils import enviar_whatsapp
import random



def enviar_codigo_login(paciente, clinica):
    mensagem = f"""
        🔐 Acesso à sua conta

        Olá, {paciente.nome}!

        Seu código é: {paciente.codigo_login}

        ⏳ Expira em 5 minutos.
        """

    enviar_whatsapp(
        clinica,
        paciente.telefone,
        mensagem
    )

def enviar_codigo_whatsapp(telefone, codigo):
    print(f"📲 Enviando WhatsApp para {telefone}")
    print(f"Seu código é: {codigo}")
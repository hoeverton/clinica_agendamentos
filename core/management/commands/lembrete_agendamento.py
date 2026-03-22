from django.core.management.base import BaseCommand
from datetime import timedelta, datetime
from django.utils import timezone
from agendamentos.models import Agendamento, WhatsappLog
from agendamentos.utils import enviar_whatsapp, registrar_envio_whatsapp


class Command(BaseCommand):
    help = 'Envia lembretes de agendamento'

    def handle(self, *args, **kwargs):
        print("🚀 Rodando envio de lembretes...")

        amanha = timezone.now().date() + timedelta(days=1)

        agendamentos = Agendamento.objects.filter(data=amanha)

        print(f"📅 Agendamentos encontrados: {agendamentos.count()}")

        for ag in agendamentos:
            print(f"➡️ Processando: {ag}")

            # 🔒 Evitar envio duplicado
            ja_enviado = WhatsappLog.objects.filter(
                telefone=ag.paciente.telefone,
                tipo="lembrete",
                data__date=timezone.now().date()
            ).exists()

            if ja_enviado:
                print(f"⚠️ Lembrete já enviado para {ag.paciente.telefone}")
                continue

            # 📩 Mensagem
            mensagem = (
                f"⏰ Lembrete!\n\n"
                f"Olá {ag.paciente.nome} 👋\n\n"
                f"Você tem consulta amanhã:\n"
                f"📅 {ag.data.strftime('%d/%m/%Y')}\n"
                f"⏰ {ag.horario.strftime('%H:%M')}\n\n"
                f"Se precisar remarcar, entre em contato."
            )

            # 📲 Enviar WhatsApp
            enviado = enviar_whatsapp(
                ag.paciente.telefone,
                mensagem
            )

            print(f"📲 Enviado para {ag.paciente.telefone}: {enviado}")

            # 🧾 Registrar log
            if enviado:
                registrar_envio_whatsapp(
                    clinica=ag.clinica,
                    telefone=ag.paciente.telefone,
                    tipo="lembrete"
                )

        print("✅ Finalizado envio de lembretes")
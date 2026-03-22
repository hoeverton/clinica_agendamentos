from datetime import datetime, timedelta
from agendamentos.models import Disponibilidade, Agendamento

def buscar_horarios_disponiveis(clinica, profissional, data, duracao):
    dia_semana = data.weekday()

    disponibilidades = Disponibilidade.objects.filter(
        clinica=clinica,
        profissional=profissional,
        dia_semana=dia_semana
    )

    agendamentos = Agendamento.objects.filter(
        profissional=profissional,
        data=data
    )

    horarios_disponiveis = []

    for d in disponibilidades:
        hora = d.hora_inicio

        hora_limite = (
            datetime.combine(datetime.today(), d.hora_fim)
            - timedelta(minutes=duracao)
        ).time()

        while hora <= hora_limite:
            inicio = datetime.combine(datetime.today(), hora)
            fim = inicio + timedelta(minutes=duracao)

            conflito = False

            for ag in agendamentos:
                ag_inicio = datetime.combine(datetime.today(), ag.horario)
                ag_fim = ag_inicio + timedelta(minutes=ag.servico.duracao_minutos)

                if inicio < ag_fim and fim > ag_inicio:
                    conflito = True
                    break

            if not conflito:
                horarios_disponiveis.append(hora)

            hora = (inicio + timedelta(minutes=30)).time()

    return horarios_disponiveis
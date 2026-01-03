from agendamentos.models import Clinica

def clinica_ativa(request):
    if request.user.is_authenticated:
        clinica = Clinica.objects.filter(user=request.user).first()
        return {"clinica": clinica}
    return {}

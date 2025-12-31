from django.shortcuts import render
from agendamentos.models import Clinica

def home(request):
    clinicas = Clinica.objects.all()
    return render(request, "home.html", {"clinicas": clinicas})

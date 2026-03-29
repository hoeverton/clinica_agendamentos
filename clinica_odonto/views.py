from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from agendamentos.models import Clinica, Plano
from django.utils.text import slugify
import uuid

def home(request):
    clinicas = Clinica.objects.all()
    return render(request, "home.html")

def demo(request):
    return render(request, 'demo.html')

def cadastro(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email")
        senha = request.POST.get("senha")

        # cria usuário
        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha
        )

        # gerar slug único
        base_slug = slugify(nome)
        slug = base_slug
        while Clinica.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{str(uuid.uuid4())[:4]}"

        # pegar plano padrão (ajusta conforme seu banco)
        plano = Plano.objects.first()

        # criar clínica
        clinica = Clinica.objects.create(
            user=user,
            nome=nome,
            slug=slug,
            plano=plano
        )

        # login automático
        login(request, user)

        return redirect(f"/{clinica.slug}/dashboard/")

    return render(request, "cadastro.html")
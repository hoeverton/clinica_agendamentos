from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.models import Group
from agendamentos.models import Clinica, Plano, UsuarioClinica
from django.utils.text import slugify
from django.core.mail import send_mail
from django.core.mail import EmailMultiAlternatives
import uuid

def home(request):
    clinicas = Clinica.objects.all()
    return render(request, "home.html")

def demo(request):
    return render(request, 'demo.html')

def cadastro(request):
    if request.method == "POST":
        nome = request.POST.get("nome")
        email = request.POST.get("email").strip()
        senha = request.POST.get("senha")

        if User.objects.filter(username=email).exists():
            return render(request, "cadastro.html", {
                "erro": "Email já cadastrado"
            })

        user = User.objects.create_user(
            username=email,
            email=email,
            password=senha
        )

        # slug
        base_slug = slugify(nome)
        slug = base_slug
        while Clinica.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{uuid.uuid4().hex[:4]}"

        plano = Plano.objects.first()

        clinica = Clinica.objects.create(
            user=user,
            nome=nome,
            slug=slug,
            plano=plano
        )

        # 🔥 RELAÇÃO (igual admin)
        UsuarioClinica.objects.create(
            user=user,
            clinica=clinica
        )

        # 🔥 GRUPO ADMIN
        from django.contrib.auth.models import Group
        grupo_admin = Group.objects.get(name="Administrador")
        user.groups.add(grupo_admin)

        login(request, user)
        subject = 'Bem-vindo ao Agenda Fácil Odonto 🦷'

        html_content = f"""
        <h2>Bem-vindo, {nome} 👋</h2>

        <p>Sua clínica foi criada com sucesso!</p>

        <p>
        <a href="https://agendafacilodonto.com.br/clinica/login"
        style="background:#28a745;color:#fff;padding:12px 20px;text-decoration:none;border-radius:5px;">
        Acessar Dashboard
        </a>
        </p>

        <p>Qualquer dúvida estamos à disposição 🚀</p>
        """

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body='Bem-vindo ao sistema!',
                from_email=None,
                to=[email],
            )

            msg.attach_alternative(html_content, "text/html")
            msg.send()

        except Exception as e:
            print("Erro ao enviar email:", e)

        
        return redirect("clinica_dashboard")

    return render(request, "cadastro.html")
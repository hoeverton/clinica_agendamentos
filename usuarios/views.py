from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from agendamentos.models import UsuarioClinica


# 🔒 verifica se é admin da clínica
def is_admin(user):
    return user.groups.filter(name="Admin").exists()


# 📋 LISTAR USUÁRIOS DA CLÍNICA
@login_required
def usuarios_list(request):
    if not is_admin(request.user):
        return HttpResponseForbidden()

    clinica = request.user.usuarioclinica.clinica

    usuarios = UsuarioClinica.objects.filter(clinica=clinica)

    return render(request, 'usuarios/list.html', {
        'usuarios': usuarios
    })


# ➕ CRIAR USUÁRIO
@login_required
def usuario_create(request):
    if not is_admin(request.user):
        return HttpResponseForbidden()

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        grupo_nome = request.POST.get('grupo')

        # cria usuário
        user = User.objects.create_user(
            username=username,
            password=password
        )

        # vincula clínica
        clinica = request.user.usuarioclinica.clinica

        UsuarioClinica.objects.create(
            user=user,
            clinica=clinica
        )

        # adiciona ao grupo
        grupo, _ = Group.objects.get_or_create(name=grupo_nome)
        user.groups.add(grupo)

        return redirect('usuarios_list')

    grupos = Group.objects.all()

    return render(request, 'usuarios/create.html', {
        'grupos': grupos
    })


# ✏️ EDITAR USUÁRIO
@login_required
def usuario_update(request, user_id):
    if not is_admin(request.user):
        return HttpResponseForbidden()

    usuario = get_object_or_404(User, id=user_id)
    usuario_clinica = get_object_or_404(UsuarioClinica, user=usuario)

    # 🔒 garante que pertence à mesma clínica
    if usuario_clinica.clinica != request.user.usuarioclinica.clinica:
        return HttpResponseForbidden()

    if request.method == 'POST':
        usuario.username = request.POST.get('username')

        grupo_nome = request.POST.get('grupo')
        grupo, _ = Group.objects.get_or_create(name=grupo_nome)

        usuario.groups.clear()
        usuario.groups.add(grupo)

        usuario.save()

        return redirect('usuarios_list')

    grupos = Group.objects.all()

    return render(request, 'usuarios/update.html', {
        'usuario': usuario,
        'grupos': grupos
    })


# ❌ EXCLUIR USUÁRIO
@login_required
def usuario_delete(request, user_id):
    if not is_admin(request.user):
        return HttpResponseForbidden()

    usuario = get_object_or_404(User, id=user_id)
    usuario_clinica = get_object_or_404(UsuarioClinica, user=usuario)

    # 🔒 garante mesma clínica
    if usuario_clinica.clinica != request.user.usuarioclinica.clinica:
        return HttpResponseForbidden()

    usuario.delete()

    return redirect('usuarios_list')

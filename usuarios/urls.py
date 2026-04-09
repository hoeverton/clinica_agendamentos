from django.urls import path
from . import views

urlpatterns = [
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
    path('usuarios/novo/', views.usuario_create, name='usuario_create'),
    path('usuarios/<int:user_id>/editar/', views.usuario_update, name='usuario_update'),
    path('usuarios/<int:user_id>/deletar/', views.usuario_delete, name='usuario_delete'),
    path('usuarios/', views.usuarios_list, name='usuarios_list'),
]
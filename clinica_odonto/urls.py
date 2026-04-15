from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from .views import home, demo, cadastro


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', home),
    path('demo/', demo, name='demo'),
    path('cadastro/',cadastro, name='cadastro'),
    path("clinica/", include("clinica.urls")),   
    path("agendamentos/", include("agendamentos.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("paciente/", include("pacientes.urls")),    
    path('api/', include('whatsapp.urls')),
    path("whatsapp/", include("whatsapp.urls")),    
    path(
    'recuperar-senha/',
    auth_views.PasswordResetView.as_view(        
        html_email_template_name='registration/password_reset_email.html'
    ),
    name='password_reset'
),
    path('recuperar-senha/enviado/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/concluido/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('', include('usuarios.urls')),

]


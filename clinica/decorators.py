from django.http import HttpResponse
from clinica.services.plano_service import PlanoService

def plano_required(funcao_plano):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            clinica = request.user.clinica

            if not funcao_plano(clinica):
                return HttpResponse("Seu plano não permite essa ação")

            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator
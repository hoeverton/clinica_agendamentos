from functools import wraps
from django.shortcuts import redirect

def paciente_logado(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("paciente_id"):
            return redirect("solicitar_codigo")
        return view_func(request, *args, **kwargs)
    return wrapper
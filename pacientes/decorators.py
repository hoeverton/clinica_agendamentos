from functools import wraps
from django.shortcuts import redirect



def paciente_logado(view_func):
    print("******** DEF PACIENTE_LOGADO DECORATRS ******************")

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):

        if not request.session.get("paciente_id"):
            return redirect("solicitar_codigo")

        # repassa TODOS argumentos para a view
        return view_func(request, *args, **kwargs)

    return wrapper
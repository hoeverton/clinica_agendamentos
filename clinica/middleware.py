from clinica.utils import get_clinica


class ClinicaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            request.clinica = get_clinica(request.user)
        else:
            request.clinica = None

        return self.get_response(request)
def get_clinica(user):
    relacao = user.usuarioclinica_set.first()
    return relacao.clinica if relacao else None
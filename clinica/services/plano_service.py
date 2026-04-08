class PlanoService:

    @staticmethod
    def pode_usar_prontuario(clinica):
        return clinica.plano.pode_usar_prontuario

    @staticmethod
    def pode_ver_relatorios(clinica):
        return clinica.plano.tem_relatorios

    @staticmethod
    def pode_criar_profissional(clinica):
        if clinica.plano.max_profissionais is None:
            return True
        return clinica.profissionais.count() < clinica.plano.max_profissionais
    
    @staticmethod
    def pode_criar_servico(clinica):
        if clinica.plano.max_servicos is None:
            return True
        return clinica.servicos.count() < clinica.plano.max_servicos
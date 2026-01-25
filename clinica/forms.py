from django import forms
from agendamentos.models import Profissional, Servico

class ProfissionalForm(forms.ModelForm):
    class Meta:
        model = Profissional
        fields = ['nome', 'especialidade', 'servicos']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'especialidade': forms.TextInput(attrs={'class': 'form-control'}),
            'servicos': forms.CheckboxSelectMultiple(),
        }

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'duracao_minutos', 'preco']

        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        labels = {
            'preco': 'Preço',
            'duracao_minutos': 'Duração (minutos)',
        }
from django import forms

from .models import Campeonato, Jogador, Partida, Time


class CampoData(forms.DateInput):
    """Mostra o seletor de data do navegador."""
    input_type = 'date'

    def __init__(self):
        super().__init__(format='%Y-%m-%d')


class CampeonatoForm(forms.ModelForm):
    class Meta:
        model = Campeonato
        fields = ['nome', 'modalidade', 'data_inicio']
        widgets = {'data_inicio': CampoData()}

    def __init__(self, *args, usuario, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.usuario = usuario

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        repetido = Campeonato.objects.filter(
            usuario=self.instance.usuario, nome__iexact=nome,
        ).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError('Você já tem um campeonato com este nome.')
        return nome


class TimeForm(forms.ModelForm):
    class Meta:
        model = Time
        fields = ['nome', 'responsavel', 'telefone']

    def __init__(self, *args, campeonato, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.campeonato = campeonato

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        repetido = Time.objects.filter(
            campeonato=self.instance.campeonato, nome__iexact=nome,
        ).exclude(pk=self.instance.pk)
        if repetido.exists():
            raise forms.ValidationError('Este campeonato já tem um time com este nome.')
        return nome


class JogadorForm(forms.ModelForm):
    class Meta:
        model = Jogador
        fields = ['nome', 'numero', 'posicao']

    def __init__(self, *args, time, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.time = time
        self.fields['posicao'].choices = [('', 'Não informada')] + Jogador.Posicao.choices

    def outros_do_time(self):
        return Jogador.objects.filter(time=self.instance.time).exclude(pk=self.instance.pk)

    def clean_nome(self):
        nome = self.cleaned_data['nome'].strip()
        if self.outros_do_time().filter(nome__iexact=nome).exists():
            raise forms.ValidationError('Este time já tem um jogador com este nome.')
        return nome

    def clean_numero(self):
        numero = self.cleaned_data['numero']
        if numero is not None and self.outros_do_time().filter(numero=numero).exists():
            raise forms.ValidationError('Este número de camisa já está em uso no time.')
        return numero


class PartidaForm(forms.ModelForm):
    class Meta:
        model = Partida
        fields = ['mandante', 'visitante', 'data', 'local', 'gols_mandante', 'gols_visitante']
        widgets = {'data': CampoData()}
        help_texts = {
            'gols_mandante': 'Deixe o placar em branco se a partida ainda não aconteceu.',
        }

    def __init__(self, *args, campeonato, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.campeonato = campeonato
        # Só os times deste campeonato podem ser escolhidos.
        for campo in ('mandante', 'visitante'):
            self.fields[campo].queryset = campeonato.times.all()
            self.fields[campo].empty_label = 'Selecione um time'

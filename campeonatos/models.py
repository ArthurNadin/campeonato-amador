from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import F, Q


class Campeonato(models.Model):
    class Modalidade(models.TextChoices):
        FUTEBOL = 'futebol', 'Futebol de campo'
        SOCIETY = 'society', 'Futebol society'
        FUTSAL = 'futsal', 'Futsal'
        OUTRA = 'outra', 'Outra'

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='campeonatos',
    )
    nome = models.CharField('nome', max_length=120)
    modalidade = models.CharField(
        'modalidade',
        max_length=10,
        choices=Modalidade.choices,
        default=Modalidade.FUTEBOL,
    )
    data_inicio = models.DateField('data de início')
    criado_em = models.DateTimeField('criado em', auto_now_add=True)

    class Meta:
        ordering = ['-data_inicio', 'nome']
        constraints = [
            models.UniqueConstraint(
                fields=['usuario', 'nome'],
                name='campeonato_unico_por_usuario',
            ),
        ]

    def __str__(self):
        return self.nome

    def classificacao(self):
        """Tabela de pontos corridos: 3 pontos por vitória e 1 por empate.

        Desempate: pontos, vitórias, saldo de gols, gols pró e nome.
        Só as partidas com placar lançado entram na conta.
        """
        tabela = {
            time.pk: {
                'time': time, 'pontos': 0, 'jogos': 0, 'vitorias': 0,
                'empates': 0, 'derrotas': 0, 'gols_pro': 0, 'gols_contra': 0,
            }
            for time in self.times.all()
        }

        for partida in self.partidas.filter(gols_mandante__isnull=False):
            lados = [
                (partida.mandante_id, partida.gols_mandante, partida.gols_visitante),
                (partida.visitante_id, partida.gols_visitante, partida.gols_mandante),
            ]
            for time_id, feitos, sofridos in lados:
                linha = tabela[time_id]
                linha['jogos'] += 1
                linha['gols_pro'] += feitos
                linha['gols_contra'] += sofridos
                if feitos > sofridos:
                    linha['vitorias'] += 1
                    linha['pontos'] += 3
                elif feitos == sofridos:
                    linha['empates'] += 1
                    linha['pontos'] += 1
                else:
                    linha['derrotas'] += 1

        for linha in tabela.values():
            linha['saldo'] = linha['gols_pro'] - linha['gols_contra']

        return sorted(
            tabela.values(),
            key=lambda l: (
                -l['pontos'], -l['vitorias'], -l['saldo'], -l['gols_pro'],
                l['time'].nome.lower(),
            ),
        )


class Time(models.Model):
    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.CASCADE,
        related_name='times',
    )
    nome = models.CharField('nome', max_length=80)
    responsavel = models.CharField('responsável', max_length=120, blank=True)
    telefone = models.CharField('telefone', max_length=20, blank=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.UniqueConstraint(
                fields=['campeonato', 'nome'],
                name='time_unico_por_campeonato',
            ),
        ]

    def __str__(self):
        return self.nome


class Jogador(models.Model):
    class Posicao(models.TextChoices):
        GOLEIRO = 'goleiro', 'Goleiro'
        DEFENSOR = 'defensor', 'Defensor'
        MEIO_CAMPO = 'meio', 'Meio-campo'
        ATACANTE = 'atacante', 'Atacante'

    time = models.ForeignKey(
        Time,
        on_delete=models.CASCADE,
        related_name='jogadores',
    )
    nome = models.CharField('nome', max_length=120)
    numero = models.PositiveSmallIntegerField(
        'número da camisa',
        null=True,
        blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(99)],
    )
    posicao = models.CharField(
        'posição',
        max_length=10,
        choices=Posicao.choices,
        blank=True,
    )

    class Meta:
        ordering = ['nome']
        verbose_name_plural = 'jogadores'
        constraints = [
            models.UniqueConstraint(
                fields=['time', 'nome'],
                name='jogador_unico_por_time',
            ),
        ]

    def __str__(self):
        return self.nome


class Partida(models.Model):
    campeonato = models.ForeignKey(
        Campeonato,
        on_delete=models.CASCADE,
        related_name='partidas',
    )
    mandante = models.ForeignKey(
        Time,
        on_delete=models.CASCADE,
        related_name='partidas_como_mandante',
        verbose_name='mandante',
    )
    visitante = models.ForeignKey(
        Time,
        on_delete=models.CASCADE,
        related_name='partidas_como_visitante',
        verbose_name='visitante',
    )
    data = models.DateField('data')
    local = models.CharField('local', max_length=120, blank=True)
    # Placar vazio significa que a partida ainda não foi realizada.
    gols_mandante = models.PositiveSmallIntegerField('gols do mandante', null=True, blank=True)
    gols_visitante = models.PositiveSmallIntegerField('gols do visitante', null=True, blank=True)

    class Meta:
        ordering = ['data', 'id']
        constraints = [
            models.CheckConstraint(
                condition=~Q(mandante=F('visitante')),
                name='partida_times_diferentes',
                violation_error_message='Um time não pode jogar contra ele mesmo.',
            ),
            models.CheckConstraint(
                condition=(
                    Q(gols_mandante__isnull=True, gols_visitante__isnull=True)
                    | Q(gols_mandante__isnull=False, gols_visitante__isnull=False)
                ),
                name='partida_placar_completo',
                violation_error_message='Informe os gols dos dois times ou deixe os dois em branco.',
            ),
        ]

    def __str__(self):
        return f'{self.mandante} x {self.visitante}'

    @property
    def realizada(self):
        return self.gols_mandante is not None

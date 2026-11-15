from django.contrib import admin

from .models import Campeonato, Jogador, Partida, Time


@admin.register(Jogador)
class JogadorAdmin(admin.ModelAdmin):
    list_display = ('nome', 'numero', 'posicao', 'time')
    search_fields = ('nome',)


@admin.register(Campeonato)
class CampeonatoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'modalidade', 'data_inicio', 'usuario')
    list_filter = ('modalidade',)
    search_fields = ('nome',)


@admin.register(Time)
class TimeAdmin(admin.ModelAdmin):
    list_display = ('nome', 'campeonato', 'responsavel')
    search_fields = ('nome',)


@admin.register(Partida)
class PartidaAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'campeonato', 'data', 'gols_mandante', 'gols_visitante')
    list_filter = ('campeonato',)

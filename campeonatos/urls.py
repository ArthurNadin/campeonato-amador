from django.urls import path

from . import views

urlpatterns = [
    path('', views.CampeonatoLista.as_view(), name='inicio'),

    path('campeonatos/novo/', views.CampeonatoCriar.as_view(), name='campeonato_criar'),
    path('campeonatos/<int:pk>/', views.CampeonatoDetalhe.as_view(), name='campeonato_detalhe'),
    path('campeonatos/<int:pk>/editar/', views.CampeonatoEditar.as_view(), name='campeonato_editar'),
    path('campeonatos/<int:pk>/excluir/', views.CampeonatoExcluir.as_view(), name='campeonato_excluir'),

    path('campeonatos/<int:campeonato_pk>/times/novo/', views.TimeCriar.as_view(), name='time_criar'),
    path('times/<int:pk>/', views.TimeDetalhe.as_view(), name='time_detalhe'),
    path('times/<int:pk>/editar/', views.TimeEditar.as_view(), name='time_editar'),
    path('times/<int:pk>/excluir/', views.TimeExcluir.as_view(), name='time_excluir'),

    path('times/<int:time_pk>/jogadores/novo/', views.JogadorCriar.as_view(), name='jogador_criar'),
    path('jogadores/<int:pk>/editar/', views.JogadorEditar.as_view(), name='jogador_editar'),
    path('jogadores/<int:pk>/excluir/', views.JogadorExcluir.as_view(), name='jogador_excluir'),

    path('campeonatos/<int:campeonato_pk>/partidas/nova/', views.PartidaCriar.as_view(), name='partida_criar'),
    path('partidas/<int:pk>/editar/', views.PartidaEditar.as_view(), name='partida_editar'),
    path('partidas/<int:pk>/excluir/', views.PartidaExcluir.as_view(), name='partida_excluir'),
]

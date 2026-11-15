from datetime import date

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Campeonato, Jogador, Partida, Time

SENHA = 'senha-de-teste-123'


def criar_campeonato(usuario, nome='Copa do Bairro'):
    return Campeonato.objects.create(
        usuario=usuario, nome=nome, modalidade='society', data_inicio=date(2026, 3, 1),
    )


class AcessoTests(TestCase):
    def test_paginas_exigem_login(self):
        for url in [reverse('inicio'), reverse('campeonato_criar'), reverse('time_criar', args=[1])]:
            resposta = self.client.get(url)
            self.assertRedirects(resposta, f"{reverse('login')}?next={url}")

    def test_cadastro_cria_usuario_e_faz_login(self):
        resposta = self.client.post(reverse('cadastro'), {
            'username': 'ana', 'email': 'ana@exemplo.com',
            'password1': SENHA, 'password2': SENHA,
        })
        self.assertRedirects(resposta, reverse('inicio'))
        self.assertTrue(User.objects.filter(username='ana').exists())
        self.assertEqual(self.client.get(reverse('inicio')).status_code, 200)

    def test_login_com_senha_errada_nao_entra(self):
        User.objects.create_user('ana', password=SENHA)
        resposta = self.client.post(reverse('login'), {'username': 'ana', 'password': 'errada'})
        self.assertEqual(resposta.status_code, 200)
        self.assertNotIn('_auth_user_id', self.client.session)


class FormulariosTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password=SENHA)
        self.client.login(username='ana', password=SENHA)
        self.copa = criar_campeonato(self.ana)
        self.leoes = Time.objects.create(campeonato=self.copa, nome='Leões')
        self.tigres = Time.objects.create(campeonato=self.copa, nome='Tigres')
        self.detalhe = reverse('campeonato_detalhe', args=[self.copa.pk])

    def dados_partida(self, **extra):
        dados = {
            'mandante': self.leoes.pk, 'visitante': self.tigres.pk,
            'data': '2026-03-08', 'local': 'Campo da praça',
            'gols_mandante': '', 'gols_visitante': '',
        }
        dados.update(extra)
        return dados

    def test_formulario_grava_campeonato_do_usuario(self):
        resposta = self.client.post(reverse('campeonato_criar'), {
            'nome': 'Torneio de Verão', 'modalidade': 'futsal', 'data_inicio': '2026-01-10',
        })
        campeonato = Campeonato.objects.get(nome='Torneio de Verão')
        self.assertRedirects(resposta, reverse('campeonato_detalhe', args=[campeonato.pk]))
        self.assertEqual(campeonato.usuario, self.ana)

    def test_nome_de_campeonato_repetido_e_recusado(self):
        resposta = self.client.post(reverse('campeonato_criar'), {
            'nome': 'copa do bairro', 'modalidade': 'futsal', 'data_inicio': '2026-01-10',
        })
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Campeonato.objects.count(), 1)

    def test_time_entra_no_campeonato_da_url(self):
        resposta = self.client.post(reverse('time_criar', args=[self.copa.pk]), {'nome': 'Águias'})
        self.assertRedirects(resposta, self.detalhe)
        self.assertEqual(Time.objects.get(nome='Águias').campeonato, self.copa)

    def test_nome_de_time_repetido_no_campeonato_e_recusado(self):
        resposta = self.client.post(reverse('time_criar', args=[self.copa.pk]), {'nome': 'leões'})
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.copa.times.count(), 2)

    def test_partida_agendada_sem_placar(self):
        resposta = self.client.post(reverse('partida_criar', args=[self.copa.pk]), self.dados_partida())
        self.assertRedirects(resposta, self.detalhe)
        self.assertFalse(Partida.objects.get().realizada)

    def test_lancar_placar_em_partida_agendada(self):
        partida = Partida.objects.create(
            campeonato=self.copa, mandante=self.leoes, visitante=self.tigres, data=date(2026, 3, 8),
        )
        resposta = self.client.post(
            reverse('partida_editar', args=[partida.pk]),
            self.dados_partida(gols_mandante='2', gols_visitante='1'),
        )
        self.assertRedirects(resposta, self.detalhe)
        partida.refresh_from_db()
        self.assertEqual((partida.gols_mandante, partida.gols_visitante), (2, 1))

    def test_time_nao_joga_contra_ele_mesmo(self):
        resposta = self.client.post(
            reverse('partida_criar', args=[self.copa.pk]),
            self.dados_partida(visitante=self.leoes.pk),
        )
        self.assertContains(resposta, 'Um time não pode jogar contra ele mesmo.')
        self.assertEqual(Partida.objects.count(), 0)

    def test_placar_pela_metade_e_recusado(self):
        resposta = self.client.post(
            reverse('partida_criar', args=[self.copa.pk]),
            self.dados_partida(gols_mandante='2'),
        )
        self.assertContains(resposta, 'Informe os gols dos dois times')
        self.assertEqual(Partida.objects.count(), 0)

    def test_partida_nao_aceita_time_de_outro_campeonato(self):
        outro = criar_campeonato(self.ana, nome='Outro torneio')
        intruso = Time.objects.create(campeonato=outro, nome='Intruso')
        resposta = self.client.post(
            reverse('partida_criar', args=[self.copa.pk]),
            self.dados_partida(visitante=intruso.pk),
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Partida.objects.count(), 0)

    def test_excluir_time_remove_as_partidas_dele(self):
        Partida.objects.create(
            campeonato=self.copa, mandante=self.leoes, visitante=self.tigres, data=date(2026, 3, 8),
        )
        resposta = self.client.post(reverse('time_excluir', args=[self.tigres.pk]))
        self.assertRedirects(resposta, self.detalhe)
        self.assertEqual(Partida.objects.count(), 0)


class JogadoresTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user('ana', password=SENHA)
        self.client.login(username='ana', password=SENHA)
        self.leoes = Time.objects.create(campeonato=criar_campeonato(self.ana), nome='Leões')
        self.pagina_do_time = reverse('time_detalhe', args=[self.leoes.pk])
        self.novo = reverse('jogador_criar', args=[self.leoes.pk])

    def test_jogador_entra_no_time_da_url_e_aparece_no_elenco(self):
        resposta = self.client.post(self.novo, {'nome': 'Rafael', 'numero': '10', 'posicao': 'meio'})
        self.assertRedirects(resposta, self.pagina_do_time)
        self.assertEqual(Jogador.objects.get(nome='Rafael').time, self.leoes)
        self.assertContains(self.client.get(self.pagina_do_time), 'Rafael')

    def test_numero_e_posicao_sao_opcionais(self):
        self.client.post(self.novo, {'nome': 'Rafael', 'numero': '', 'posicao': ''})
        jogador = Jogador.objects.get()
        self.assertIsNone(jogador.numero)
        self.assertEqual(jogador.posicao, '')

    def test_nome_ou_camisa_repetidos_no_time_sao_recusados(self):
        Jogador.objects.create(time=self.leoes, nome='Rafael', numero=10)
        mesmo_nome = self.client.post(self.novo, {'nome': 'rafael', 'numero': '7'})
        mesma_camisa = self.client.post(self.novo, {'nome': 'Bruno', 'numero': '10'})
        self.assertContains(mesmo_nome, 'já tem um jogador com este nome')
        self.assertContains(mesma_camisa, 'já está em uso no time')
        self.assertEqual(Jogador.objects.count(), 1)

    def test_mesma_camisa_em_times_diferentes_e_aceita(self):
        tigres = Time.objects.create(campeonato=self.leoes.campeonato, nome='Tigres')
        Jogador.objects.create(time=tigres, nome='Bruno', numero=10)
        self.client.post(self.novo, {'nome': 'Rafael', 'numero': '10'})
        self.assertEqual(self.leoes.jogadores.count(), 1)

    def test_camisa_fora_de_1_a_99_e_recusada(self):
        for numero in ['0', '100']:
            self.client.post(self.novo, {'nome': 'Rafael', 'numero': numero})
        self.assertEqual(Jogador.objects.count(), 0)

    def test_editar_jogador_mantendo_o_proprio_nome_e_numero(self):
        jogador = Jogador.objects.create(time=self.leoes, nome='Rafael', numero=10)
        resposta = self.client.post(
            reverse('jogador_editar', args=[jogador.pk]),
            {'nome': 'Rafael', 'numero': '10', 'posicao': 'atacante'},
        )
        self.assertRedirects(resposta, self.pagina_do_time)
        jogador.refresh_from_db()
        self.assertEqual(jogador.posicao, 'atacante')

    def test_excluir_jogador(self):
        jogador = Jogador.objects.create(time=self.leoes, nome='Rafael')
        resposta = self.client.post(reverse('jogador_excluir', args=[jogador.pk]))
        self.assertRedirects(resposta, self.pagina_do_time)
        self.assertEqual(Jogador.objects.count(), 0)

    def test_usuario_nao_mexe_em_jogador_de_outro(self):
        bia = User.objects.create_user('bia', password=SENHA)
        time_da_bia = Time.objects.create(campeonato=criar_campeonato(bia), nome='Time da Bia')
        jogador_da_bia = Jogador.objects.create(time=time_da_bia, nome='Carla')

        urls = [
            reverse('time_detalhe', args=[time_da_bia.pk]),
            reverse('jogador_criar', args=[time_da_bia.pk]),
            reverse('jogador_editar', args=[jogador_da_bia.pk]),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 404, url)
        self.client.post(reverse('jogador_criar', args=[time_da_bia.pk]), {'nome': 'Invasor'})
        self.client.post(reverse('jogador_excluir', args=[jogador_da_bia.pk]))
        self.assertEqual(list(time_da_bia.jogadores.values_list('nome', flat=True)), ['Carla'])


class PrivacidadeTests(TestCase):
    def test_usuario_nao_acessa_campeonato_de_outro(self):
        ana = User.objects.create_user('ana', password=SENHA)
        bia = User.objects.create_user('bia', password=SENHA)
        copa_da_bia = criar_campeonato(bia, nome='Copa da Bia')
        time_da_bia = Time.objects.create(campeonato=copa_da_bia, nome='Time da Bia')
        self.client.login(username='ana', password=SENHA)

        self.assertNotContains(self.client.get(reverse('inicio')), 'Copa da Bia')
        urls = [
            reverse('campeonato_detalhe', args=[copa_da_bia.pk]),
            reverse('campeonato_editar', args=[copa_da_bia.pk]),
            reverse('time_criar', args=[copa_da_bia.pk]),
            reverse('partida_criar', args=[copa_da_bia.pk]),
            reverse('time_editar', args=[time_da_bia.pk]),
        ]
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 404, url)

        self.client.post(reverse('campeonato_excluir', args=[copa_da_bia.pk]))
        self.client.post(reverse('time_excluir', args=[time_da_bia.pk]))
        self.client.post(reverse('time_criar', args=[copa_da_bia.pk]), {'nome': 'Invasor'})
        self.assertTrue(Campeonato.objects.filter(pk=copa_da_bia.pk).exists())
        self.assertEqual(list(copa_da_bia.times.values_list('nome', flat=True)), ['Time da Bia'])


class ClassificacaoTests(TestCase):
    def setUp(self):
        ana = User.objects.create_user('ana', password=SENHA)
        self.copa = criar_campeonato(ana)
        self.a = Time.objects.create(campeonato=self.copa, nome='Águias')
        self.b = Time.objects.create(campeonato=self.copa, nome='Búfalos')
        self.c = Time.objects.create(campeonato=self.copa, nome='Corujas')

    def jogo(self, mandante, visitante, gols_m=None, gols_v=None):
        Partida.objects.create(
            campeonato=self.copa, mandante=mandante, visitante=visitante,
            data=date(2026, 3, 8), gols_mandante=gols_m, gols_visitante=gols_v,
        )

    def test_pontos_saldo_e_ordem(self):
        self.jogo(self.a, self.b, 2, 0)   # Águias vencem
        self.jogo(self.b, self.c, 1, 1)   # empate
        self.jogo(self.c, self.a, 0, 3)   # Águias vencem
        self.jogo(self.a, self.b)         # agendada: não conta

        tabela = self.copa.classificacao()
        self.assertEqual([l['time'] for l in tabela], [self.a, self.b, self.c])

        aguias, bufalos, corujas = tabela
        self.assertEqual(
            (aguias['pontos'], aguias['jogos'], aguias['vitorias'], aguias['saldo']),
            (6, 2, 2, 5),
        )
        # Búfalos e Corujas têm 1 ponto; o saldo (-2 contra -3) desempata.
        self.assertEqual((bufalos['pontos'], bufalos['saldo']), (1, -2))
        self.assertEqual((corujas['pontos'], corujas['saldo']), (1, -3))

    def test_time_sem_jogos_aparece_zerado(self):
        tabela = self.copa.classificacao()
        self.assertEqual(len(tabela), 3)
        self.assertTrue(all(l['pontos'] == 0 and l['jogos'] == 0 for l in tabela))

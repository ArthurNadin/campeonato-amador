from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from .forms import CampeonatoForm, JogadorForm, PartidaForm, TimeForm
from .models import Campeonato, Jogador, Partida, Time


class MensagemMixin:
    """Mostra um aviso de sucesso depois de salvar ou excluir."""
    mensagem = ''

    def form_valid(self, form):
        messages.success(self.request, self.mensagem)
        return super().form_valid(form)


# ---------- Campeonatos ----------

class CampeonatoDoUsuarioMixin(LoginRequiredMixin):
    def get_queryset(self):
        return Campeonato.objects.filter(usuario=self.request.user)


class CampeonatoFormMixin(MensagemMixin):
    form_class = CampeonatoForm
    template_name = 'campeonatos/formulario.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['usuario'] = self.request.user
        return kwargs

    def get_success_url(self):
        return reverse('campeonato_detalhe', args=[self.object.pk])


class CampeonatoLista(CampeonatoDoUsuarioMixin, ListView):
    template_name = 'campeonatos/inicio.html'
    context_object_name = 'campeonatos'

    def get_queryset(self):
        return super().get_queryset().annotate(
            total_times=Count('times', distinct=True),
            total_partidas=Count('partidas', distinct=True),
        )


class CampeonatoDetalhe(CampeonatoDoUsuarioMixin, DetailView):
    template_name = 'campeonatos/campeonato_detalhe.html'
    context_object_name = 'campeonato'

    def get_context_data(self, **kwargs):
        contexto = super().get_context_data(**kwargs)
        contexto['classificacao'] = self.object.classificacao()
        contexto['total_jogadores'] = Jogador.objects.filter(time__campeonato=self.object).count()
        contexto['partidas'] = self.object.partidas.select_related('mandante', 'visitante')
        return contexto


class CampeonatoCriar(LoginRequiredMixin, CampeonatoFormMixin, CreateView):
    mensagem = 'Campeonato criado.'
    extra_context = {'titulo': 'Novo campeonato', 'voltar_url': reverse_lazy('inicio')}


class CampeonatoEditar(CampeonatoDoUsuarioMixin, CampeonatoFormMixin, UpdateView):
    mensagem = 'Campeonato atualizado.'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            titulo='Editar campeonato',
            voltar_url=reverse('campeonato_detalhe', args=[self.object.pk]),
            **kwargs,
        )


class CampeonatoExcluir(CampeonatoDoUsuarioMixin, MensagemMixin, DeleteView):
    template_name = 'campeonatos/confirmar_exclusao.html'
    success_url = reverse_lazy('inicio')
    mensagem = 'Campeonato excluído.'

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            aviso='Os times e as partidas deste campeonato também serão excluídos.',
            voltar_url=reverse('campeonato_detalhe', args=[self.object.pk]),
            **kwargs,
        )


# ---------- Times e partidas (sempre dentro de um campeonato) ----------

class ItemDoCampeonatoMixin(LoginRequiredMixin, MensagemMixin):
    """Base das telas de time e partida.

    Ao criar, o campeonato vem da URL; ao editar ou excluir, vem do próprio
    registro. Nos dois casos ele precisa pertencer ao usuário logado.
    """
    titulo = ''
    aviso = ''

    def get_queryset(self):
        return self.model.objects.filter(campeonato__usuario=self.request.user)

    def get_campeonato(self):
        if 'campeonato_pk' in self.kwargs:
            return get_object_or_404(
                Campeonato, pk=self.kwargs['campeonato_pk'], usuario=self.request.user,
            )
        return self.object.campeonato

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # A tela de exclusão usa um formulário vazio, que não recebe campeonato.
        if self.form_class in (TimeForm, PartidaForm):
            kwargs['campeonato'] = self.get_campeonato()
        return kwargs

    def get_success_url(self):
        return reverse('campeonato_detalhe', args=[self.get_campeonato_pk()])

    def get_campeonato_pk(self):
        return self.kwargs.get('campeonato_pk') or self.object.campeonato_id

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            titulo=self.titulo,
            aviso=self.aviso,
            voltar_url=reverse('campeonato_detalhe', args=[self.get_campeonato_pk()]),
            **kwargs,
        )


class TimeCriar(ItemDoCampeonatoMixin, CreateView):
    model = Time
    form_class = TimeForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Novo time'
    mensagem = 'Time cadastrado.'


class TimeEditar(ItemDoCampeonatoMixin, UpdateView):
    model = Time
    form_class = TimeForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Editar time'
    mensagem = 'Time atualizado.'


class TimeExcluir(ItemDoCampeonatoMixin, DeleteView):
    model = Time
    template_name = 'campeonatos/confirmar_exclusao.html'
    aviso = 'Os jogadores e as partidas deste time também serão excluídos.'
    mensagem = 'Time excluído.'


class TimeDetalhe(LoginRequiredMixin, DetailView):
    """Página do time, com o elenco."""
    template_name = 'campeonatos/time_detalhe.html'
    context_object_name = 'time'

    def get_queryset(self):
        return Time.objects.filter(
            campeonato__usuario=self.request.user
        ).select_related('campeonato')


# ---------- Jogadores (sempre dentro de um time) ----------

class JogadorMixin(LoginRequiredMixin, MensagemMixin):
    """Ao criar, o time vem da URL; ao editar ou excluir, vem do jogador."""
    model = Jogador
    titulo = ''

    def get_queryset(self):
        return Jogador.objects.filter(time__campeonato__usuario=self.request.user)

    def get_time(self):
        if 'time_pk' in self.kwargs:
            return get_object_or_404(
                Time, pk=self.kwargs['time_pk'], campeonato__usuario=self.request.user,
            )
        return self.object.time

    def get_time_pk(self):
        return self.kwargs.get('time_pk') or self.object.time_id

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.form_class is JogadorForm:
            kwargs['time'] = self.get_time()
        return kwargs

    def get_success_url(self):
        return reverse('time_detalhe', args=[self.get_time_pk()])

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            titulo=self.titulo,
            voltar_url=reverse('time_detalhe', args=[self.get_time_pk()]),
            **kwargs,
        )


class JogadorCriar(JogadorMixin, CreateView):
    form_class = JogadorForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Novo jogador'
    mensagem = 'Jogador cadastrado.'


class JogadorEditar(JogadorMixin, UpdateView):
    form_class = JogadorForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Editar jogador'
    mensagem = 'Jogador atualizado.'


class JogadorExcluir(JogadorMixin, DeleteView):
    template_name = 'campeonatos/confirmar_exclusao.html'
    mensagem = 'Jogador excluído.'


class PartidaCriar(ItemDoCampeonatoMixin, CreateView):
    model = Partida
    form_class = PartidaForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Nova partida'
    mensagem = 'Partida registrada.'


class PartidaEditar(ItemDoCampeonatoMixin, UpdateView):
    model = Partida
    form_class = PartidaForm
    template_name = 'campeonatos/formulario.html'
    titulo = 'Editar partida'
    mensagem = 'Partida atualizada.'


class PartidaExcluir(ItemDoCampeonatoMixin, DeleteView):
    model = Partida
    template_name = 'campeonatos/confirmar_exclusao.html'
    mensagem = 'Partida excluída.'

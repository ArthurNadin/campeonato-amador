from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import CadastroForm


def cadastro(request):
    """Cria uma conta nova e já deixa o usuário logado."""
    if request.user.is_authenticated:
        return redirect('inicio')

    form = CadastroForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        usuario = form.save()
        login(request, usuario)
        messages.success(request, 'Conta criada com sucesso. Bem-vindo(a)!')
        return redirect('inicio')

    return render(request, 'contas/cadastro.html', {'form': form})

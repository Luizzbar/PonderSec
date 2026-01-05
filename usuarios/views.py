from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login as auth_login
from django.utils import timezone
import random

from .models import ChatSession, Message, UserQuota, BlindComparison, LLMConfig

from .services import DualEngine


def cadastro(request):
    if request.method == "GET":
        return render(request, 'cadastro.html')
    else:
        username = request.POST.get('username')
        email = request.POST.get('email')
        senha = request.POST.get('password')
        senha_confirm = request.POST.get('password_confirm')

        if senha != senha_confirm:
            return HttpResponse("As senhas não coincidem!")
    
        if User.objects.filter(username=username).exists():
            return HttpResponse("Usuário já existe")

        user = User.objects.create_user(username=username, email=email, password=senha)
        user.save()
        return HttpResponse("Usuário cadastrado com sucesso! Vá para o login.")

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    else:
        username = request.POST.get('username')
        senha = request.POST.get('password')
        user = authenticate(request, username=username, password=senha)

        if user is not None:
            auth_login(request, user)
            return redirect('tela_inicial') 
        else:
            return HttpResponse("Credenciais inválidas!")


@login_required
def tela_inicial(request):
    # Mostra histórico de sessões
    conversas = ChatSession.objects.filter(user=request.user).order_by('-updated_at')
    
    # Cria a quota do usuário se não existir
    quota, _ = UserQuota.objects.get_or_create(user=request.user)
    
    contexto = {
        'conversas': conversas,
        'usuario': request.user,
        'restantes': quota.perguntas_restantes
    }
    return render(request, 'tela_inicial.html', contexto)

@login_required
def iniciar_chat(request):
    """Cria nova sessão e vai para a arena"""
    nova_sessao = ChatSession.objects.create(
        user=request.user,
        title=f"Arena {timezone.now().strftime('%H:%M')}"
    )
    return redirect('sala_chat', session_id=nova_sessao.id)

@login_required
def sala_chat(request, session_id):
    sessao = get_object_or_404(ChatSession, id=session_id, user=request.user)
    
    # Verifica Quota
    quota, _ = UserQuota.objects.get_or_create(user=request.user)

    # Verifica se existe um duelo pendente (usuário ainda não escolheu quem ganhou)
    duelo_pendente = BlindComparison.objects.filter(session=sessao, winner__isnull=True).last()

    if request.method == "POST":
        
        # Usuário enviou uma pergunta (Novo Duelo)
        if 'mensagem' in request.POST:
            texto = request.POST.get('mensagem')
            
            if quota.perguntas_restantes <= 0:
                return render(request, 'chat.html', {
                    'sessao': sessao, 
                    'erro': 'Limite de 20 perguntas atingido!'
                })

            # Salva msg do usuário
            Message.objects.create(session=sessao, role='user', content=texto)
            
            try:
                # CHAVES DE API (Seu Hardcode)
                key_groq = "chave_groq_aqui" 
                key_gemini = "chave_gemini_aqui"
                
                engine = DualEngine(key_groq, key_gemini)
                resultados = engine.gerar_duelo(texto)
                
                # --- PROTEÇÃO CONTRA TRAVAMENTO ---
                
                # 1. Se deu erro explícito
                if "erro" in resultados:
                    Message.objects.create(session=sessao, role='system', content=f"Erro na API: {resultados['erro']}")
                
                # 2. Se as respostas vieram vazias (Isso evita a tela branca)
                elif not resultados['gpt'] or not resultados['gemini']:
                    Message.objects.create(session=sessao, role='system', content="Erro: Uma das IAs retornou resposta vazia. Tente novamente.")
                
                # 3. Se tudo deu certo, AÍ SIM cria o duelo
                else:
                    gpt_is_a = random.choice([True, False])
                    
                    BlindComparison.objects.create(
                        session=sessao,
                        prompt_usuario=texto,
                        resposta_gpt=resultados['gpt'],
                        resposta_gemini=resultados['gemini'],
                        gpt_is_option_a=gpt_is_a
                    )
                    
                    quota.perguntas_restantes -= 1
                    quota.save()
                    
            except Exception as e:
                print(f"ERRO FATAL VIEW: {e}")
                Message.objects.create(session=sessao, role='system', content=f"Erro Interno: {e}")

            return redirect('sala_chat', session_id=sessao.id)

        # Usuário escolheu o vencedor (A ou B)
        elif 'escolha' in request.POST:
            escolha = request.POST.get('escolha') # 'A' ou 'B'
            duelo_id = request.POST.get('duelo_id')
            duelo = get_object_or_404(BlindComparison, id=duelo_id)
            
            # Lógica para descobrir quem era A e quem era B
            vencedor = ''
            texto_vencedor = ''
            
            if duelo.gpt_is_option_a:
                # Se A era DeepSeek
                vencedor = 'DeepSeek' if escolha == 'A' else 'Gemini'
                texto_vencedor = duelo.resposta_gpt if escolha == 'A' else duelo.resposta_gemini
            else:
                # Se A era Gemini
                vencedor = 'Gemini' if escolha == 'A' else 'DeepSeek'
                texto_vencedor = duelo.resposta_gemini if escolha == 'A' else duelo.resposta_gpt
            
            # Registra o vencedor
            duelo.winner = vencedor
            duelo.save()
            
            # Salva a resposta vencedora no chat visível
            Message.objects.create(
                session=sessao, 
                role='assistant', 
                content=f"🏆 VENCEDOR: {vencedor}\n\n{texto_vencedor}"
            )
            
            return redirect('sala_chat', session_id=sessao.id)

    mensagens = sessao.messages.all().order_by('timestamp')
    
    # Prepara dados do duelo se houver um pendente
    opcoes = None
    if duelo_pendente:
        opcoes = {
            'id': duelo_pendente.id,
            'texto_a': duelo_pendente.resposta_gpt if duelo_pendente.gpt_is_option_a else duelo_pendente.resposta_gemini,
            'texto_b': duelo_pendente.resposta_gemini if duelo_pendente.gpt_is_option_a else duelo_pendente.resposta_gpt
        }

    return render(request, 'chat.html', {
        'sessao': sessao, 
        'mensagens': mensagens,
        'duelo_pendente': opcoes,
        'restantes': quota.perguntas_restantes
    })
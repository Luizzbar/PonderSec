from django.db import models
from django.contrib.auth.models import User

# 1. Configuração da API (Por usuário)
# Aqui o usuário salva a chave dele (OpenAI, Anthropic, etc)
class LLMConfig(models.Model):
    PROVIDERS = [
        ('openai', 'OpenAI (GPT)'),
        ('anthropic', 'Anthropic (Claude)'),
        ('meta', 'Llama (Local/Groq)'),
        ('google', 'Gemini'),
        ('deepseek', 'DeepSeek AI')
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='llm_config')
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='google')
    api_key = models.CharField(max_length=255, help_text="Sua chave de API para invocação")
    model_name = models.CharField(max_length=50, default='gemini', help_text="Ex: gpt-4, claude-3-opus")
    
    # Temperatura define a criatividade (0 = preciso/técnico, 1 = criativo)
    temperature = models.FloatField(default=0.2, help_text="0.0 a 1.0 (Menor é melhor para segurança)")

    def __str__(self):
        return f"Config de {self.user.username} ({self.provider})"

# 2. Sessão de Chat (Uma conversa inteira)
class ChatSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, default="Nova Análise")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.created_at.strftime('%d/%m %H:%M')}"

# 3. Mensagens (O diálogo)
class Message(models.Model):
    ROLES = [
        ('user', 'Usuário (Pentester)'),
        ('assistant', 'IA (PonderSec)'),
        ('system', 'System Prompt'), # Instrução oculta de segurança
    ]

    session = models.ForeignKey(ChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLES)
    content = models.TextField() # O texto da pergunta ou resposta
    
    # Metadados opcionais (ex: tokens gastos, latência)
    tokens_used = models.IntegerField(default=0, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.role}: {self.content[:30]}..."
    
class UserQuota(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='quota')
    perguntas_restantes = models.IntegerField(default=20)
    
    def __str__(self):
        return f"{self.user.username}: {self.perguntas_restantes} restantes"

class BlindComparison(models.Model):
    session = models.ForeignKey('ChatSession', on_delete=models.CASCADE)
    prompt_usuario = models.TextField()
    
    # As respostas geradas
    resposta_gpt = models.TextField()
    resposta_gemini = models.TextField()
    
    # Qual foi mostrada como "Opção A" na tela? (para garantir cegueira)
    # Se True, A = GPT. Se False, A = Gemini.
    gpt_is_option_a = models.BooleanField()
    
    # O Vencedor escolhido pelo usuário
    winner = models.CharField(max_length=20, null=True, blank=True) # 'gpt' ou 'gemini'
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Duelo em {self.session.id} - Vencedor: {self.winner}"
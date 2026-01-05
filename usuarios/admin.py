from django.contrib import admin
from .models import ChatSession, Message, LLMConfig, BlindComparison, UserQuota

# Configuração da LLM (API Keys)
@admin.register(LLMConfig)
class LLMConfigAdmin(admin.ModelAdmin):
    list_display = ('user', 'provider', 'model_name')
    search_fields = ('user__username',)

# Visualização das Mensagens dentro do Chat
class MessageInline(admin.TabularInline):
    model = Message
    extra = 0
    readonly_fields = ('timestamp', 'role')

@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    inlines = [MessageInline] # Mostra as mensagens ao abrir a sessão


@admin.register(BlindComparison)
class BlindComparisonAdmin(admin.ModelAdmin):
    # Mostra colunas úteis na lista
    list_display = ('id', 'session', 'get_user', 'winner', 'timestamp')
    list_filter = ('winner',) # Filtro lateral para ver quem ganha mais (GPT ou Gemini)
    
    # Função auxiliar para mostrar o usuário dono da sessão
    def get_user(self, obj):
        return obj.session.user.username
    get_user.short_description = 'Usuário'

@admin.register(UserQuota)
class UserQuotaAdmin(admin.ModelAdmin):
    list_display = ('user', 'perguntas_restantes')
    search_fields = ('user__username',)
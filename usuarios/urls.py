from django.urls import path
from . import views

urlpatterns = [
    path('cadastro/', views.cadastro, name="cadastro"),
    path('', views.login, name="login"),
    path('tela-inicial/', views.tela_inicial, name="tela_inicial"),
    path('chat/novo/', views.iniciar_chat, name='iniciar_chat'),
    path('chat/<int:session_id>/', views.sala_chat, name='sala_chat'), # Se usar UUID mude <int> para <uuid>

]
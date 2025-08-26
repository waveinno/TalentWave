from django.urls import path
from .views import AdvancedAIAgentChatView, AIAgentHistoryView

urlpatterns = [
     path("chat/", AdvancedAIAgentChatView.as_view(), name="ai_agent_chat"),
    path("history/", AIAgentHistoryView.as_view(), name="ai_agent_history"),
]

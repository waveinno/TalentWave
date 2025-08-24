from django.urls import path
from .views import chat, widget_page

urlpatterns = [
    path("chat", chat, name="ai_agent_chat"),
    path("widget", widget_page, name="ai_agent_widget")
]

from django.contrib import admin
from .models import AIAgentLog


@admin.register(AIAgentLog)
class AIAgentLogAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "short_q", "short_a")
    search_fields = ("question", "answer", "user__username")


    def short_q(self, obj):
        return (obj.question or "")[:80]


    def short_a(self, obj):
        return (obj.answer or "")[:80]
from django.db import models
from django.conf import settings

class AiConversation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AiMessage(models.Model):
    ROLE_CHOICES = [("user","user"),("assistant","assistant"),("tool","tool")]
    conversation = models.ForeignKey(AiConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

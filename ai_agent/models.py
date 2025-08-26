from django.db import models
from django.conf import settings


class AIAgentLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at']


    def __str__(self):
        return f"{self.user} @ {self.created_at:%Y-%m-%d %H:%M}: {self.question[:40]}..."
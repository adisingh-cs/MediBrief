from django.db import models
from django.contrib.auth.models import User

class ChatEntry(models.Model):
    user_input = models.TextField()
    response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='chats')

    def __str__(self):
        return f"Chat at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

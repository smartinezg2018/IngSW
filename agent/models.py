from django.db import models

# Create your models here.
class Conversation(models.Model):
    """
    Groups all interactions with a specific user on X.
    """
    user_id = models.CharField(max_length=50, db_index=True)  # X's internal user ID
    conversation_id = models.CharField(max_length=50, blank=True, null=True)  # X thread ID
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.user_id} ({self.created_at.date()})"


class Message(models.Model):
    """
    Each individual message in the conversation (user or agent).
    """
    SENDER_CHOICES = [
        ("user", "User"),
        ("agent", "Agent"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    tweet_id = models.CharField(max_length=50)  # X tweet/comment ID
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    timestamp = models.DateTimeField()
from django.db import models

# Create your models here.


    
class Post(models.Model):
    """
    Represents an X post (tweet) that we're tracking
    """
    post_id = models.CharField(max_length=50, unique=True)  # ID from X API
    text = models.TextField(blank=True, null=True)
    author_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Post {self.post_id}"

class Offer(models.Model):
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    
    

class Comment(models.Model):
    """
    Represents a reply (comment) to a Post
    """
    comment_id = models.CharField(max_length=50, unique=True) 
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    author_id = models.CharField(max_length=50)  # maps to user ID in X
    in_reply_to_user_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField()
    

    def __str__(self):
        return f"Comment {self.comment_id} on Post {self.post.post_id}"
    
    
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
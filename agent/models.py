from django.db import models

# Create your models here.



class Post(models.Model):
    """
    Represents an X post (tweet) that we're tracking.
    """
    post_id = models.CharField(max_length=50, unique=True)  # ID from X API
    text = models.TextField(blank=True, null=True)
    author_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Post {self.post_id}"


class Comment(models.Model):
    """
    Represents a reply (comment) to a Post.
    """
    comment_id = models.CharField(max_length=50, unique=True) 
    post = models.ForeignKey(Post, related_name="comments", on_delete=models.CASCADE)
    text = models.TextField()
    author_id = models.CharField(max_length=50)  # maps to user ID in X
    in_reply_to_user_id = models.CharField(max_length=50, blank=True, null=True)
    created_at = models.DateTimeField()
    

    def __str__(self):
        return f"Comment {self.comment_id} on Post {self.post.post_id}"
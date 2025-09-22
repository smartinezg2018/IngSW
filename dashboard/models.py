from django.db import models
from django.utils import timezone
# Create your models here.


    
class Post(models.Model):
    """
    Represents an X post (tweet) that we're tracking
    """
    
    caption = models.TextField(blank=True, null=True)
    date = models.DateTimeField(default=timezone.now, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    image = models.ImageField(upload_to="uploads/", blank=True, null=True)
    media_id = models.CharField(max_length=100,blank=True, null=True,unique=True)
    

    

class Comment(models.Model):
    
    comment_id = models.CharField(max_length=50, unique=True) 
    post = models.ForeignKey(
        Post, 
        related_name="comments", 
        to_field="media_id",   # <-- link to media_id instead of id
        db_column="media_id",  # optional: column name in DB
        on_delete=models.CASCADE
    )
    text = models.TextField()
    user_id = models.CharField(max_length=50,blank=True, null=True)
    username = models.CharField(max_length=50,blank=True, null=True)  
    

    def __str__(self):
        return f"Comment {self.comment_id} on Post {self.post.media_id}"
    
    

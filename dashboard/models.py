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
    

class JobOffer(models.Model):
    """
    Job offer entity for loading and listing vacancies.
    """

    STATUS_CHOICES = (
        ("active", "Active"),
        ("closed", "Closed"),
    )

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    salary = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    posted_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-posted_date", "-created_at"]
        unique_together = ("title", "company", "posted_date")

    def __str__(self) -> str:
        d = self.posted_date.isoformat() if self.posted_date else "n/a"
        return f"{self.title} @ {self.company} ({d})"


class AgentConfig(models.Model):
    """
    Agent configuration singleton - controls agent activation/deactivation.
    Only one instance should exist.
    """
    
    name = models.CharField(max_length=100, default="IngSW Agent")
    is_active = models.BooleanField(default=False, help_text="Whether the agent is currently active")
    description = models.TextField(blank=True, null=True, help_text="Description of what this agent does")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Agent Configuration"
        verbose_name_plural = "Agent Configuration"

    def __str__(self):
        status = "Active" if self.is_active else "Inactive"
        return f"{self.name} - {status}"

    @classmethod
    def get_instance(cls):
        """Get or create the singleton instance"""
        obj, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'name': 'IngSW Agent',
                'description': 'Agent for automated Instagram posting and job offer management',
                'is_active': False
            }
        )
        return obj

    def save(self, *args, **kwargs):
        # Ensure only one instance exists
        self.pk = 1
        super().save(*args, **kwargs)



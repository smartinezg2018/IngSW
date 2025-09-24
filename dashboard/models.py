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
    # --- ya existentes ---
    comment_id = models.CharField(max_length=100, unique=True)
    post = models.ForeignKey(
        "Post",
        to_field="media_id",        # importante: FK por media_id como tienes
        db_column="media_id",
        on_delete=models.CASCADE,
        related_name="comments",
    )
    text = models.TextField(blank=True, default="")
    user_id = models.CharField(max_length=100, blank=True, default="")
    username = models.CharField(max_length=150, blank=True, default="")

    # --- nuevos campos NLP ---
    class Sentiment(models.TextChoices):
        POS = "pos", "Positive"
        NEU = "neu", "Neutral"
        NEG = "neg", "Negative"

    class Status(models.TextChoices):
        NEW = "new", "New"                    # recién creado, sin etiquetar aún o sin revisar
        REVIEW = "review", "Needs Review"     # interés medio (0.4-0.8) u otros casos
        NEEDS_REPLY = "needs_reply", "Needs Reply"  # interés >= threshold y no contestado
        REPLIED = "replied", "Replied"        # contestado manual/externo
        NOT_INTERESTED = "not_interested", "Not Interested"  # bajo interés
        AUTO_REPLIED = "auto_replied", "Auto Replied"        # reservado para futuro LLM

    sentiment = models.CharField(
        max_length=8,
        choices=Sentiment.choices,
        blank=True,
        default=""
    )
    sentiment_score = models.FloatField(null=True, blank=True)  # confianza del modelo de sentimiento
    interest_score = models.FloatField(null=True, blank=True)   # 0..1 “qué tanto parece interesado en la vacante”
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True
    )
    last_scored_at = models.DateTimeField(null=True, blank=True)  # cuándo se etiquetó por última vez

    def mark_status_from_interest(self, threshold: float = 0.8):
        # No sobreescribas si ya está REPLIED o AUTO_REPLIED (respeta flujo humano/LLM)
        if self.status in [self.Status.REPLIED, self.Status.AUTO_REPLIED]:
            return
        if self.interest_score is None:
            self.status = self.Status.REVIEW
            return
        if self.interest_score >= threshold:
            self.status = self.Status.NEEDS_REPLY
        elif self.interest_score >= 0.4:
            self.status = self.Status.REVIEW
        else:
            self.status = self.Status.NOT_INTERESTED

    def touch_scored(self):
        self.last_scored_at = timezone.now()

    def __str__(self):
        return f"Comment {self.comment_id} on Post {self.post.media_id}"
    
    

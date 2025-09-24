# dashboard/management/commands/tag_comments.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from django.conf import settings
from dashboard.models import Comment
from dashboard.services.nlp import analyze_comment

class Command(BaseCommand):
    help = "Etiqueta comentarios con sentimiento e interés, y actualiza status según umbral."

    def add_arguments(self, parser):
        parser.add_argument(
            "--since-days",
            type=int,
            default=None,
            help="Solo comentarios creados/actualizados en los últimos N días.",
        )
        parser.add_argument(
            "--only-missing",
            action="store_true",
            help="Procesa solo comentarios sin interest_score o sentiment.",
        )
        parser.add_argument(
            "--post",
            type=str,
            default=None,
            help="Filtra por un media_id específico.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="No guarda cambios; solo muestra qué haría.",
        )

    def handle(self, *args, **opts):
        qs = Comment.objects.all()

        if opts["since_days"]:
            since = timezone.now() - timedelta(days=opts["since_days"])
            qs = qs.filter(Q(last_scored_at__isnull=True) | Q(last_scored_at__gte=since))

        if opts["only_missing"]:
            qs = qs.filter(Q(interest_score__isnull=True) | Q(sentiment__exact="") | Q(sentiment_score__isnull=True))

        if opts["post"]:
            qs = qs.filter(post__media_id=opts["post"])

        count = 0
        threshold = getattr(settings, "COMMENT_INTEREST_THRESHOLD", 0.8)

        self.stdout.write(self.style.NOTICE(f"Procesando {qs.count()} comentarios... umbral={threshold}"))
        for c in qs.iterator():
            label, s_score, i_score, lang = analyze_comment(c.text)
            msg = f"[{c.comment_id}] lang={lang} sentiment={label}({s_score}) interest={i_score}"

            if not opts["dry_run"]:
                c.sentiment = label
                c.sentiment_score = s_score
                c.interest_score = i_score
                c.mark_status_from_interest(threshold=threshold)
                c.touch_scored()
                c.save(update_fields=["sentiment", "sentiment_score", "interest_score", "status", "last_scored_at"])
                self.stdout.write(self.style.SUCCESS(msg + f" -> status={c.status}"))
            else:
                self.stdout.write(msg)
            count += 1

        self.stdout.write(self.style.SUCCESS(f"Listo. Comentarios procesados: {count}"))

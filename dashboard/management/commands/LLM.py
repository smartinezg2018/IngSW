# import requests
from django.conf import settings
import requests
from django.core.management.base import BaseCommand
from dashboard.models import Post, Comment
import requests
import time

long_access_token = settings.LONG_ACCESS_TOKEN
api_key = settings.GOOGLE_API

def instagram_response(response,comment_id):
    url = f"https://graph.facebook.com/v2.0/{comment_id}/replies"
    payload = {
        "message" : response,
        "access_token" : long_access_token
    }

    response = requests.post(url, params=payload)
    data = response.json()
    return data



def generate_hr_response(post_description, comment_text, max_retries=6):
    prompt = f"""
    Actúa como reclutador de RRHH profesional y amable.

    Contexto del puesto: {post_description}
    Pregunta/comentario: {comment_text}

    Instrucciones:
    - Responde de forma útil, cordial y CORTA
    - Si no tienes información suficiente en el contexto, responde "No tengo contexto suficiente para responder esa pregunta específica"
    - Basa tu respuesta únicamente en la información del puesto proporcionada
    - Máximo 2-3 oraciones
    """

    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    for attempt in range(max_retries):
        try:
            response = requests.post(
                api_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Validación más robusta de la respuesta
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    text = candidate["content"]["parts"][0].get("text", "")
                    if text.strip():
                        return text
            
            # Si llegamos aquí, la respuesta no tiene el formato esperado
            print(f"Respuesta inesperada en intento {attempt + 1}: {result}")
            
        except requests.exceptions.Timeout:
            print(f"Timeout en intento {attempt + 1}")
            
        except requests.exceptions.HTTPError as e:
            print(f"Error HTTP en intento {attempt + 1}: {e}")
            # Si es un error 429 (rate limit), espera más tiempo
            if response.status_code == 429:
                wait_time = (attempt + 1) * 5
                print(f"Rate limit alcanzado. Esperando {wait_time} segundos...")
                time.sleep(wait_time)
            elif response.status_code >= 500:
                # Error del servidor, reintenta
                time.sleep(2 ** attempt)  # Backoff exponencial
            else:
                # Error del cliente (400s), no reintentar
                break
                
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión en intento {attempt + 1}: {e}")
            
        except (KeyError, IndexError) as e:
            print(f"Error parseando respuesta en intento {attempt + 1}: {e}")
        
        # Espera antes de reintentar (backoff exponencial)
        if attempt < max_retries - 1:
            wait_time = 2 ** attempt  # 1s, 2s, 4s...
            print(f"Reintentando en {wait_time} segundos...")
            time.sleep(wait_time)
    
    # Si todos los intentos fallan
    return "Lo siento, no puedo responder en este momento. Por favor, intenta nuevamente más tarde."


# Usage:
# result = generate_hr_response("Software Engineer job", "What's the salary?")
# if result['success']:
#     print(result['response'])
# else:
#     print(f"Error: {result['error']}")




class Command(BaseCommand):
    help = 'Process comments that need reply'

    def handle(self, *args, **options):
        self.stdout.write("Starting to process comments needing reply...")
        self.print_comments_needing_reply()
        self.stdout.write(self.style.SUCCESS("Successfully processed comments needing reply"))

    def print_comments_needing_reply(self):
        """
        For each post, filters and prints information about comments 
        that have status 'needs_reply'
        """
        # Get all posts
        posts = Post.objects.all()
        
        if not posts.exists():
            self.stdout.write(self.style.WARNING("No posts found in the database."))
            return
        
        total_comments_needing_reply = 0
        
        for post in posts:
            # Filter comments for this post that need reply
            comments_needing_reply = post.comments.filter(
                status=Comment.Status.NEEDS_REPLY
            )
            
            # Only print if there are comments needing reply
            if comments_needing_reply.exists():
                count = comments_needing_reply.count()
                total_comments_needing_reply += count
                
                self.stdout.write(f"\n--- POST: {post.media_id} ---")
                self.stdout.write(f"Caption: {post.caption[:100]}..." if post.caption else "No caption")
                self.stdout.write(f"Date: {post.date}")
                self.stdout.write(f"Comments needing reply: {count}")
                self.stdout.write("-" * 50)
                
                for comment in comments_needing_reply:
                   response = generate_hr_response(post.description,comment.text)
                   instagram_response(response,comment.comment_id)
                   print(response)
                   comment.status = comment.Status.REVIEW
                   comment.save()
        
        if total_comments_needing_reply == 0:
            self.stdout.write(self.style.WARNING("No comments needing reply found."))
        else:
            self.stdout.write(f"\nTotal comments needing reply: {total_comments_needing_reply}")

    def get_comments_needing_reply(self):
        """
        Returns a dictionary with posts and their comments needing reply
        """
        result = {}
        posts = Post.objects.all()
        
        for post in posts:
            comments_needing_reply = post.comments.filter(
                status=Comment.Status.NEEDS_REPLY
            )
            
            
            if comments_needing_reply.exists():
                result[post.media_id] = {
                    'post': post,
                    'comments': list(comments_needing_reply)
                }
                
        
        return result
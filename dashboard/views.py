from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from django.core.management import call_command
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render
from dotenv import load_dotenv
from pathlib import Path
import json

from dashboard.models import Post, Comment
from .models import Post
from django.db.models import Count

import time
import http.server
import datetime
import socketserver
import threading
import subprocess
import time
import json
import requests

import http.server
import socketserver
import threading
import subprocess
import time
import requests
from urllib.parse import urljoin
from django.conf import settings
import os
import json



def post_instagram(post):
    """
    Post an image to Instagram using Facebook Graph API.
    
    Args:
        post: Post object with image, caption, and media_id attributes
    
    Returns:
        bool: True if successful, False otherwise
    """
    httpd = None
    ngrok = None
    thread = None
    
    try:
        # Start HTTP Server
        PORT = 8080
        Handler = http.server.SimpleHTTPRequestHandler
        httpd = socketserver.TCPServer(("", PORT), Handler)
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        print(f"HTTP server started on port {PORT}")
        
        # Start ngrok with proper configuration
        ngrok_command = ["ngrok", "http", str(PORT), "--log=stdout"]
        ngrok = subprocess.Popen(
            ngrok_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print("Ngrok process started")
        
        # Check if ngrok is actually running
        time.sleep(2)
        if ngrok.poll() is not None:
            # Process has terminated
            stdout, stderr = ngrok.communicate()
            raise Exception(f"Ngrok failed to start. stdout: {stdout}, stderr: {stderr}")
        
        # Get ngrok public URL with retry logic
        public_url = get_ngrok_url(max_retries=15, delay=2)
        print(f"Ngrok public URL: {public_url}")
        
        # Construct image URL
        image_url = urljoin(public_url, post.image.url.lstrip('/'))
        print(f"Image URL: {image_url}")
        
        caption = post.caption
        
        # Step 1: Create media container
        creation_id = create_media_container(image_url, caption)
        print(f"Media container created with ID: {creation_id}")
        time.sleep(2)

        # Step 2: Publish the media
        publish_success = publish_media(creation_id)
        
        if not publish_success:
            print("Failed to publish media")
            return False
        
        print("Media published successfully")
        
        # Step 3: Wait for media to be available
        time.sleep(3)
        
        # Step 4: Retrieve and save the published media ID
        published_id = get_published_media_id(caption)
        
        if published_id:
            post.media_id = published_id
            post.save()
            print(f"Post saved with media_id: {published_id}")
            return True
        else:
            print("Could not retrieve published media ID")
            return False
            
    except Exception as e:
        print(f"Error posting to Instagram: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Cleanup resources
        print("Cleaning up resources...")
        
        if ngrok:
            try:
                ngrok.terminate()
                ngrok.wait(timeout=5)
                print("Ngrok terminated")
            except Exception as e:
                print(f"Error terminating ngrok: {e}")
                try:
                    ngrok.kill()
                except:
                    pass
        
        if httpd:
            try:
                httpd.shutdown()
                print("HTTP server shut down")
            except Exception as e:
                print(f"Error shutting down HTTP server: {e}")


def check_ngrok_installed():
    """Check if ngrok is installed and accessible."""
    try:
        result = subprocess.run(
            ["ngrok", "version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        print(f"Ngrok version: {result.stdout.strip()}")
        return True
    except FileNotFoundError:
        print("ERROR: ngrok is not installed or not in PATH")
        print("Install ngrok from: https://ngrok.com/download")
        return False
    except Exception as e:
        print(f"Error checking ngrok: {e}")
        return False


def get_ngrok_url(max_retries=15, delay=2):
    """
    Retrieve the ngrok public URL with retry logic.
    
    Args:
        max_retries: Maximum number of retry attempts
        delay: Delay in seconds between retries
    
    Returns:
        str: The ngrok public URL
    
    Raises:
        Exception: If unable to get ngrok URL after max retries
    """
    # First check if ngrok is installed
    if not check_ngrok_installed():
        raise Exception("Ngrok is not properly installed")
    
    for attempt in range(max_retries):
        try:
            resp = requests.get("http://localhost:4040/api/tunnels", timeout=5)
            resp.raise_for_status()
            
            data = resp.json()
            tunnels = data.get("tunnels", [])
            
            if tunnels and len(tunnels) > 0:
                public_url = tunnels[0].get("public_url")
                if public_url:
                    # Prefer https URL
                    for tunnel in tunnels:
                        url = tunnel.get("public_url", "")
                        if url.startswith("https://"):
                            return url
                    return public_url
            
            print(f"Ngrok URL not ready, attempt {attempt + 1}/{max_retries}")
            
        except requests.exceptions.ConnectionError as e:
            print(f"Cannot connect to ngrok API (attempt {attempt + 1}/{max_retries})")
            print("Make sure ngrok is running and its web interface is on port 4040")
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching ngrok URL (attempt {attempt + 1}/{max_retries}): {e}")
        
        time.sleep(delay)
    
    raise Exception(f"Failed to get ngrok URL after {max_retries} attempts. "
                   "Ngrok may not be running or accessible on port 4040.")


def create_media_container(image_url, caption):
    """
    Create an Instagram media container.
    
    Args:
        image_url: URL of the image to post
        caption: Caption for the post
    
    Returns:
        str: Creation ID of the media container
    
    Raises:
        Exception: If the API request fails
    """
    API_VERSION = "v21.0"
    url = f"https://graph.facebook.com/{API_VERSION}/{settings.IG_USER_ID}/media"
    
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": settings.LONG_ACCESS_TOKEN,
    }
    
    response = requests.post(url, params=payload, timeout=30)
    data = response.json()
    
    print(f"Create container response: {data}")
    
    # Check for errors
    if "error" in data:
        error_msg = data["error"].get("message", "Unknown error")
        raise Exception(f"Instagram API error (create): {error_msg}")
    
    if "id" not in data:
        raise Exception(f"No creation_id returned from Instagram API: {data}")
    
    return data["id"]


def publish_media(creation_id, retries=5, backoff=2):
    """
    Publish the media container to Instagram with retry logic.

    Args:
        creation_id (str): The creation ID from create_media_container
        retries (int): Number of retry attempts if the API request fails
        backoff (int | float): Base seconds to wait before retrying (increases each attempt)

    Returns:
        bool: True if successful, False otherwise
    """

    API_VERSION = "v21.0"
    url = f"https://graph.facebook.com/{API_VERSION}/{settings.IG_USER_ID}/media_publish"

    payload = {
        "creation_id": creation_id,
        "access_token": settings.LONG_ACCESS_TOKEN
    }

    for attempt in range(1, retries + 1):
        try:
            print(f"Attempt {attempt}/{retries} - Publishing media...")
            
            response = requests.post(url, params=payload, timeout=30)
            data = response.json()
            print(f"Publish response: {data}")

            # Check for API error
            if "error" in data:
                error_msg = data["error"].get("message", "Unknown error")
                print(f"Instagram API error (publish): {error_msg}")

            # Check for missing media ID
            elif "id" not in data:
                print(f"No media ID returned from publish: {data}")
            else:
                return True  # Success!

        except requests.exceptions.RequestException as e:
            print(f"Request error on attempt {attempt}: {e}")

        # If not last attempt, wait before retrying
        if attempt < retries:
            wait_time = backoff * attempt
            print(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    print("Failed to publish media after multiple attempts.")
    return False


def get_published_media_id(caption, max_retries=3):
    """
    Retrieve the media ID of the published post by matching the caption.
    
    Args:
        caption: Caption to match against
        max_retries: Number of retry attempts
    
    Returns:
        str or None: The media ID if found, None otherwise
    """
    API_VERSION = "v21.0"
    url = f"https://graph.facebook.com/{API_VERSION}/{settings.IG_USER_ID}/media"
    
    params = {
        "fields": "id,caption,media_url,timestamp",
        "access_token": settings.LONG_ACCESS_TOKEN,
        "limit": 1,

    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            resp.raise_for_status()
            
            data = resp.json()
            print(f"Retrieved media data: {data}")
            
            if "data" in data and len(data["data"]) > 0:
                # Try to match by caption
                for item in data["data"]:
                    if item.get("caption") == caption:
                        return item["id"]
                
                # If no exact match, return the most recent post
                # (assuming it's the one we just published)
                print("No exact caption match found, returning most recent post")
                return data["data"][0]["id"]
            
            if attempt < max_retries - 1:
                print(f"No media data found, retrying... (attempt {attempt + 1}/{max_retries})")
                time.sleep(2)
                
        except requests.exceptions.RequestException as e:
            print(f"Error retrieving media ID (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                time.sleep(4)
    
    return None
    
    

    





def forms(request):
    # products = Product.objects.all()
    return render(request,"forms.html",{})


@csrf_exempt 
@require_POST
def save_forms(request):
    description = request.POST.get("description")
    caption = request.POST.get("caption")
    image = request.FILES.get("image")

    post = Post.objects.create(
        description=description,
        caption=caption,
        image=image
    )
    post.save()
    post_instagram(post)

    return JsonResponse({"status": "success", "id": post.id})



def update_comments():
    business_discovery_parameters = "id,comments_count"
    other_parameters = "comments{id,text,user,username}"
    fields = business_discovery_parameters + "," + other_parameters

    url = f"https://graph.facebook.com/v21.0/{settings.IG_USER_ID}/media"
    payload = {
        "fields": fields,
        "access_token": settings.LONG_ACCESS_TOKEN,
    }

    response = requests.get(url, params=payload)
    data = response.json()
    print(data)

    # Guardar/actualizar comentarios en la BD
    for post_data in data.get("data", []):
        media_id = post_data["id"]

        try:
            post = Post.objects.get(media_id=media_id)  # busca el Post por media_id
        except Post.DoesNotExist:
            print(f"Post {media_id} not found, skipping.")
            continue

        # Solo si hay comentarios
        if post_data.get("comments") and "data" in post_data["comments"]:
            for c in post_data["comments"]["data"]:
                Comment.objects.update_or_create(
                    comment_id=c["id"],  # unique identifier
                    defaults={
                        "post": post,
                        "text": c.get("text", ""),
                        "user_id": c.get("user", {}).get("id"),
                        "username": c.get("username"),
                    },
                )



def update_comments_view(request):
    if request.method == "POST":
        update_comments()  # call your function directly
        return JsonResponse({"message": "update_comments() executed!"})

def tag_comments_view(request):
    if request.method == "POST":
        call_command("tag_comments")
        return JsonResponse({"message": "call_command('tag_comments') executed!"})

def llm_view(request):
    if request.method == "POST":
        call_command("LLM")
        return JsonResponse({"message": "call_command('LLM') executed!"})
    

def comments(request):
    # update_comments()
    # call_command("tag_comments")
    # call_command("LLM")


    # ---------------------- POSTS: search + sort + pagination ----------------------
    q = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "newest")

    posts_qs = Post.objects.annotate(comment_count=Count("comments"))

    if q:
        posts_qs = posts_qs.filter(
            Q(media_id__icontains=q)
            | Q(description__icontains=q)
            | Q(caption__icontains=q)
        )

    sort_map = {
        "newest": "-date",
        "oldest": "date",
        "most_comments": "-comment_count",
        "least_comments": "comment_count",
    }
    posts_qs = posts_qs.order_by(sort_map.get(sort, "-date"))

    paginator = Paginator(posts_qs, 10)  # 10 per page
    posts_page = paginator.get_page(request.GET.get("page"))

    # ---------------------- COMMENTS: search + sort + pagination -------------------
    c_q = request.GET.get("c_q", "").strip()             # search by comment id, post id, text
    c_sort = request.GET.get("c_sort", "recent")         # recent/status/post/username/sentiment

    comments_qs = Comment.objects.select_related("post")

    if c_q:
        comments_qs = comments_qs.filter(
            Q(comment_id__icontains=c_q)
            | Q(post__media_id__icontains=c_q)
            | Q(text__icontains=c_q)
        )

    # Extra filter by status value (optional dropdown in template)
    c_status = request.GET.get("c_status", "").strip().lower()

    # Filter comments by a specific status if provided
    if c_status:
        comments_qs = comments_qs.filter(status__iexact=c_status)

    # Sort order
    c_sort_map = {
        "recent": "-last_scored_at",
        "status": "status",
        "post": "post__media_id",
        "username": "username",
        "sentiment": "sentiment",
    }
    comments_qs = comments_qs.order_by(c_sort_map.get(c_sort, "-last_scored_at"))


    comments_paginator = Paginator(comments_qs, 15)
    comments_page = comments_paginator.get_page(request.GET.get("c_page"))

    # ---------------------- Render ----------------------
    return render(
        request,
        "comments.html",
        {
            "posts": posts_page.object_list,
            "posts_page": posts_page,
            "comments": comments_page.object_list,
            "comments_page": comments_page,
            "q": q,
            "sort": sort,
            "c_q": c_q,
            "c_sort": c_sort,
            "c_status": c_status,

        },
    )



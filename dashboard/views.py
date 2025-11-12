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

def post_instagram(post : Post):
    
    PORT = 8080
    Handler = http.server.SimpleHTTPRequestHandler
    httpd = socketserver.TCPServer(("", PORT), Handler)
    thread = threading.Thread(target=httpd.serve_forever)
    thread.start()
    ngrok = subprocess.Popen(["ngrok", "http", str(PORT)], stdout=subprocess.PIPE)
    time.sleep(2)
    resp = requests.get("http://localhost:4040/api/tunnels")
    public_url = resp.json()["tunnels"][0]["public_url"]

    image_url = public_url + f"/{post.image.url}"
    
    print(image_url)
    caption = post.caption

    # creation of the container
    url = f"https://graph.facebook.com/v17.0/{settings.IG_USER_ID}/media"
    
    payload = {
        "image_url" : image_url,
        "caption" : caption,
        "access_token" : settings.LONG_ACCESS_TOKEN,
    }
    
    response = requests.post(url, params=payload)
    data = response.json()
    creation_id = data["id"]

    # publishing the image
    url = f"https://graph.facebook.com/v17.0/{settings.IG_USER_ID}/media_publish"
    payload = {
        "creation_id" : creation_id,
        "access_token" : settings.LONG_ACCESS_TOKEN
    }

    response = requests.post(url, params=payload)
    time.sleep(2)
    
    
    
    # getting the id of the last post
    url = f"https://graph.facebook.com/v17.0/{settings.IG_USER_ID}/media"
    params = {
        "fields": "id,caption,media_url,timestamp",
        "access_token": settings.LONG_ACCESS_TOKEN,
    }
    resp = requests.get(url, params=params)
    
    ngrok.terminate()
    httpd.shutdown()
    
    
    data = resp.json()
    print('data: ',data)

    if "data" in data:
        # Try to match by caption or image URL
        for item in data["data"]:
            if item.get("caption") == post.caption:
                published_id = item["id"]
                print("Recovered media_id:", published_id)
                post.media_id = published_id
                post.save()
                break
    
    

    





def forms(request):
    # products = Product.objects.all()
    return render(request,"forms.html",{})


@csrf_exempt  # For testing only! Use proper CSRF token handling in production
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


def comments(request):
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

    # Ejecuta clasificación/etiquetado (igual que antes, solo aseguramos que ocurra antes de consultar)
    call_command("tag_comments")

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
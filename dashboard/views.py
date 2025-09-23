from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.conf import settings
from dotenv import load_dotenv
from pathlib import Path
import json

from dashboard.models import Post, Comment, JobOffer, AgentConfig
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
import csv
from io import TextIOWrapper, StringIO
from django.db import models

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
        "user_tags" : '[{"username":"mountainbetweenus", "x":0.5, "y":0.5}]',
        "collaborators" : '["mountainbetweenus"]',
        "access_token" : settings.LONG_ACCESS_TOKEN,
    }
    
    response = requests.post(url, params=payload)
    data = response.json()
    print(json.dumps(data, indent=4))
    creation_id = data["id"]
    print(f"creation_id : {creation_id}")

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
    
    ngrok.terminate()
    httpd.shutdown()
    





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
    "access_token" : settings.LONG_ACCESS_TOKEN
    }

    response = requests.get(url, params=payload)
    data = response.json()
    print(data)
    
    for post_data in data['data']:
        media_id = post_data['id']

        try:
            post = Post.objects.get(media_id=media_id)  # get Post by media_id
        except Post.DoesNotExist:
            print(f"Post {media_id} not found, skipping.")
            continue

        # Only if there are comments
        if post_data.get('comments') and 'data' in post_data['comments']:
            for c in post_data['comments']['data']:
                Comment.objects.update_or_create(
                    comment_id=c['id'],   # unique identifier
                    defaults={
                        "post": post,
                        "text": c.get("text", ""),
                        "user_id": c.get("user", {}).get("id"),
                        "username": c.get("username"),
                    }
                )
    
    
    posts = Post.objects.annotate(comment_count=Count('comments')).order_by('-comment_count') 
    return render(request,"comments.html",{"posts": posts})


def jobs_list(request):
    """List all job offers with simple filtering by company or text query."""
    q = request.GET.get("q")
    company = request.GET.get("company")
    offers = JobOffer.objects.all()
    if company:
        offers = offers.filter(company__icontains=company)
    if q:
        offers = offers.filter(models.Q(title__icontains=q) | models.Q(description__icontains=q) | models.Q(location__icontains=q))
    return render(request, "jobs_list.html", {"offers": offers, "q": q or "", "company": company or ""})


@csrf_exempt  # For quick enablement; ideally use CSRF token on the form
def jobs_upload(request):
    """
    Upload a CSV file with headers: title,company,location,description,link,salary,posted_date(YYYY-MM-DD)
    Creates or updates offers based on (title, company, posted_date).
    """
    if request.method == "POST":
        f = request.FILES.get("file")
        if not f:
            return HttpResponse("No file uploaded", status=400)

        # Decode to text
        try:
            text_file = TextIOWrapper(f.file, encoding="utf-8")
            reader = csv.DictReader(text_file)
        except Exception:
            # fallback to reading bytes, then decode
            content = f.read().decode("utf-8", errors="ignore")
            reader = csv.DictReader(StringIO(content))

        created, updated, skipped = 0, 0, 0
        for row in reader:
            title = (row.get("title") or "").strip()
            company = (row.get("company") or "").strip()
            posted_date = (row.get("posted_date") or "").strip()
            if not title or not company:
                skipped += 1
                continue

            defaults = {
                "location": (row.get("location") or "").strip() or None,
                "description": (row.get("description") or "").strip() or None,
                "link": (row.get("link") or "").strip() or None,
                "status": (row.get("status") or "active").strip() or "active",
            }
            # salary
            salary_str = (row.get("salary") or "").replace(",", "").strip()
            if salary_str:
                try:
                    defaults["salary"] = float(salary_str)
                except ValueError:
                    pass
            # posted_date
            if posted_date:
                try:
                    defaults["posted_date"] = datetime.datetime.strptime(posted_date, "%Y-%m-%d").date()
                except ValueError:
                    pass

            obj, was_created = JobOffer.objects.update_or_create(
                title=title, company=company, posted_date=defaults.get("posted_date"), defaults=defaults
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1

        return render(request, "jobs_upload.html", {"created": created, "updated": updated, "skipped": skipped})

    return render(request, "jobs_upload.html")


def agent_status(request):
    """Show current agent status and provide toggle functionality."""
    agent = AgentConfig.get_instance()
    return render(request, "agent_status.html", {"agent": agent})


@csrf_exempt
def agent_toggle(request):
    """Toggle agent activation status."""
    if request.method == "POST":
        agent = AgentConfig.get_instance()
        agent.is_active = not agent.is_active
        agent.save()
        status = "activado" if agent.is_active else "desactivado"
        return JsonResponse({"status": "success", "message": f"Agente {status}", "is_active": agent.is_active})
    
    return JsonResponse({"status": "error", "message": "Método no permitido"}, status=405)

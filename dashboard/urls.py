from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.forms, name='forms'),
    path('save_forms/', views.save_forms, name='save_forms'),
    path('comments/', views.comments, name='comments'),
    
    path('update-comments/', views.update_comments_view, name='update_comments'),
    path('tag-comments/', views.tag_comments_view, name='tag_comments'),
    path('llm/', views.llm_view, name='llm'),

]
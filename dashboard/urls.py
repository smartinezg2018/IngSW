from django.urls import path
from . import views

urlpatterns = [
    path('post/', views.forms, name='forms'),
    path('save_forms/', views.save_forms, name='save_forms'),
    path('comments/', views.comments, name='comments'),
]
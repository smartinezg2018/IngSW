from django.urls import path
from . import views

urlpatterns = [
    path('post/', views.forms, name='forms'),
    path('save_forms/', views.save_forms, name='save_forms'),
    path('comments/', views.comments, name='comments'),
    path('jobs/', views.jobs_list, name='jobs_list'),
    path('jobs/upload/', views.jobs_upload, name='jobs_upload'),
    path('agent/', views.agent_status, name='agent_status'),
    path('agent/toggle/', views.agent_toggle, name='agent_toggle'),
]
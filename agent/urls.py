from django.urls import path
from . import views

urlpatterns = [
    path('agent_status/', views.agent_status, name='agent_status'),
]
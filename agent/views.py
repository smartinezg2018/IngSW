from django.shortcuts import render

# Create your views here.
def agent_status(request):
    """Show current agent status and provide toggle functionality."""
    return render(request, "agent_status.html", {})
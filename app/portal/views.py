from django.shortcuts import render

# Create your views here.
def game_history(request):
    return render(request, "portal/game_history.html")
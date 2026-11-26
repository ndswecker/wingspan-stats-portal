from django.shortcuts import redirect, render

def about(request):
    return render(request, "portal/about/about.html")
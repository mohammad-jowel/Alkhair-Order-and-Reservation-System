from django.shortcuts import render
from django.http import HttpResponse

def login_view(request):
    return HttpResponse("Login page placeholder")

def register_view(request):
    return HttpResponse("Register page placeholder")

def logout_view(request):
    return HttpResponse("Logout placeholder")

def profile_view(request):
    return HttpResponse("Profile placeholder")

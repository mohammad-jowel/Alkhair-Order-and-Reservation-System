from django.shortcuts import render
from django.http import HttpResponse

def menu_list(request):
    return HttpResponse("Menu list placeholder")

def manage_menu(request):
    return HttpResponse("Manage menu placeholder")

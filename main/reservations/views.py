from django.shortcuts import render
from django.http import HttpResponse

def reservation_list(request):
    return HttpResponse("Reservation list placeholder")

def manage_reservations(request):
    return HttpResponse("Manage reservations placeholder")

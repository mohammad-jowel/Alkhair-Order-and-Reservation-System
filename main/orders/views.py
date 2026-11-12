from django.shortcuts import render
from django.http import HttpResponse

def cart_view(request):
    return HttpResponse("Cart placeholder")

def my_orders(request):
    return HttpResponse("My orders placeholder")

def manage_orders(request):
    return HttpResponse("Manage orders placeholder")

def clear_table(request):
    if 'table_id' in request.session:
        del request.session['table_id']
    if 'table_number' in request.session:
        del request.session['table_number']
    return HttpResponse("Table cleared")

from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse

def login_view(request):
    return render(request, 'main/login.html')
    
    # if request.method == 'POST':
    #     phone_number = request.POST.get('phone_number')
    #     name = request.POST.get('name')
    #     # Add your login logic here
    #     return redirect('home')  # Redirect to home page after successful login
    # return render(request, 'login.html')
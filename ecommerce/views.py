from django.shortcuts import render, redirect
from .models import Item
from django.contrib import messages
from .forms import UserSignUpForm


def home(request):
    context = {
        'title': 'Home',
        'items': Item.objects.all()
    }
    return render(request, 'ecommerce/home.html', context)


def about(request):
    return render(request, 'ecommerce/about.html')


def signup(request):
    if request.method == 'POST':
        user_signup_form = UserSignUpForm(request.POST)
        if user_signup_form.is_valid():
            user_signup_form.save()
            messages.success(request, 'Account Created')
            return redirect('ecommerce-home')
    else:
        user_signup_form = UserSignUpForm()
    return render(request, 'ecommerce/signup.html', {'user_signup_form': user_signup_form})


from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout, authenticate, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required

def dashboard_home(request):
	return render(request, 'dashboard/dashboard.html')


@login_required(login_url='dashboard_sign_in')
def dashboard_profile(request):
    return render(request, 'dashboard/profile.html')


def dashboard_sign_in(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        try:
            user = User.objects.get(username=username)
        except:
            print("User does not exist")


        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard_home')
        else:
            print("Username OR password is incorrect")

    context = {}
    return render(request, 'dashboard/sign-in.html', context)


def dashboard_sign_up(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard_home')
    else:
        form = UserCreationForm()

    context = {'form': form}
    return render(request, 'dashboard/sign-up.html', context)


def dashboard_logout(request):
    context = {}
    logout(request)
    return redirect('dashboard_sign_in')
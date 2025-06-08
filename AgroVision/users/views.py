from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib import messages
from .models import UserProfile

# Create your views here.

def signup(request):
    if request.method == 'POST':
        if 'skip' in request.POST:
            # Handle basic signup without profile details
            username = request.POST.get('username')
            phone_number = request.POST.get('phone_number')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')

            if password != password_confirm:
                messages.error(request, 'Passwords do not match!')
                return render(request, 'users/signup.html')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
                return render(request, 'users/signup.html')

            # Create user
            user = User.objects.create_user(username=username, password=password)
            user.userprofile.phone_number = phone_number
            user.userprofile.save()
            
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome to AgroVision!')
            return redirect('community_chat:chat_home')
        else:
            # Handle full profile creation
            username = request.POST.get('username')
            phone_number = request.POST.get('phone_number')
            password = request.POST.get('password')
            password_confirm = request.POST.get('password_confirm')
            
            # Profile fields
            farm_location = request.POST.get('farm_location')
            farming_type = request.POST.get('farming_type')
            preferred_language = request.POST.get('preferred_language', 'English')
            profile_picture = request.FILES.get('profile_picture')

            if password != password_confirm:
                messages.error(request, 'Passwords do not match!')
                return render(request, 'users/signup.html')

            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists!')
                return render(request, 'users/signup.html')

            # Create user with profile
            user = User.objects.create_user(username=username, password=password)
            
            # Update profile
            profile = user.userprofile
            profile.phone_number = phone_number
            profile.farm_location = farm_location
            profile.farming_type = farming_type
            profile.preferred_language = preferred_language
            if profile_picture:
                profile.profile_picture = profile_picture
            profile.save()

            login(request, user)
            messages.success(request, 'Profile created successfully! Welcome to AgroVision!')
            return redirect('community_chat:chat_home')

    return render(request, 'users/signup.html')

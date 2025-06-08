from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
from .models import ChatGroup, Message
from django.db.models import Q
from django.utils import timezone

@login_required
def chat_home(request):
    user_groups = request.user.chat_groups.all()
    public_groups = ChatGroup.objects.filter(is_public=True).exclude(members=request.user)
    context = {
        'user_groups': user_groups,
        'public_groups': public_groups
    }
    return render(request, 'community_chat/chat_home.html', context)

@login_required
def group_chat(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user not in group.members.all() and not group.is_public:
        messages.error(request, "You don't have permission to access this group.")
        return redirect('community_chat:chat_home')
    
    if request.method == 'POST':
        content = request.POST.get('content')
        image = request.FILES.get('image')
        if content or image:
            Message.objects.create(
                group=group,
                sender=request.user,
                content=content,
                image=image
            )
    
    chat_messages = group.messages.all()
    context = {
        'group': group,
        'chat_messages': chat_messages
    }
    return render(request, 'community_chat/group_chat.html', context)

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        is_public = request.POST.get('is_public', 'off') == 'on'
        group_image = request.FILES.get('group_image')
        
        group = ChatGroup.objects.create(
            name=name,
            description=description,
            creator=request.user,
            is_public=is_public,
            group_image=group_image
        )
        group.members.add(request.user)
        messages.success(request, f'Group "{name}" created successfully!')
        return redirect('community_chat:group_chat', group_id=group.id)
    
    return render(request, 'community_chat/create_group.html')

@login_required
def join_group(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user not in group.members.all():
        group.members.add(request.user)
        messages.success(request, f'You have joined the group "{group.name}"')
    return redirect('community_chat:group_chat', group_id=group.id)

@login_required
def leave_group(request, group_id):
    group = get_object_or_404(ChatGroup, id=group_id)
    if request.user in group.members.all():
        group.members.remove(request.user)
        messages.success(request, f'You have left the group "{group.name}"')
    return redirect('community_chat:chat_home')

@login_required
def get_messages(request, group_id):
    """API endpoint for getting new messages"""
    last_message_id = request.GET.get('last_id')
    group = get_object_or_404(ChatGroup, id=group_id)
    
    messages_query = group.messages.all()
    if last_message_id:
        messages_query = messages_query.filter(id__gt=last_message_id)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'sender': msg.sender.username,
        'created_at': msg.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        'image_url': msg.image.url if msg.image else None
    } for msg in messages_query]
    
    return JsonResponse({'messages': messages_data})

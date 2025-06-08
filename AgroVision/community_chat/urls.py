from django.urls import path
from . import views

app_name = 'community_chat'

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path('group/<int:group_id>/', views.group_chat, name='group_chat'),
    path('create/', views.create_group, name='create_group'),
    path('join/<int:group_id>/', views.join_group, name='join_group'),
    path('leave/<int:group_id>/', views.leave_group, name='leave_group'),
    path('api/messages/<int:group_id>/', views.get_messages, name='get_messages'),
] 
"""
URL configuration for agro project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from users import views as user_views
from agrov.views import history
from agrov.views import upload_image, scheme
urlpatterns = [
    path('admin/', admin.site.urls),
    path("",upload_image),
    path("scheme/",scheme),
    path('chat/', include('community_chat.urls', namespace='community_chat')),
    path('signup/', user_views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(template_name='users/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='users/logout.html',
        next_page='login',
        http_method_names=['get', 'post']
    ), name='logout'),
    path('weather/', include('weather.urls')),
    path('treat/',include('treat.urls')),
    path('ai/',include('agrov.urls'),name="ai"),
    path('history/', history, name='history'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

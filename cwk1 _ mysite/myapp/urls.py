"""
URL configuration for cwk1 project.

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
from django.urls import path
from . import views

urlpatterns = [
    path('', views.api_root, name='api_root'),  # Root API endpoint
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('professors/', views.professor_list, name='professor_list'),
    path('module-instances/', views.module_instance_list, name='module_instance_list'),
    path('ratings/', views.rating_list, name='rating_list'),
    path('average/<str:professor_id>/<str:module_code>/', views.average_rating, name='average_rating'),
    path('rate/', views.rate_professor, name='rate_professor'),
]
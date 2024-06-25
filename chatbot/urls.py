# chatbot/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat, name='chat'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('check-auth/', views.check_auth, name='check_auth'),
]
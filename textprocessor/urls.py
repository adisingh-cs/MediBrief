from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('download-pdf/', views.download_pdf, name='download_pdf'),
    path('chat/<int:chat_id>/pdf/', views.download_chat_pdf, name='download_chat_pdf'),
    path('chat/<int:chat_id>/', views.view_chat, name='view_chat'),
    path('chat/<int:chat_id>/edit/', views.edit_chat, name='edit_chat'),
    path('chat/<int:chat_id>/delete/', views.delete_chat, name='delete_chat'),
    path('chat/<int:chat_id>/pdf/', views.download_chat_pdf, name='download_chat_pdf'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
]

"""
URL configuration for spotify_playlist project.

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
from music import views


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('authorize/', views.authorize, name='authorize'),
    path('callback/', views.callback, name='callback'),
    path('create_playlist/', views.create_playlist, name='create_playlist'),
    path('like_songs_from_playlist/', views.like_songs_from_playlist, name='like_songs_from_playlist'),
    path('list_playlists/', views.list_playlists, name='list_playlists'),
    path('search_account/', views.search_account, name='search_account'),
    path('list_account_playlists/', views.list_account_playlists, name='list_account_playlists'),
    path('save_liked_songs/', views.save_liked_songs, name='save_liked_songs'),
]




from django.contrib import admin
from django.urls import path, re_path
from dataexchange import views
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls), 
    path('login/', views.login, name='login'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('message/', views.message, name='message'),
    path('message1/', views.message1, name='message1'),
    path('inbox/', views.inbox, name='inbox'),
    path('voice/', views.voice, name='voice'),
    path('compose/', views.compose, name='compose'),
    path('userview/', views.userview, name='userview'),
    path('feedback/', views.feedback, name='feedback'),
    path('viewfeedback/', views.viewfeedback, name='viewfeedback'),
    path('profile/', views.profile, name='profile'),
    path('editprofile/', views.editprofile, name='editprofile'),
    path('reg/', views.reg, name='reg'),
    path('blindemail/', views.home, name='blind_home'), # Renamed slightly for clarity
    path('search/', views.search, name='search'),
    path('forgot/', views.forgot, name='forgot'),
    path('security/', views.security, name='security'),
    path('newpass/', views.newpass, name='newpass'),
    path('draft/', views.draft, name='draft'),
    path('sent/', views.sent, name='sent'),
    path('logout/', views.logout, name='logout'),
    path('changeimage/', views.changeimage, name='changeimage'),
    path('save/', views.save, name='save'),
    path('draft1/', views.draft1, name='draft1'),
    path('draft2/', views.draft2, name='draft2'),
    path('home/', views.home, name='home_redirect'),
    re_path(r'^.*$', views.home), 
] + staticfiles_urlpatterns()
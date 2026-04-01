"""eyelessdata URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from dataexchange import views
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path('',views.commonhome,name='commonhome'),
    path('admin/', admin.site.urls), 
    path('login/', views.login, name='login'),
    path('message/',views.message,name='message'),
    path('message1/',views.message1,name='message1'),
    path('adminhome/',views.adminhome,name='adminhome'),
    path('userhome/',views.userhome,name='userhome'),
    path('inbox/',views.inbox,name='inbox'),
    path('voice/',views.voice,name='voice'),
    path('compose/',views.compose,name='compose'),
    path('userview/',views.userview,name='userview'),
    path('feedback/',views.feedback,name='feedback'),
    path('viewfeedback/',views.viewfeedback,name='viewfeedback'),
    path('profile/',views.profile,name='profile'),
    path('editprofile/',views.editprofile,name='editprofile'),
    path('reg/',views.reg,name='reg'),
    path('blindemail/',views.commonhome,name='commonhome'),
    path('search/',views.search,name='search'),
    path('forgot/',views.forgot,name='forgot'),
    path('security/',views.security,name='security'),
    path('newpass/',views.newpass,name='newpass'),
    path('draft/',views.draft,name='draft'),
    path('sent/',views.sent,name='sent'),
    path('logout/',views.logout, name='logout'),
    path('changeimage/',views.changeimage,name='changeimage'),
    path('save/',views.save,name='save'),
    path('draft1/',views.draft1,name='draft1'),
    path('draft2/',views.draft2,name='draft2'),
]+staticfiles_urlpatterns()


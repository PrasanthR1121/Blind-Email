from urllib import request

from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout

from django.http import HttpResponse,HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .models import Registration, Message, Feedback

import MySQLdb 
import datetime
import subprocess

@never_cache
def login(request):
    if request.user.is_authenticated or request.session.get('username'):
        if not request.session.get('tab_alert_shown'):
            messages.info(request, "Active session detected. Resuming...")
            request.session['tab_alert_shown'] = True
        return redirect('/dashboard/')

    if request.method == "POST":
        identifier = request.POST.get("uname")
        password = request.POST.get("password")
        next_url = request.GET.get('next')
        
        # 2. Try Admin Authentication
        admin_user = authenticate(request, username=identifier, password=password)
        if admin_user and admin_user.is_superuser:
            auth_login(request, admin_user)
            
            # Clear old messages (like "Logged Out") before adding new ones
            storage = messages.get_messages(request)
            for _ in storage: pass 
            
            request.session['username'] = admin_user.username 
            request.session['tab_alert_shown'] = True
            messages.success(request, f"Welcome, Admin {admin_user.username}")
            return redirect(next_url if next_url else "/dashboard/")

        # 3. Try Regular User Authentication
        try:
            user = Registration.objects.get(email_id=identifier, password=password)
            if user.status == "approved":
                # Clear old messages
                storage = messages.get_messages(request)
                for _ in storage: pass 
                
                request.session['username'] = user.email_id
                request.session['tab_alert_shown'] = True
                messages.success(request, f"Welcome back, {user.name}!")
                return redirect(next_url if next_url else "/dashboard/")
            else:
                messages.warning(request, f"Account {user.status.capitalize()}")
                return redirect('login')

        except Registration.DoesNotExist:
            messages.error(request, "Invalid Credentials")
            return redirect('login')

    return render(request, "login.html")

# Original
# @never_cache
# def dashboard(request):
#     # Determine who is logged in
#     is_admin = request.user.is_authenticated and request.user.is_superuser
#     user_email = request.session.get('username')

#     if not is_admin and not user_email:
#         return redirect('login')

#     if is_admin:
#         # ADMIN DATA: Global platform stats
#         context = {
#             "role": "Admin",
#             "name": request.user.username,
#             "data1": Registration.objects.count(), # Total Users
#             "count1": Message.objects.count(),     # Total Messages
#             "count": Feedback.objects.count(),      # Total Feedback
#             "det": Message.objects.all().order_by('-id')[:3],
#             "feed": Feedback.objects.all().order_by('-id')[:3],
#         }
#     else:
#         # USER DATA: Personal stats only
#         user_obj = Registration.objects.get(email_id=user_email)
#         context = {
#             "role": "User",
#             "name": user_obj.name,
#             "data1": "Active",
#             "count": Message.objects.filter(receiver=user_obj).count(), # Personal Inbox
#             "count1": Message.objects.filter(sender=user_obj).count(),   # Personal Sent
#             "det": Message.objects.filter(receiver=user_obj).order_by('-id')[:3],
#             "data": [user_obj],
#         }

#     return render(request, "dashboard.html", context)

@never_cache
def dashboard(request):

    is_test_admin = True 
    
    if is_test_admin:
        context = {
            "role": "Admin",
            "name": "Prasanth",
            "data1": 150,          # Simulated Total Users
            "count": 4200,         # Simulated Global Emails
            "count1": 15,          # Simulated Pending Feedback
            "det": ["New user registered: Sneha", "Server backup successful", "Feedback received from User101"],
            "feed": [1, 2, 3],     # Just for length check
        }
    else:
        context = {
            "role": "User",
            "name": "Sneha",
            "data1": "Approved",    # Account Status
            "count": 12,            # Personal Inbox
            "count1": 8,             # Personal Sent
            "det": ["Meeting request from HR", "Welcome to Blind Email", "Security Alert: Login from Kerala"],
            "feed": [],             # Empty feed for user
            "data": [{"image": {"name": ""}}] # Empty image list to trigger the initial 'S'
        }
       
    return render(request, "dashboard.html", context)

def reg(request):
    error = ""
    msg = ""

    if request.method == "POST":
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")

        if Registration.objects.filter(email_id=email).exists():
            messages.error(request, "Email already exists")
            return redirect('reg')
        elif Registration.objects.filter(mobile=mobile).exists():
            messages.error(request, "Mobile already exists")
            return redirect('reg')
        else:
            Registration.objects.create(
                name=request.POST.get("name"),
                address=request.POST.get("address"),
                dob=request.POST.get("dob"),
                gender=request.POST.get("gender"),
                email_id=email,
                mobile=mobile,
                password=request.POST.get("password"),
                answer=request.POST.get("answer"),
            )
            messages.success(request, "Registered successfully. Wait for approval.")
            return redirect('reg')

    return render(request, "reg.html", {"error": error, "msg": msg})
      
def forgot(request):
    error = ""

    if request.method == "POST":
        username = request.POST.get("uname")
        mobile = request.POST.get("mobile")

        user = Registration.objects.filter(
            email_id=username,
            mobile=mobile
        ).first()

        if user:
            request.session['reset_user'] = user.email_id
            return redirect("/security/")
        else:
            error = "Invalid email or mobile"

    return render(request, "forgot.html", {"error": error}) 

def security(request):
    error = ""

    if request.method == "POST":
        answer = request.POST.get("answer")
        username = request.session.get("reset_user")

        user = Registration.objects.filter(
            email_id=username,
            answer=answer
        ).first()

        if user:
            return redirect("/newpass/")
        else:
            error = "Wrong answer"

    return render(request, "security.html", {"error": error})

def newpass(request):
    error = ""

    username = request.session.get("reset_user")

    if not username:
        return redirect("/login/")

    if request.method == "POST":
        password = request.POST.get("password")
        cpassword = request.POST.get("cpassword")

        if password == cpassword:
            user = Registration.objects.get(email_id=username)
            user.password = password
            user.save()

            request.session.pop("reset_user", None)
            return redirect("/login/")
        else:
            error = "Password mismatch"

    return render(request, "newpass.html", {"error": error})

def save(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto")
        receiver = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            Message.objects.create(
                sender=user,
                receiver=receiver,
                subject=request.POST.get("subject"),
                content=request.POST.get("content"),
                status="draft"
            )

    return redirect("/draft/")     

def message(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto")
        receiver = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            status = "sent" if "send" in request.POST else "draft"

            Message.objects.create(
                sender=user,
                receiver=receiver,
                subject=request.POST.get("subject"),
                content=request.POST.get("content"),
                status=status
            )

    inbox_preview = Message.objects.filter(
        receiver=user,
        status="sent"
    ).order_by("-id")[:2]

    feed = Feedback.objects.all().order_by("-id")[:3]

    return render(request, "message.html", {
        "messages": inbox_preview,
        "feed": feed
    })

def compose(request):
    if not request.session.get('username'):
        return redirect("/login/")

    msg_id = request.GET.get("count")

    message = Message.objects.filter(id=msg_id).first()

    if not message:
        return redirect("/inbox/")

    request.session['reply_to'] = message.sender.email_id

    if request.method == "POST":
        return redirect("/message1/")

    return render(request, "compose.html", {
        "frm1": message.sender.email_id,
        "sub": message.subject,
        "con": message.content
    })
  
def inbox(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    messages = Message.objects.filter(
        receiver=user,
        status="sent"
    ).order_by("-id")

    count_inbox = messages.count()
    count_draft = Message.objects.filter(
        sender=user,
        status="draft"
    ).count()

    return render(request, "inbox.html", {
        "data": messages,
        "data1": count_inbox,
        "c1": count_draft
    })

def search(request):
    if not request.session.get('username'):
        return redirect("/login/")

    keyword = request.POST.get("se")
    user = Registration.objects.get(email_id=request.session['username'])

    results = Message.objects.filter(
        receiver=user,
        content__icontains=keyword
    )

    return render(request, "search.html", {"data3": results})

def sent(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    sent_msgs = Message.objects.filter(
        sender=user,
        status="sent"
    )

    return render(request, "sent.html", {"data": sent_msgs})

def draft(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    drafts = Message.objects.filter(
        sender=user,
        status="draft"
    )

    return render(request, "draft.html", {"data": drafts})

def draft1(request):
    if not request.session.get('username'):
        return redirect("/login/")

    msg_id = request.GET.get("count")
    message = Message.objects.filter(id=msg_id).first()

    if not message:
        return redirect("/draft/")

    request.session['draft_id'] = message.id

    if request.method == "POST":
        return redirect("/draft2/")

    return render(request, "draft1.html", {
        "frm1": message.receiver.email_id,
        "sub": message.subject,
        "con": message.content
    })

def draft2(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])
    users = Registration.objects.all()

    if request.method == "POST":
        Message.objects.create(
            sender=user,
            sendto=request.POST.get("sendto"),
            date=datetime.date.today(),
            subject=request.POST.get("subject"),
            content=request.POST.get("content"),
            status="sent"
        )

        # delete draft
        Message.objects.filter(id=request.session.get('did')).delete()

        return redirect("/inbox/")

    return render(request, "draft2.html", {
        "frm1": request.session.get('frm1'),
        "sub": request.session.get('sub'),
        "con": request.session.get('con'),
        "data": users
    })

def message(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto")
        receiver = Registration.objects.get(email_id=receiver_email)

        Message.objects.create(
            sender=user,
            receiver=receiver,
            subject=request.POST.get("subject"),
            content=request.POST.get("content"),
            status="sent"
        )

    inbox = Message.objects.filter(receiver=user).order_by("-id")

    return render(request, "message.html", {"messages": inbox})

def message1(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])
    users = Registration.objects.all()

    if request.method == "POST":
        Message.objects.create(
            sender=user,
            sendto=request.POST.get("sendto"),
            date=datetime.date.today(),
            subject=request.POST.get("subject"),
            content=request.POST.get("content"),
            status="sent"
        )
        return redirect("/inbox/")

    return render(request, "message1.html", {
        "frm1": request.session.get('frm1'),
        "data": users
    })

def userview(request):
    if not request.session.get('username'):
        return redirect("/login/")

    users = Registration.objects.all()

    user_id = request.GET.get("id")
    status = request.GET.get("status")

    if user_id:
        Registration.objects.filter(id=user_id).update(status=status)

    return render(request, "userview.html", {"data": users})

def profile(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    return render(request, "profile.html", {"data": user})

def editprofile(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        user.name = request.POST.get("name")
        user.address = request.POST.get("address")
        user.dob = request.POST.get("dob")
        user.mobile = request.POST.get("mobile")
        user.save()

        return redirect("/profile/")

    return render(request, "editprofile.html", {"data": user}) 
    
@never_cache
@login_required(login_url='login')
def adminhome(request):
    if not request.user.is_authenticated or not request.user.is_superuser:
        return redirect('userhome')

    total_users = Registration.objects.count()
    total_messages = Message.objects.count()
    total_feedback = Feedback.objects.count()
    
    recent_messages = Message.objects.order_by('-id')[:3]
    feed = Feedback.objects.order_by('-id')[:3]

    context = {
        "data1": total_users,     
        "count1": total_messages,  
        "count": total_feedback,   
        "det": recent_messages,
        "feed": feed,
        "role": "Admin"
    }

    return render(request, "dashboard.html", context)

@never_cache
@login_required(login_url='login')
def userhome(request):
    # if not request.session.get('username'):
    #     return redirect("/login/")

    # user = Registration.objects.get(email_id=request.session['username'])

    # inbox_count = Message.objects.filter(sendto=user.email_id).count()
    # total_messages = Message.objects.count()
    # total_users = Registration.objects.count()

    # recent_messages = Message.objects.filter(
    #     sendto=user.email_id,
    #     status="sent"
    # ).order_by('-id')[:2][::-1]

    # det = []
    # for msg in recent_messages:
    #     sender = Registration.objects.filter(email_id=msg.sender).first()
    #     if sender:
    #         det.append((sender.name, sender.image))

    # feed = Feedback.objects.order_by('-id')[:3].values_list('complaint', flat=True)

     return render(request, "userhome.html"
    # {
    #     "data": [user],
    #     "count": inbox_count,
    #     "count1": total_messages,
    #     "data1": total_users,
    #     "det": det,
    #     "feed": feed
    )
# @never_cache
# def userhome(request):
#     # Security check for custom session
#     email = request.session.get('username')
#     if not email:
#         return redirect('login')

#     # USER LOGIC: Data filtered to THIS user only
#     user_obj = Registration.objects.get(email_id=email)
    
#     # Personal statistics
#     my_inbox = Message.objects.filter(receiver=user_obj).count()
#     my_sent = Message.objects.filter(sender=user_obj, status="sent").count()
#     my_feed = Feedback.objects.filter(sender=user_obj).count()
    
#     # Personal recent messages
#     det = Message.objects.filter(receiver=user_obj).order_by('-id')[:3]
    
#     return render(request, "dashboard.html", {
#         "data1": "Active",         # Placeholder for user view
#         "count": my_inbox,         # User's personal inbox
#         "count1": my_sent,         # User's personal sent count
#         "feed_count": my_feed,
#         "det": det,
#         "data": [user_obj],        # For profile info
#         "role": "User"
#     })
  
def voice(request):
    return render(request,"voice.html") 

def home(request):
    return render(request,"home.html")  

def logout(request):
    storage = messages.get_messages(request)
    for _ in storage: 
        pass 
    auth_logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out!")
    return redirect("login")

def feedback(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        Feedback.objects.create(
            sender=user,
            subject=request.POST.get("subject"),
            complaint=request.POST.get("mycontent"),
            date=datetime.date.today()
        )

    return render(request, "feedback.html")
         
def viewfeedback(request):
    if not request.session.get('username'):
        return redirect("/login/")

    data = Feedback.objects.all().order_by('-id')

    return render(request, "viewfeedback.html", {"data": data})

def changeimage(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST" and request.FILES.get('img'):
        user.image = request.FILES['img']  
        user.save()

        return redirect("/profile/")

    return render(request, "changeimage.html", {"data": user})

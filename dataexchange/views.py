import MySQLdb 
import datetime
import subprocess
from django.shortcuts import render,redirect
from django.http import HttpResponse,HttpResponseRedirect
from django.core.files.storage import FileSystemStorage
from .models import Registration, Message, Feedback

def login(request):
    error = ""

    if request.method == "POST":
        username = request.POST.get("uname")
        password = request.POST.get("password")

        if username == "admin@gmail.com" and password == "admin":
            return redirect("/userview/")

        try:
            user = Registration.objects.get(email_id=username, password=password)

            if user.status == "approved":
                request.session['username'] = user.email_id
                return redirect("/userhome/")
            elif user.status == "rejected":
                error = "You have been rejected by admin"
            else:
                error = "Waiting for approval"

        except Registration.DoesNotExist:
            error = "Invalid credentials"

    return render(request, "login.html", {"error": error})

def reg(request):
    error = ""
    msg = ""

    if request.method == "POST":
        email = request.POST.get("email")
        mobile = request.POST.get("mobile")

        if Registration.objects.filter(email_id=email).exists():
            error = "Email already exists"
        elif Registration.objects.filter(mobile=mobile).exists():
            error = "Mobile already exists"
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
            msg = "Registered successfully. Wait for approval."

    return render(request, "reg.html", {"error": error, "msg": msg})

def adminlogin(request):
    error=""
    request.session['username']=""
    if(request.POST):        
        username=request.POST.get("uname")
        request.session['username']=username
        password=request.POST.get("password")
        if((username=='admin') and (password=='admin')):
            return HttpResponseRedirect("/adminhome/")
        else:
            error="enter valid email"     
    return render(request,"adminlogin.html",{"error":error})
         
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

def adminhome(request):
    if request.session["username"]:
       return render(request,"adminhome.html")                   
    else:
          return HttpResponseRedirect("/login")
        
def voice(request):
    return render(request,"voice.html") 

def commonhome(request):
    return render(request,"commonhome.html")  

def logout(request):
    request.session.flush()
    return render(request, "logout.html")
 
def userhome(request):
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    inbox_count = Message.objects.filter(sendto=user.email_id).count()
    total_messages = Message.objects.count()
    total_users = Registration.objects.count()

    recent_messages = Message.objects.filter(
        sendto=user.email_id,
        status="sent"
    ).order_by('-id')[:2][::-1]

    det = []
    for msg in recent_messages:
        sender = Registration.objects.filter(email_id=msg.sender).first()
        if sender:
            det.append((sender.name, sender.image))

    feed = Feedback.objects.order_by('-id')[:3].values_list('complaint', flat=True)

    return render(request, "adminhome.html", {
        "data": [user],
        "count": inbox_count,
        "count1": total_messages,
        "data1": total_users,
        "det": det,
        "feed": feed
    })

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

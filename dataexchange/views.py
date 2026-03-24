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

def draft1(request):
    db = get_db()
    c = db.cursor()
    det=[]
    if(request.session['username']):
        s1="sent"
        unam=request.session['username']
        c.execute("select * from(select * from message where sendto='"+unam+"' and status='"+s1+"' order by m_id desc limit 2)as r order by m_id")
        count2=c.fetchall()
        for i in count2:
            c.execute("select name,image from registration where email_id='"+ str(i[2]) +"'")
            count3=c.fetchone()
            det.append(count3)
        c.execute("select complaint from feedback order by f_id desc limit 3")    
        feed=c.fetchall()
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        frm=request.GET.get("count")
        request.session['did']=frm
        s="select sendto,subject,content from message where m_id='"+frm+"'"
        print(s)
        c.execute(s)
        data=c.fetchall()
        frm1=data[0][0]
        sub=data[0][1]
        con=data[0][2]
        request.session['frm1']=frm1
        request.session['sub']=sub
        request.session['con']=con

        if request.POST:
                    return HttpResponseRedirect("/draft2/")
    else:
        return HttpResponseRedirect("/login/")           
    return render(request,"draft1.html",{"frm1":frm1,"sub":sub,"con":con,"s":s,"data2":data2})  
  
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
def message1(request):
    db = get_db()
    c = db.cursor()
    if(request.session['username']):
        c.execute("select * from registration")
        data=c.fetchall()
        frm1=request.session['frm1']  
        if(request.POST):
            if(request.GET.get("content")==""):
                content=request.POST.get("content")
            else:
                content=request.POST.get("content")
            sendto=request.POST.get("sendto")
            date=datetime.date.today()
            subject=request.POST.get("subject")
            unam=request.session['username']
            status="sent"
            s="insert into message(`from`,sendto,date,subject,content,status) values('"+str(unam)+"','"+str(sendto)+"','"+ str(date)+"','"+str(subject)+"','"+str(content)+"','"+status+"')"
            c.execute(s)
            db.commit()
            return HttpResponseRedirect("/inbox/")
    return render(request,"message1.html",{"frm1":frm1,"data":data}) 

def draft2(request):
    db = get_db()
    c = db.cursor()
    if(request.session['username']):
        c.execute("select * from registration")
        data=c.fetchall()
        frm1=request.session['frm1']
        sub=request.session['sub']
        con=request.session['con']
        if(request.POST):
            if(request.GET.get("content")==""):
                content=request.POST.get("content")
            else:
                content=request.POST.get("content")
            sendto=request.POST.get("sendto")
            date=datetime.date.today()
            subject=request.POST.get("subject")
            unam=request.session['username']
            status="sent"
            s="insert into message(`from`,sendto,date,subject,content,status) values('"+str(unam)+"','"+str(sendto)+"','"+ str(date)+"','"+str(subject)+"','"+str(content)+"','"+status+"')"
            c.execute(s)
            db.commit()
            c.execute("delete from message where m_id='"+ str(request.session['did']) +"'")
            db.commit()
            return HttpResponseRedirect("/inbox/")
    return render(request,"draft2.html",{"frm1":frm1,"sub":sub,"con":con,"data":data})

def userview(request):
    db = get_db()
    c = db.cursor()
    if(request.session['username']):
        c.execute("select * from registration")
        data=c.fetchall()
        id=request.GET.get("id")
        status=request.GET.get("status")
        if(id):
            c.execute("update registration set status='"+status+"' where u_id='"+id+"';")
            db.commit()
    else:
        return HttpResponseRedirect("/login/")     
    return render(request,"userview.html",{"data":data})

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
    data=request.GET.get("id")
    request.session['username']=""
    return render(request,"logout.html",{"data":data})  
  
def userhome(request):
    db = get_db()
    c = db.cursor()
    det=[]
    if(request.session['username']):
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data=c.fetchall()
        c.execute("select count(content) from message where sendto='"+unam+"'")
        count=c.fetchone()
        c.execute("select count(*) from message")
        count1=c.fetchone()
        c.execute("select count(*) from registration")
        data1=c.fetchone()
        s="sent"
        c.execute("select * from(select * from message where sendto='"+unam+"' and status='"+s+"' order by m_id desc limit 2)as r order by m_id")
        count2=c.fetchall()
        for i in count2:
            c.execute("select name,image from registration where email_id='"+ str(i[2]) +"'")
            count3=c.fetchone()
            det.append(count3)
        c.execute("select complaint from feedback order by f_id desc limit 3")    
        feed=c.fetchall()
    else:
        return HttpResponseRedirect("/login/")    
    return render(request,"adminhome.html",{"data":data,"count":count[0],"data1":data1[0],"count1":count1[0],"det":det,"feed":feed})      

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
    db = get_db()
    c = db.cursor()
    if(request.session['username']):
        c.execute("select * from feedback")
        data=c.fetchall()
    else:
        return HttpResponseRedirect("/login/")    
    return render(request,"viewfeedback.html",{"data":data}) 

def changeimage(request):
    db = get_db()
    c = db.cursor()
    if(request.session['username']):
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data=c.fetchall()
        if(request.POST):    
            if(request.FILES['img']):
                    myfile=request.FILES['img']
                    fs=FileSystemStorage()
                    filename=fs.save(myfile.name,myfile)
                    fileurl=fs.url(filename)
            c.execute("update registration set image='"+fileurl+"' where email_id='"+unam+"'") 
            db.commit() 
            return HttpResponseRedirect("/profile/")  
    else:
        return HttpResponseRedirect("/login/")         
    return render(request,"changeimage.html",{"data":data})    
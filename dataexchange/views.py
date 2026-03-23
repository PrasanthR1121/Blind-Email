from django.shortcuts import render
from django.http import HttpResponse,HttpResponseRedirect
import MySQLdb 
import datetime
import subprocess
from django.core.files.storage import FileSystemStorage
import os
db=MySQLdb.connect("localhost","root","","dataexchange")
c=db.cursor()
def login(request):
 
    error=""
    request.session['username']=""
    password=""
    if(request.POST):        
        username=request.POST.get("uname")
        request.session['username']=username
        password=request.POST.get("password")
        if((username=='admin@gmail.com') and (password=='admin')):
             return HttpResponseRedirect("/userview/")
        else:
            
            c.execute("select count('"+ username +"') from registration where email_id='"+ username +"' and password='"+password+"'" )
            data=c.fetchone()
            if data[0]==1:
                c.execute("select status from registration where email_id='"+username+"' ")
                data1=c.fetchone() 
                #if data1:         
                if (data[0]==1 and data1[0]=="approved"):                
                        # subprocess.call("E:\\windapp\\windapp\\bin\\Debug\\windapp.exe")  
                        # f=open("E:\\face.txt","r")
                        # data=f.read()
                        # z=len(data)
                        # f.close() 
                        # if(data[0:z-1]==username):
                        return HttpResponseRedirect("/userhome/")            
                else:
                        if(data1[0]=="rejected"):
                            error="you have been rejected from ADMIN"
                        else:
                            error="enter valid email"   
            else:
                    return HttpResponseRedirect("/login/") 
                        

            #db.commit()
            
            
    return render(request,"login.html",{"error":error})
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
    error=""
    if(request.POST):
        username=request.POST.get("uname")
        mobile=request.POST.get("mobile")
        request.session['username']=username
        c.execute("select count('"+ username +"') from registration where email_id='"+ username +"' and mobile='"+ mobile +"'")
        data=c.fetchone()
        if (data[0]==1):
            return HttpResponseRedirect("/security/")
        else:
            error="enter valid email"       

    return render(request,"forgot.html",{"error":error})   

def security(request):
    error=""
    if(request.POST):
        answer=request.POST.get("answer")
        c.execute("select count(*) from registration where answer='"+answer+"'")
        print("select count(*) from registration where answer='"+answer+"'")
        data=c.fetchone()
        if (data[0]>1):
            return HttpResponseRedirect("/newpass/")
        else:
            error="enter correct answer"  
    return render(request,"security.html",{"error":error}) 

def newpass(request):
    error=""
    unam=request.session['username']
    if(request.POST):
        password=request.POST.get("password")
        cpassword=request.POST.get("cpassword")
        if(password==cpassword):
            c.execute("update registration set password='"+password+"' where email_id='"+unam+"'")
            db.commit()
            return HttpResponseRedirect("/login/")
        else: 
            error="password mismatch" 
    return render(request,"newpass.html",{"error":error})            


def reg(request):
    error=""
    msg=""
    err=""
    msg1=""
    if(request.POST):
        # subprocess.call('E:\\windapp\\windapp\\bin\\Debug\\windapp.exe') 
        name=request.POST.get("name")
        address=request.POST.get("address")
        dob=request.POST.get("dob")
        gender=request.POST.get("gender")             
        email=request.POST.get("email")
        mobile=request.POST.get("mobile")
        password=request.POST.get("password")
        cpassword=request.POST.get("cpassword")
        answer=request.POST.get("answer")
        
        if(request.FILES['img']):
            myfile=request.FILES['img']
            fs=FileSystemStorage()
            filename=fs.save(myfile.name,myfile)
            fileurl=fs.url(filename)
        else:
            fileurl="/static/media/a.png"
        if(password==cpassword):
            c.execute("select count('"+email+"') from registration where email_id='"+email+"'")
            data=c.fetchone()
            c.execute("select count('"+mobile+"') from registration where mobile='"+mobile+"'")
            mob=c.fetchone()
            if (data[0]==0):
                if (mob[0]==0):
                    c.execute("insert into registration(name,address,dob,gender,email_id,mobile,image,password,answer) values('"+name+"','"+address+"','"+dob+"','"+gender+"','"+email+"','"+str(mobile)+"','"+fileurl+"','"+password+"','"+answer+"')")
                    db.commit()
                    msg="wait for admin to approve"
                else:
                    msg1="existing mobile number"


            
            else:
                error="USERNAME ALREDY EXISTED"
        else:
            err="password and confirm password donot match"
        
    return render(request,"reg.html",{"error":error,"msg":msg,"err":err,"msg1":msg1})    

def save(request):
    if(request.session['username']):
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        content="no data"
        s=""
        if(request.GET.get("msg")):
            content=request.GET.get("msg")
            sendto=request.GET.get("to")
            date=datetime.date.today()
            subject=request.GET.get("sub")
            status="draft"
            unam=request.session['username']
            s="insert into message(`from`,sendto,date,subject,content,status) values('"+ str(unam) +"',"+ str(sendto) +",'"+ str(date)+"',"+ str(subject) +","+ str(content) +",'"+ str(status) +"')"
        # c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()
    else:
        return HttpResponseRedirect("/login/")
            
    return render(request,"message.html",{"data":s,"msg":request.POST.get("content"),"data2":data2})        
       
def message(request):
    det=[]
    if(request.session['username']):
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        content="no data"
        s="sent"
        c.execute("select * from(select * from message where sendto='"+unam+"' and status='"+s+"' order by m_id desc limit 2)as r order by m_id")
        count2=c.fetchall()
        for i in count2:
            c.execute("select name,image from registration where email_id='"+ str(i[2]) +"'")
            count3=c.fetchone()
            det.append(count3)
        c.execute("select complaint from feedback order by f_id desc limit 3")    
        feed=c.fetchall()
        if(request.GET.get("msg")):
            content=request.GET.get("msg")
            sendto=request.GET.get("to")
            date=datetime.date.today()
            subject=request.GET.get("sub")
            status="sent"
            unam=request.session['username']
            s="insert into message(`from`,sendto,date,subject,content,status) values('"+ str(unam) +"',"+ str(sendto) +",'"+ str(date)+"',"+ str(subject) +","+ str(content) +",'"+ str(status) +"')"
        # c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()

        if("send" in request.POST):
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
            #c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()

        if("draft" in request.POST):
            if(request.GET.get("content")==""):
                content=request.POST.get("content")
            else:
                content=request.POST.get("content")

            sendto=request.POST.get("sendto")
            date=datetime.date.today()
            subject=request.POST.get("subject")
            unam=request.session['username']
            status="Draft"
            s="insert into message(`from`,sendto,date,subject,content,status) values('"+str(unam)+"','"+str(sendto)+"','"+ str(date)+"','"+str(subject)+"','"+str(content)+"','"+status+"')"
            #c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()
    else:
        return HttpResponseRedirect("/login/")
            
    return render(request,"message.html",{"data":s,"msg":request.POST.get("content"),"data2":data2,"det":det,"feed":feed})
def compose(request):
    if(request.session['username']):
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        frm=request.GET.get("count")
        s="select `from`,subject,content from message where m_id='"+frm+"'"
        print(s)
        c.execute(s)
        data=c.fetchall()
        frm1=data[0][0]
        sub=data[0][1]
        con=data[0][2]
        request.session['frm1']=frm1
        if request.POST:
                    return HttpResponseRedirect("/message1/")
    else:
        return HttpResponseRedirect("/login/")           
    return render(request,"compose.html",{"frm1":frm1,"sub":sub,"con":con,"s":s,"data2":data2})
def draft1(request):
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
    if(request.session['username']):
        data3=""
        s="sent"
        c1="draft"
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        c.execute("select count(*) from message where sendto='"+unam+"' and `status`='"+s+"'")
        data1=c.fetchone()
        c.execute("select count(*) from message where `from`='"+unam+"' and `status`='"+c1+"'")
        c1=c.fetchone()
        c.execute("select `from`,date,subject,content,sendto,m_id from message where sendto='"+unam+"' and `status`='"+s+"'")
        data=c.fetchall()
        if(request.POST):
            request.session["z"]=request.POST.get("se")
            
            return HttpResponseRedirect("/search/")
            return render(request,"search.html",{"data3":data3})
    else:
        return HttpResponseRedirect("/login/")    
    return render(request,"inbox.html",{"data":data,"data1":data1[0],"data2":data2,"c1":c1[0]})
def search(request):
    if(request.session['username']):
        z=request.session["z"]
        unam=request.session['username']
        y=z+'%'
        s="select * from message where content like '"+z+"%' and sendto ='"+unam+"'"
        c.execute(s)
        data3=c.fetchall()
        unam=request.session['username']
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
    else:
        return HttpResponseRedirect("/login/")       
    return render(request,"search.html",{"data2":data2,"data3":data3})


def sent(request):
    det=[]
    c1="draft"
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
    
        s="sent"
        c.execute("select count(*) from message where sendto='"+unam+"' and `status`='"+s+"'")
        data1=c.fetchone()
        c.execute("select count(*) from message where `from`='"+unam+"' and `status`='"+c1+"'")
        c1=c.fetchone()
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        c.execute("select * from message where `from`='"+unam+"' and `status`='"+s+"'") 
        data=c.fetchall()
        print("select * from message where `from`='"+unam+"' and `status`='"+s+"'")
    else:
        return HttpResponseRedirect("/login/")      
    return render(request,"sent.html",{"data":data,"data2":data2,"feed":feed,"det":det,"c1":c1[0],"data1":data1[0]})


def draft(request):
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
    
        s="draft"
        c1="sent"
        
        c.execute("select * from registration where email_id='"+unam+"'")
        data2=c.fetchall()
        c.execute("select count(*) from message where sendto='"+unam+"' and `status`='"+c1+"'")
        data1=c.fetchone()
        c.execute("select count(*) from message where `from`='"+unam+"' and `status`='"+s+"'")
        data4=c.fetchone()
        c.execute("select sendto,date,subject,content,m_id from message where `from`='"+unam+"' and `status`='"+s+"'")
        data=c.fetchall()
    else:
        return HttpResponseRedirect("/login/")     
    return render(request,"draft.html",{"data":data,"data1":data1[0],"data2":data2,"data4":data4[0],"feed":feed,"det":det})   
def message1(request):
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
            #c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()
            return HttpResponseRedirect("/inbox/")


    return render(request,"message1.html",{"frm1":frm1,"data":data}) 
def draft2(request):
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
            #c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()
            # c.execute("select max(m_id) from message where `from`='"+ str(unam) +"'")
            # did=c.fetchone()


            #draft
            c.execute("delete from message where m_id='"+ str(request.session['did']) +"'")
            db.commit()

            return HttpResponseRedirect("/inbox/")


    return render(request,"draft2.html",{"frm1":frm1,"sub":sub,"con":con,"data":data})

def userview(request):
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
        data=c.fetchall()
        if(request.POST):
            return HttpResponseRedirect("/editprofile/")
    else:
        return HttpResponseRedirect("/login/")
    return render(request,"profile.html",{"data":data,"feed":feed,"det":det}) 
def editprofile(request):
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
        data=c.fetchall() 
        for d in data:
                uid=d[0]
        if(request.POST):
            name=request.POST.get("name")
            address=request.POST.get("address")
            dob=request.POST.get("dob")
            #gender=request.POST.get("gender")             
            email=request.POST.get("email")
            mobile=request.POST.get("mobile")
            #password=request.POST.get("password")
            c.execute("update registration set name='"+name+"',address='"+address+"',dob='"+str(dob)+"',email_id='"+email+"',mobile='"+str(mobile)+"' where u_id='"+str(uid)+"'")
            db.commit()
            return HttpResponseRedirect("/profile/")
    else:
        return HttpResponseRedirect("/login/")
    return render(request,"editprofile.html",{"data":data,"feed":feed,"det":det})   
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
        data=c.fetchall()
        content="no data"
        s=""
        if(request.GET.get("msg")):
            content=request.GET.get("msg")
            msgto="admin"
            
            date=datetime.date.today()
            subject=request.GET.get("sub")
            status="sent"
            unam=request.session['username']
            s="insert into feedback(`from`,`to`,`date`,sub,complaint) values('"+unam+"','"+msgto+"','"+ str(date)+"',"+subject+","+content+")"
        # c.execute("insert into message(from,sendto,subject,content) values('"+unam+"','"+sendto+"','"+subject+"','"+content+"')")
            c.execute(s)
            db.commit()
        if(request.POST):
            unam=request.session['username']
            msgto="admin"
            date=datetime.date.today()
            subject=request.POST.get("subject")
            feedback=request.POST.get("mycontent")
            c.execute("insert into feedback(`from`,`to`,`date`,sub,complaint) values('"+unam+"','"+msgto+"','"+ str(date)+"','"+subject+"','"+feedback+"')")
            db.commit()
    else:
        return HttpResponseRedirect("/login/")          
            
    return render(request,"feedback.html",{"data":data,"det":det,"feed":feed}) 
         
def viewfeedback(request):
    if(request.session['username']):
        c.execute("select * from feedback")
        data=c.fetchall()
    else:
        return HttpResponseRedirect("/login/")    
    return render(request,"viewfeedback.html",{"data":data}) 
def changeimage(request):
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

# Create your views here.

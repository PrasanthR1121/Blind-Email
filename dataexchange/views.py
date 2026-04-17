from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Registration, Message, Feedback

import datetime


# ─────────────────────────────────────────────
# HELPER: clears stale messages from previous page
# ─────────────────────────────────────────────
def _clear_messages(request):
    storage = messages.get_messages(request)
    for _ in storage:
        pass


# ─────────────────────────────────────────────
# AUTH VIEWS
# ─────────────────────────────────────────────

@never_cache
def login(request):
    """
    Voice cues:
    - On load (GET): "Login page. Enter your username and password."
    - Success (admin): "Welcome Admin <name>. Redirecting to dashboard."
    - Success (user): "Welcome back <name>. Redirecting to dashboard."
    - Pending/blocked: "Your account is currently <status>. Contact admin."
    - Failure: "Login failed. Invalid credentials. Please try again."
    """
    if request.session.get('username'):
        return redirect('/dashboard/')

    if request.method == "POST":
        identifier = request.POST.get("uname", "").strip()
        password   = request.POST.get("password", "")

        _clear_messages(request)

        # 1. Try Django superuser auth
        admin_user = authenticate(request, username=identifier, password=password)

        if admin_user is not None and admin_user.is_superuser:
            auth_login(request, admin_user)
            request.session['username'] = admin_user.username
            request.session.modified = True
            messages.success(
                request,
                f"Welcome, Admin {admin_user.username}. Redirecting to your dashboard."
            )
            return redirect("/dashboard/")

        if admin_user is not None and not admin_user.is_superuser:
            messages.error(request, "Access denied. This account does not have admin privileges.")
            return redirect('login')

        # 2. Try Registration model user
        try:
            user = Registration.objects.get(email_id=identifier, password=password)
            if user.status == "approved":
                request.session['username'] = user.email_id
                request.session.modified = True
                messages.success(
                    request,
                    f"Welcome back, {user.name}. Redirecting to your dashboard."
                )
                return redirect("/dashboard/")
            else:
                messages.warning(
                    request,
                    f"Your account is currently {user.status}. Please contact the administrator."
                )
                return redirect('login')

        except Registration.DoesNotExist:
            messages.error(
                request,
                "Login failed. Invalid email or password. Please try again."
            )
            return redirect('login')

    # GET — no message needed; login.html speaks a welcome prompt on its own
    return render(request, "login.html")


@never_cache
def logout(request):
    """
    Voice cue: "You have been logged out successfully. Returning to login page."
    """
    _clear_messages(request)
    auth_logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out successfully. Returning to login page.")
    return redirect("login")


# ─────────────────────────────────────────────
# REGISTRATION
# ─────────────────────────────────────────────

def reg(request):
    """
    Voice cues:
    - Duplicate email:  "Error. This email address is already registered."
    - Duplicate mobile: "Error. This mobile number is already registered."
    - Success:          "<name>, your account has been created. Please wait for admin approval."
    - System error:     "A system error occurred. Please try again."
    """
    if request.method == "POST":
        email  = request.POST.get('email', '').strip()
        mobile = request.POST.get('mobile', '').strip()

        if Registration.objects.filter(email_id=email).exists():
            messages.error(request, "Error. This email address is already registered.")
            return redirect('reg')

        if Registration.objects.filter(mobile=mobile).exists():
            messages.error(request, "Error. This mobile number is already registered.")
            return redirect('reg')

        try:
            user = Registration.objects.create(
                name     = request.POST.get('name'),
                address  = request.POST.get('address'),
                dob      = request.POST.get('dob'),
                gender   = request.POST.get('gender'),
                email_id = email,
                mobile   = mobile,
                password = request.POST.get('password'),
                answer   = request.POST.get('answer'),
                image    = request.FILES.get('img'),
                status   = 'pending'
            )
            messages.success(
                request,
                f"{user.name}, your account has been created successfully. "
                f"Please wait for admin approval before you can log in."
            )
            return redirect('login')

        except Exception:
            messages.error(request, "A system error occurred. Please try again.")
            return redirect('reg')

    return render(request, 'reg.html')


# ─────────────────────────────────────────────
# PASSWORD RECOVERY
# ─────────────────────────────────────────────

def forgot(request):
    """
    Voice cues:
    - Not found: "No account matched that email and mobile. Please check and try again."
    """
    error = ""
    if request.method == "POST":
        email  = request.POST.get("uname", "").strip()
        mobile = request.POST.get("mobile", "").strip()

        user = Registration.objects.filter(email_id=email, mobile=mobile).first()
        if user:
            request.session['reset_user'] = user.email_id
            return redirect("/security/")
        else:
            error = "No account matched that email and mobile number. Please check and try again."

    return render(request, "forgot.html", {"error": error})


def security(request):
    """
    Voice cues:
    - Wrong answer: "Incorrect security answer. Please try again."
    """
    error = ""
    if request.method == "POST":
        answer   = request.POST.get("answer", "").strip()
        username = request.session.get("reset_user")

        user = Registration.objects.filter(email_id=username, answer=answer).first()
        if user:
            return redirect("/newpass/")
        else:
            error = "Incorrect security answer. Please try again."

    return render(request, "security.html", {"error": error})


def newpass(request):
    """
    Voice cues:
    - Mismatch: "Passwords do not match. Please re-enter both fields."
    - Success:  handled by login page welcome message after redirect.
    """
    error    = ""
    username = request.session.get("reset_user")

    if not username:
        return redirect("/login/")

    if request.method == "POST":
        password  = request.POST.get("password", "")
        cpassword = request.POST.get("cpassword", "")

        if password == cpassword:
            user = Registration.objects.get(email_id=username)
            user.password = password
            user.save()
            request.session.pop("reset_user", None)
            messages.success(request, "Password updated successfully. Please log in with your new password.")
            return redirect("/login/")
        else:
            error = "Passwords do not match. Please re-enter both fields."

    return render(request, "newpass.html", {"error": error})


# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────

@never_cache
def dashboard(request):
    """
    Voice cues (spoken by dashboard.html JS):
    - Admin: "Welcome Admin <name>. You have <N> users, <N> emails, <N> feedback items."
    - User:  "Welcome <name>. You have <N> messages in your inbox and <N> sent items."
    """
    is_admin   = request.user.is_authenticated and request.user.is_superuser
    user_email = request.session.get('username')

    if not is_admin and not user_email:
        return redirect('login')

    if is_admin:
        context = {
            "role":   "Admin",
            "name":   request.user.username,
            "data1":  Registration.objects.count(),
            "count":  Message.objects.count(),
            "count1": Feedback.objects.count(),
            "det":    list(Message.objects.order_by('-id')[:5]
                          .values_list('subject', flat=True)),
            "feed":   Feedback.objects.order_by('-id')[:3],
        }
    else:
        user_obj = Registration.objects.get(email_id=user_email)
        inbox_count = Message.objects.filter(receiver=user_obj, status="sent").count()
        sent_count  = Message.objects.filter(sender=user_obj, status="sent").count()
        recent      = Message.objects.filter(receiver=user_obj).order_by('-id')[:5]

        context = {
            "role":   "User",
            "name":   user_obj.name,
            "data1":  "Active",
            "count":  inbox_count,
            "count1": sent_count,
            "det":    [f"From {m.sender.name}: {m.subject}" for m in recent],
            "feed":   [],
            "data":   [user_obj],
        }

    return render(request, "dashboard.html", context)


# ─────────────────────────────────────────────
# INBOX
# ─────────────────────────────────────────────

def inbox(request):
    """
    Voice cues:
    - Empty:    "Your inbox is empty. No new messages."
    - Has mail: "You have <N> messages in your inbox. Use Tab to navigate each message."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    _clear_messages(request)
    user = Registration.objects.get(email_id=request.session['username'])
    msgs = Message.objects.filter(receiver=user, status="sent").order_by("-id")
    count = msgs.count()

    if count == 0:
        messages.info(request, "Your inbox is empty. No new messages.")
    else:
        messages.info(
            request,
            f"You have {count} message{'s' if count != 1 else ''} in your inbox. "
            f"Use Tab to navigate each message."
        )

    return render(request, "inbox.html", {"data": msgs})


# ─────────────────────────────────────────────
# COMPOSE / SEND
# ─────────────────────────────────────────────

def message(request):
    """
    Voice cues:
    - Recipient not found: "Recipient not found. Please check the email address and try again."
    - Sent:                "Your message with subject <subject> has been sent successfully."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto", "").strip()
        receiver       = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            subject = request.POST.get("subject", "")
            Message.objects.create(
                sender   = user,
                receiver = receiver,
                subject  = subject,
                content  = request.POST.get("content"),
                status   = "sent"
            )
            messages.success(
                request,
                f"Your message with subject '{subject}' has been sent successfully to {receiver.name}."
            )
            return redirect("/inbox/")
        else:
            messages.error(
                request,
                "Recipient not found. Please check the email address and try again."
            )

    return render(request, "message.html")


def save(request):
    """
    Saves a draft.
    Voice cue: "Your message has been saved as a draft."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto", "").strip()
        receiver       = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            Message.objects.create(
                sender   = user,
                receiver = receiver,
                subject  = request.POST.get("subject"),
                content  = request.POST.get("content"),
                status   = "draft"
            )
            messages.info(request, "Your message has been saved as a draft.")
        else:
            messages.error(request, "Recipient not found. Draft not saved.")

    return redirect("/draft/")


# ─────────────────────────────────────────────
# READ / REPLY
# ─────────────────────────────────────────────

def compose(request):
    """
    Opens a received message to reply.
    Voice cue spoken by template on load:
    "Reading message from <sender>. Subject: <subject>. Press R to reply."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    msg_id  = request.GET.get("count")
    msg_obj = Message.objects.filter(id=msg_id).first()

    if not msg_obj:
        messages.error(request, "Message not found.")
        return redirect("/inbox/")

    request.session['reply_to'] = msg_obj.sender.email_id

    return render(request, "compose.html", {
        "frm1":    msg_obj.sender.email_id,
        "sub":     msg_obj.subject,
        "con":     msg_obj.content,
        "sender":  msg_obj.sender.name,
    })


def message1(request):
    """
    Reply form submission.
    Voice cue: "Reply sent successfully."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user  = Registration.objects.get(email_id=request.session['username'])
    users = Registration.objects.all()

    if request.method == "POST":
        receiver_email = request.POST.get("sendto", "").strip()
        receiver       = Registration.objects.filter(email_id=receiver_email).first()
        if receiver:
            Message.objects.create(
                sender   = user,
                receiver = receiver,
                subject  = request.POST.get("subject"),
                content  = request.POST.get("content"),
                status   = "sent"
            )
            messages.success(request, "Your reply has been sent successfully.")
        return redirect("/inbox/")

    return render(request, "message1.html", {
        "frm1": request.session.get('reply_to', ''),
        "data": users
    })


# ─────────────────────────────────────────────
# SEARCH
# ─────────────────────────────────────────────

def search(request):
    """
    Voice cues:
    - Results found: "<N> messages found matching '<keyword>'."
    - No results:    "No messages found matching '<keyword>'."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    keyword = request.POST.get("se", "").strip()
    user    = Registration.objects.get(email_id=request.session['username'])

    results = Message.objects.filter(receiver=user, content__icontains=keyword)
    count   = results.count()

    if count:
        messages.info(request, f"{count} message{'s' if count != 1 else ''} found matching '{keyword}'.")
    else:
        messages.info(request, f"No messages found matching '{keyword}'.")

    return render(request, "search.html", {"data3": results, "keyword": keyword})


# ─────────────────────────────────────────────
# SENT
# ─────────────────────────────────────────────

def sent(request):
    """
    Voice cues:
    - Empty:    "Your sent folder is empty."
    - Has mail: "You have <N> sent messages."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    _clear_messages(request)
    user      = Registration.objects.get(email_id=request.session['username'])
    sent_msgs = Message.objects.filter(sender=user, status="sent").order_by("-id")
    count     = sent_msgs.count()

    if count == 0:
        messages.info(request, "Your sent folder is empty.")
    else:
        messages.info(request, f"You have {count} sent message{'s' if count != 1 else ''}.")

    return render(request, "sent.html", {"data": sent_msgs})


# ─────────────────────────────────────────────
# DRAFTS
# ─────────────────────────────────────────────

def draft(request):
    """
    Voice cues:
    - Empty:    "You have no saved drafts."
    - Has drafts: "You have <N> saved draft messages."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    _clear_messages(request)
    user   = Registration.objects.get(email_id=request.session['username'])
    drafts = Message.objects.filter(sender=user, status="draft").order_by("-id")
    count  = drafts.count()

    if count == 0:
        messages.info(request, "You have no saved drafts.")
    else:
        messages.info(request, f"You have {count} saved draft message{'s' if count != 1 else ''}.")

    return render(request, "draft.html", {"data": drafts})


def draft1(request):
    """Opens a draft for editing."""
    if not request.session.get('username'):
        return redirect("/login/")

    msg_id  = request.GET.get("count")
    msg_obj = Message.objects.filter(id=msg_id).first()

    if not msg_obj:
        messages.error(request, "Draft not found.")
        return redirect("/draft/")

    request.session['draft_id'] = msg_obj.id

    return render(request, "draft1.html", {
        "frm1": msg_obj.receiver.email_id,
        "sub":  msg_obj.subject,
        "con":  msg_obj.content
    })


def draft2(request):
    """
    Sends a draft as a real email.
    Voice cue: "Your draft has been sent successfully."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        receiver_email = request.POST.get("sendto", "").strip()
        receiver       = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            Message.objects.create(
                sender   = user,
                receiver = receiver,
                subject  = request.POST.get("subject"),
                content  = request.POST.get("content"),
                status   = "sent"
            )
            # Delete the original draft
            draft_id = request.session.pop('draft_id', None)
            if draft_id:
                Message.objects.filter(id=draft_id).delete()

            messages.success(request, "Your draft has been sent successfully.")
            return redirect("/inbox/")
        else:
            messages.error(request, "Recipient not found. Draft was not sent.")
            return redirect("/draft/")

    return render(request, "draft2.html", {
        "frm1": request.session.get('frm1', ''),
        "sub":  request.session.get('sub', ''),
        "con":  request.session.get('con', ''),
        "data": Registration.objects.all()
    })


# ─────────────────────────────────────────────
# ADMIN: USER MANAGEMENT
# ─────────────────────────────────────────────

def userview(request):
    """
    Voice cues:
    - Status updated: "User status has been updated to <status>."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user_id = request.GET.get("id")
    status  = request.GET.get("status")

    if user_id and status:
        Registration.objects.filter(id=user_id).update(status=status)
        messages.success(request, f"User status has been updated to {status}.")

    users = Registration.objects.all().order_by('-id')
    return render(request, "userview.html", {"data": users})


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

def profile(request):
    """
    Voice cue (spoken by template):
    "Viewing your profile. Name: <name>. Email: <email>."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])
    return render(request, "profile.html", {"data": user})


def editprofile(request):
    """
    Voice cues:
    - Success: "Your profile has been updated successfully."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        user.name    = request.POST.get("name")
        user.address = request.POST.get("address")
        user.dob     = request.POST.get("dob")
        user.mobile  = request.POST.get("mobile")
        user.save()
        messages.success(request, "Your profile has been updated successfully.")
        return redirect("/profile/")

    return render(request, "editprofile.html", {"data": user})


def changeimage(request):
    """
    Voice cues:
    - Success: "Your profile photo has been updated."
    - No file: "No image selected. Please choose a file."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        if request.FILES.get('img'):
            user.image = request.FILES['img']
            user.save()
            messages.success(request, "Your profile photo has been updated.")
        else:
            messages.error(request, "No image selected. Please choose a file.")
        return redirect("/profile/")

    return render(request, "changeimage.html", {"data": user})


# ─────────────────────────────────────────────
# FEEDBACK
# ─────────────────────────────────────────────

def feedback(request):
    """
    Voice cues:
    - Success: "Thank you. Your feedback has been submitted successfully."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    user = Registration.objects.get(email_id=request.session['username'])

    if request.method == "POST":
        Feedback.objects.create(
            sender    = user,
            subject   = request.POST.get("subject"),
            complaint = request.POST.get("mycontent"),
            date      = datetime.date.today()
        )
        messages.success(request, "Thank you. Your feedback has been submitted successfully.")

    return render(request, "feedback.html")


def viewfeedback(request):
    """
    Voice cue (spoken by template):
    "Viewing all feedback. <N> items found."
    """
    if not request.session.get('username'):
        return redirect("/login/")

    _clear_messages(request)
    data  = Feedback.objects.all().order_by('-id')
    count = data.count()

    if count == 0:
        messages.info(request, "No feedback submissions found.")
    else:
        messages.info(request, f"{count} feedback submission{'s' if count != 1 else ''} found.")

    return render(request, "viewfeedback.html", {"data": data})


# ─────────────────────────────────────────────
# MISC
# ─────────────────────────────────────────────

def voice(request):
    return render(request, "voice.html")


def home(request):
    return render(request, "home.html")


# ─────────────────────────────────────────────
# ADMIN VIEWS (Django login_required)
# ─────────────────────────────────────────────

@never_cache
@login_required(login_url='login')
def adminhome(request):
    if not request.user.is_superuser:
        return redirect('login')

    context = {
        "role":   "Admin",
        "name":   request.user.username,
        "data1":  Registration.objects.count(),
        "count":  Feedback.objects.count(),
        "count1": Message.objects.count(),
        "det":    list(Message.objects.order_by('-id')[:5].values_list('subject', flat=True)),
        "feed":   Feedback.objects.order_by('-id')[:3],
    }
    return render(request, "dashboard.html", context)


@never_cache
@login_required(login_url='login')
def userhome(request):
    email = request.session.get('username')
    if not email:
        return redirect('login')

    user_obj    = Registration.objects.get(email_id=email)
    inbox_count = Message.objects.filter(receiver=user_obj, status="sent").count()
    sent_count  = Message.objects.filter(sender=user_obj, status="sent").count()
    recent      = Message.objects.filter(receiver=user_obj).order_by('-id')[:5]

    return render(request, "dashboard.html", {
        "role":   "User",
        "name":   user_obj.name,
        "data1":  "Active",
        "count":  inbox_count,
        "count1": sent_count,
        "det":    [f"From {m.sender.name}: {m.subject}" for m in recent],
        "feed":   [],
        "data":   [user_obj],
    })
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.cache import never_cache
from .models import Registration, Message, Feedback

import datetime

SESSION_AGE_SECONDS = 60 * 60 * 24
STATUS_PENDING = "pending"
STATUS_ACTIVE = "active"
STATUS_BLOCKED = "blocked"
LOGIN_ALLOWED_STATUSES = {STATUS_ACTIVE, "approved"}


# ─────────────────────────────────────────────
# HELPER: clears stale messages from previous page
# ─────────────────────────────────────────────
def _clear_messages(request):
    storage = messages.get_messages(request)
    for _ in storage:
        pass


def _start_session(request, username):
    request.session['username'] = username
    request.session.set_expiry(SESSION_AGE_SECONDS)
    request.session.modified = True


def _normalize_status(status):
    status = (status or STATUS_PENDING).lower()
    if status == "approved":
        return STATUS_ACTIVE
    if status in {"blocked", "cancelled", "canceled", "rejected"}:
        return STATUS_BLOCKED
    if status == STATUS_ACTIVE:
        return STATUS_ACTIVE
    return STATUS_PENDING


def _current_registration(request):
    username = request.session.get('username')
    if not username:
        return None

    user = Registration.objects.filter(email_id=username).first()
    if not user:
        request.session.flush()
        return None

    normalized_status = _normalize_status(user.status)
    if normalized_status != user.status:
        user.status = normalized_status
        user.save(update_fields=['status'])

    if user.status != STATUS_ACTIVE:
        request.session.flush()
        return None

    return user


def _is_admin(request):
    return request.user.is_authenticated and request.user.is_superuser


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
            _start_session(request, admin_user.username)
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
            normalized_status = _normalize_status(user.status)
            if normalized_status != user.status:
                user.status = normalized_status
                user.save(update_fields=['status'])

            if user.status in LOGIN_ALLOWED_STATUSES:
                if user.status != STATUS_ACTIVE:
                    user.status = STATUS_ACTIVE
                    user.save(update_fields=['status'])
                _start_session(request, user.email_id)
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
        password = request.POST.get('password', '')
        cpassword = request.POST.get('cpassword', '')

        if Registration.objects.filter(email_id=email).exists():
            messages.error(request, "Error. This email address is already registered.")
            return redirect('reg')

        if Registration.objects.filter(mobile=mobile).exists():
            messages.error(request, "Error. This mobile number is already registered.")
            return redirect('reg')

        if password != cpassword:
            messages.error(request, "Error. Password and confirm password do not match.")
            return redirect('reg')

        try:
            user_data = dict(
                name     = request.POST.get('name'),
                address  = request.POST.get('address'),
                dob      = request.POST.get('dob'),
                gender   = request.POST.get('gender'),
                email_id = email,
                mobile   = mobile,
                password = password,
                answer   = request.POST.get('answer'),
                status   = STATUS_PENDING
            )
            if request.FILES.get('img'):
                user_data['image'] = request.FILES['img']

            user = Registration.objects.create(**user_data)
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
        user_obj = _current_registration(request)
        if not user_obj:
            messages.warning(request, "Your session has expired or your account is not active. Please log in again.")
            return redirect('login')
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
    _clear_messages(request)
    try:
        if _is_admin(request):
            user_name = request.user.username
            role = "Admin"
            msgs = Message.objects.filter(status="sent").order_by("-id")
        else:
            user_obj = _current_registration(request)
            if not user_obj:
                return redirect("/login/")
            user_name = user_obj.name
            role = "User"
            msgs = Message.objects.filter(receiver=user_obj, status="sent").order_by("-id")

    except Registration.DoesNotExist:
        request.session.flush()
        return redirect('login')

    count = msgs.count()
    if count == 0:
        messages.info(request, "Your inbox is empty. No new messages.")
    else:
        messages.info(
            request,
            f"You have {count} message{'s' if count != 1 else ''} in your inbox. "
            f"Use Tab to navigate each message."
        )

    context = {
        "data": msgs,
        "role": role,
        "name": user_name,
        "data1": msgs.count(), # Inbox count
    }
    return render(request, "inbox.html", context)

# ─────────────────────────────────────────────
# COMPOSE / SEND
# ─────────────────────────────────────────────

def message(request):
    """
    Voice cues:
    - Recipient not found: "Recipient not found. Please check the email address and try again."
    - Sent:                "Your message with subject <subject> has been sent successfully."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    if request.method == "POST":
        receiver_email = request.POST.get("sendto", "").strip()
        receiver       = Registration.objects.filter(email_id=receiver_email).first()

        if receiver:
            subject = request.POST.get("subject", "")
            status = "draft" if "draft" in request.POST else "sent"
            Message.objects.create(
                sender   = user,
                receiver = receiver,
                subject  = subject,
                content  = request.POST.get("content"),
                status   = status
            )
            if status == "draft":
                messages.info(request, "Your message has been saved as a draft.")
                return redirect("/draft/")
            else:
                messages.success(
                    request,
                    f"Your message with subject '{subject}' has been sent successfully to {receiver.name}."
                )
                return redirect("/sent/")
        else:
            messages.error(
                request,
                "Recipient not found. Please check the email address and try again."
            )

    return render(request, "message.html", {
        "role": "User",
        "name": user.name,
    })


def save(request):
    """
    Saves a draft.
    Voice cue: "Your message has been saved as a draft."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

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
    current_user = _current_registration(request)
    if not current_user:
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
        "role":    "User",
        "name":    current_user.name,
    })


def message1(request):
    """
    Reply form submission.
    Voice cue: "Reply sent successfully."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

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
        "data": users,
        "role": "User",
        "name": user.name,
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
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    keyword = request.POST.get("se", "").strip()

    results = Message.objects.filter(receiver=user, content__icontains=keyword)
    count   = results.count()

    if count:
        messages.info(request, f"{count} message{'s' if count != 1 else ''} found matching '{keyword}'.")
    else:
        messages.info(request, f"No messages found matching '{keyword}'.")

    return render(request, "search.html", {
        "data3": results,
        "keyword": keyword,
        "role": "User",
        "name": user.name,
    })


# ─────────────────────────────────────────────
# SENT
# ─────────────────────────────────────────────

def sent(request):
    """
    Voice cues:
    - Empty:    "Your sent folder is empty."
    - Has mail: "You have <N> sent messages."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    _clear_messages(request)
    sent_msgs = Message.objects.filter(sender=user, status="sent").order_by("-id")
    count     = sent_msgs.count()

    if count == 0:
        messages.info(request, "Your sent folder is empty.")
    else:
        messages.info(request, f"You have {count} sent message{'s' if count != 1 else ''}.")

    return render(request, "sent.html", {
        "data": sent_msgs,
        "role": "User",
        "name": user.name,
    })


# ─────────────────────────────────────────────
# DRAFTS
# ─────────────────────────────────────────────

def draft(request):
    """
    Voice cues:
    - Empty:    "You have no saved drafts."
    - Has drafts: "You have <N> saved draft messages."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    _clear_messages(request)
    drafts = Message.objects.filter(sender=user, status="draft").order_by("-id")
    count  = drafts.count()

    if count == 0:
        messages.info(request, "You have no saved drafts.")
    else:
        messages.info(request, f"You have {count} saved draft message{'s' if count != 1 else ''}.")

    return render(request, "draft.html", {
        "data": drafts,
        "role": "User",
        "name": user.name,
    })


def draft1(request):
    """Opens a draft for editing."""
    user = _current_registration(request)
    if not user:
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
        "con":  msg_obj.content,
        "role": "User",
        "name": user.name,
    })


def draft2(request):
    """
    Sends a draft as a real email.
    Voice cue: "Your draft has been sent successfully."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

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
        "data": Registration.objects.all(),
        "role": "User",
        "name": user.name,
    })


# ─────────────────────────────────────────────
# ADMIN: USER MANAGEMENT
# ─────────────────────────────────────────────

def userview(request):
    """
    Voice cues:
    - Status updated: "User status has been updated to <status>."
    """
    if not _is_admin(request):
        messages.error(request, "Admin access required.")
        return redirect("/login/")

    user_id = request.GET.get("id")
    status  = _normalize_status(request.GET.get("status"))

    if user_id and request.GET.get("status"):
        Registration.objects.filter(id=user_id).update(status=status)
        messages.success(request, f"User status has been updated to {status}.")

    users = Registration.objects.all().order_by('-id')
    return render(request, "userview.html", {
        "data": users,
        "role": "Admin",
        "name": request.session.get('username', 'Admin'),
    })


# ─────────────────────────────────────────────
# PROFILE
# ─────────────────────────────────────────────

def profile(request):
    """
    Voice cue (spoken by template):
    "Viewing your profile. Name: <name>. Email: <email>."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    return render(request, "profile.html", {
        "data": user,
        "role": "User",
        "name": user.name,
    })


def editprofile(request):
    """
    Voice cues:
    - Success: "Your profile has been updated successfully."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    if request.method == "POST":
        user.name    = request.POST.get("name")
        user.address = request.POST.get("address")
        user.dob     = request.POST.get("dob")
        user.mobile  = request.POST.get("mobile")
        user.save()
        messages.success(request, "Your profile has been updated successfully.")
        return redirect("/profile/")

    return render(request, "editprofile.html", {
        "data": user,
        "role": "User",
        "name": user.name,
    })


def changeimage(request):
    """
    Voice cues:
    - Success: "Your profile photo has been updated."
    - No file: "No image selected. Please choose a file."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    if request.method == "POST":
        if request.FILES.get('img'):
            user.image = request.FILES['img']
            user.save()
            messages.success(request, "Your profile photo has been updated.")
        else:
            messages.error(request, "No image selected. Please choose a file.")
        return redirect("/profile/")

    return render(request, "changeimage.html", {
        "data": user,
        "role": "User",
        "name": user.name,
    })


# ─────────────────────────────────────────────
# FEEDBACK
# ─────────────────────────────────────────────

def feedback(request):
    """
    Voice cues:
    - Success: "Thank you. Your feedback has been submitted successfully."
    """
    user = _current_registration(request)
    if not user:
        return redirect("/login/")

    if request.method == "POST":
        Feedback.objects.create(
            sender    = user,
            subject   = request.POST.get("subject"),
            message   = request.POST.get("mycontent"),
            date      = datetime.date.today()
        )
        messages.success(request, "Thank you. Your feedback has been submitted successfully.")

    return render(request, "feedback.html", {
        "role": "User",
        "name": user.name,
    })


def viewfeedback(request):
    """
    Voice cue (spoken by template):
    "Viewing all feedback. <N> items found."
    """
    if not _is_admin(request):
        messages.error(request, "Admin access required.")
        return redirect("/login/")

    _clear_messages(request)
    data  = Feedback.objects.all().order_by('-id')
    count = data.count()

    if count == 0:
        messages.info(request, "No feedback submissions found.")
    else:
        messages.info(request, f"{count} feedback submission{'s' if count != 1 else ''} found.")

    return render(request, "viewfeedback.html", {
        "data": data,
        "role": "Admin",
        "name": request.session.get('username', 'Admin'),
    })


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
    user_obj = _current_registration(request)
    if not user_obj:
        return redirect('login')

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

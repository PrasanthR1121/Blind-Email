from django.db import models

class Registration(models.Model):
    name = models.CharField(max_length=100)
    address = models.TextField()
    dob = models.DateField()
    gender = models.CharField(max_length=10)
    email_id = models.EmailField(unique=True)
    mobile = models.CharField(max_length=15, unique=True)
    image = models.ImageField(upload_to='profiles/', default='profiles/default.png')
    password = models.CharField(max_length=100)
    answer = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return self.email_id

class Message(models.Model):
    sender = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="sent_messages")
    receiver = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name="received_messages")
    date = models.DateField(auto_now_add=True)
    subject = models.CharField(max_length=255)
    content = models.TextField()
    status = models.CharField(max_length=20)

    def __str__(self):
        return self.subject

class Feedback(models.Model):
    sender = models.ForeignKey(Registration, on_delete=models.CASCADE)
    message = models.TextField()
    subject = models.CharField(max_length=255)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.subject
import uuid
from django.db import models
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from location.models import HealthFacility 
from core import fields, TimeUtils, models as core_models




class Notice(models.Model):
    PRIORITY_CHOICES = (
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(max_length=6, choices=PRIORITY_CHOICES, default='MEDIUM')
    health_facility = models.ForeignKey(HealthFacility, on_delete=models.CASCADE, related_name='notices')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'tbl_notices'

    def __str__(self):
        return f"{self.title} ({self.priority}) - {self.health_facility}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.send_notification()

    def send_notification(self):
        """Send email or SMS to health facility if configured."""
        hf = self.health_facility
        if not hf:
            return

        # Check if email or SMS is enabled in settings
        if getattr(settings, "NOTICE_EMAIL_ENABLED", False) and hf.email:
            self.send_email_notification(hf.email)
        if getattr(settings, "NOTICE_SMS_ENABLED", False) and hf.phone:
            self.send_sms_notification(hf.phone)

    def send_email_notification(self, email):
        subject = f"New Notice: {self.title}"
        message = f"Priority: {self.priority}\nDescription: {self.description}"
        from_email = settings.DEFAULT_FROM_EMAIL
        try:
            send_mail(subject, message, from_email, [email], fail_silently=False)
        except Exception as e:
            print(f"Failed to send email: {e}")



class NoticeMutation(core_models.UUIDModel, core_models.ObjectMutation):
    notice = models.ForeignKey(Notice, models.DO_NOTHING,
                                 related_name='mutations')
    mutation = models.ForeignKey(
        core_models.MutationLog, models.DO_NOTHING, related_name='category')

    class Meta:
        managed = True
        db_table = "tbl_noticeMutations"



class NoticeAttachment(core_models.UUIDModel, core_models.UUIDVersionedModel):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  
    notice = models.ForeignKey(
        Notice, on_delete=models.CASCADE, related_name='attachments')
    general_type = models.CharField(
        max_length=4,
        choices=(('FILE', 'File'), ('URL', 'URL')),
        default='FILE',
        help_text="Indicates whether this is a file attachment or a URL link."
    )
    type = models.TextField(blank=True, null=True, help_text="Custom type description if needed.")
    title = models.TextField(blank=True, null=True, help_text="Title or name of the attachment.")
    date = fields.DateField(blank=True, default=TimeUtils.now, help_text="Date of the attachment.")
    filename = models.TextField(blank=True, null=True, help_text="Original filename of the uploaded file.")
    mime = models.TextField(blank=True, null=True, help_text="MIME type of the file (e.g., 'application/pdf').")
    module = models.TextField(blank=False, null=True, default="notice", help_text="Module identifier for future core integration.")
    url = models.TextField(blank=True, null=True, help_text="URL link to the attachment if general_type is 'URL'.")
    document = models.TextField(blank=True, null=True, help_text="Base64-encoded file content if general_type is 'FILE'.")

    class Meta:
        db_table = 'tbl_noticeAttachments'

    def __str__(self):
        return f"{self.title or self.filename or 'Unnamed'} - {self.notice.title}"
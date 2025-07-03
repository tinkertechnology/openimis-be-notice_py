from django.core.mail import send_mail
from django.utils.html import escape
from django.core.exceptions import ValidationError

def send_notice_email(recipients: list, title: str, description: str, priority: str) -> None:
    """
    Send a notice email to the specified recipients with the given title, description, and priority.

    Args:
        recipients (list): List of email addresses of the recipients.
        title (str): The title of the notice.
        description (str): The description of the notice.
        priority (str): The priority of the notice.

    Raises:
        ValidationError: If no valid recipients are provided or email sending fails.
    """
    try:
        if not recipients:
            raise ValidationError("No valid recipients provided")

        # Define the HTML email template inline
        html_template = """
        <!doctype html>
        <html>
          <head>
            <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
          </head>
          <body style="font-family: sans-serif;">
            <div style="display: block; margin: auto; max-width: 600px;" class="main">
              <h1 style="font-size: 18px; font-weight: bold; margin-top: 20px">{title}</h1>
              <p>{description}</p>
              <p><strong>Priority:</strong> {priority}</p>
            </div>
            <style>
              .main {{ background-color: white; }}
            </style>
          </body>
        </html>
        """

        # Replace placeholders with sanitized values
        html_message = html_template.format(
            title=escape(title),
            description=escape(description),
            priority=escape(priority)
        )

        # Prepare email content
        subject = f"Notice: {title}"
        message = description  # Plain text fallback

        # Send email to all recipients
        send_mail(
            subject=subject,
            message=message,
            from_email="no-reply@openimis.org",
            recipient_list=recipients,
            html_message=html_message,
            fail_silently=False,
        )
    except Exception as exc:
        raise ValidationError(f"Failed to send email: {str(exc)}")
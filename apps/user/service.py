from django.core.mail import EmailMessage
from django.conf import settings
from django.template.loader import render_to_string

def send_welcome_email(user):
    try:
        # Render HTML email template
        html_content = render_to_string('otp_email_template/welcome_email.html', {
            'user': user,
            'company_name': getattr(settings, 'COMPANY_NAME', 'Our Platform'),
        })
        
        # Send HTML email
        email_message = EmailMessage(
            subject="Welcome to Our Platform",
            body=html_content,
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@yourdomain.com'),
            to=[user.email],
        )
        email_message.content_subtype = 'html'
        email_message.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending welcome email: {str(e)}")


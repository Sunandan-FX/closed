from django.conf import settings
from django.http import HttpResponseForbidden


class AdminAccessWhitelistMiddleware:
    """
    Restrict /admin access to:
    1) superusers, or
    2) staff users whose email is whitelisted in ADMIN_ALLOWED_EMAILS.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith("/admin/") and request.user.is_authenticated:
            if request.user.is_superuser:
                return self.get_response(request)

            if not request.user.is_staff:
                return HttpResponseForbidden("Admin access denied.")

            allowed_emails = {
                email.strip().lower()
                for email in getattr(settings, "ADMIN_ALLOWED_EMAILS", [])
                if email and email.strip()
            }
            user_email = (request.user.email or "").strip().lower()

            if allowed_emails and user_email not in allowed_emails:
                return HttpResponseForbidden("Admin access denied.")

        return self.get_response(request)


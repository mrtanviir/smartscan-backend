import logging
from accounts.models import AuditLog

logger = logging.getLogger('django')

class AuditTrailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # শুধুমাত্র স্টেট চেঞ্জিং রিকুয়েস্ট ট্র্যাকিং করা (POST, PUT, PATCH, DELETE)
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE'] and getattr(request, 'user', None) and request.user.is_authenticated:
            try:
                user = request.user
                user_phone = getattr(user, 'phone', user.get_username())
                user_role = getattr(user, 'role', 'N/A')
                ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR')) or '127.0.0.1'
                if ',' in ip:
                    ip = ip.split(',')[0].strip()
                
                action_name = f"{request.method} {request.path}"
                details = f"User '{user_phone}' ({user_role}) performed {request.method} on {request.path}"
                
                AuditLog.objects.create(
                    user=user,
                    action=action_name,
                    ip_address=ip if len(ip) <= 45 else '127.0.0.1',
                    details=details
                )
                logger.info(f"AUDIT_LOG: {details} from IP {ip}")
            except Exception:
                pass
            
        return response

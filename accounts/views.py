import random
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from config.responses import api_response
from branches.models import Branch
from .models import User, Role, AuditLog, CustomerNotification
from .serializers import AdminLoginSerializer, UserSerializer

# প্রোডাকশনে এটি Redis বা SMS Gateway (e.g. Greenweb, SSL Wireless)-এ যাবে
OTP_STORAGE = {}

def format_bengali_time_ago(dt):
    """Formats datetime into localized relative time e.g. ৫ মিনিট আগে, ২ ঘণ্টা আগে, গতকাল, ৬:৩০ পিএম, ৩ দিন আগে"""
    if not dt:
        return ""
    now = timezone.now()
    diff = now - dt
    seconds = int(diff.total_seconds())

    digits = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    def to_bn(num):
        return "".join(digits.get(c, c) for c in str(num))

    if seconds < 60:
        return "এইমাত্র"
    elif seconds < 3600:
        mins = max(1, seconds // 60)
        return f"{to_bn(mins)} মিনিট আগে"
    elif seconds < 86400:
        hours = max(1, seconds // 3600)
        return f"{to_bn(hours)} ঘণ্টা আগে"
    elif seconds < 172800:
        hour = dt.hour
        hour_12 = hour % 12 or 12
        period = "এএম" if hour < 12 else "পিএম"
        return f"গতকাল, {to_bn(hour_12)}:{to_bn(f'{dt.minute:02d}')} {period}"
    else:
        days = seconds // 86400
        return f"{to_bn(days)} দিন আগে"


class SendOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        if not phone:
            return api_response(status=False, message='ফোন নম্বর আবশ্যক', code=status.HTTP_400_BAD_REQUEST)
        
        # ৪-সংখ্যার ডেমো ওটিপি জেনারেট (যেমন: 1234 বা Random)
        otp = "1234"  # Test mode-এ ফিক্সড রাখতে পারেন অথবা str(random.randint(1000, 9999))
        OTP_STORAGE[phone] = otp
        
        return api_response(
            status=True,
            message=f'{phone} নম্বরে OTP পাঠানো হয়েছে।',
            data={'test_otp': otp, 'phone': phone},
            code=status.HTTP_200_OK
        )


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get('phone')
        otp = request.data.get('otp')
        name = request.data.get('name', 'Customer')

        if not phone or not otp:
            return api_response(status=False, message='ফোন নম্বর এবং ওটিপি উভয়ই আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        if OTP_STORAGE.get(phone) == str(otp):
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={'username': phone, 'role': Role.CUSTOMER, 'first_name': name}
            )
            refresh = RefreshToken.for_user(user)
            return api_response(
                status=True,
                message='লগইন সফল হয়েছে',
                data={
                    'token': str(refresh.access_token),
                    'refresh': str(refresh),
                    'user': UserSerializer(user).data
                },
                code=status.HTTP_200_OK
            )
        return api_response(status=False, message='ভুল OTP প্রদান করেছেন', code=status.HTTP_400_BAD_REQUEST)


class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            val_data = serializer.validated_data
            return api_response(
                status=True,
                message='অ্যাডমিন লগইন সফল হয়েছে',
                data={
                    'token': val_data['access'],
                    'access': val_data['access'],
                    'refresh': val_data['refresh'],
                    'user': val_data['user']
                },
                code=status.HTTP_200_OK
            )
        errors = list(serializer.errors.values())[0] if serializer.errors else "লগইন তথ্য সঠিক নয়"
        error_msg = errors[0] if isinstance(errors, list) else str(errors)
        return api_response(status=False, message=error_msg, data=serializer.errors, code=status.HTTP_400_BAD_REQUEST)


class CustomerProfileView(APIView):
    def get(self, request):
        user = request.user
        branch_data = {
            'id': user.branch.id,
            'name': user.branch.name_bn or user.branch.name,
            'address': user.branch.address
        } if user.branch else {
            'id': 1,
            'name': 'ধানমন্ডি শাখা',
            'address': 'হাউজ ১২, রোড ২৭, ধানমন্ডি, ঢাকা'
        }

        data = {
            'user': {
                'id': user.id,
                'name': user.first_name or user.username,
                'phone': user.phone,
                'email': user.email or 'N/A',
                'member_id': f"SS-{user.id:05d}",
                'loyalty_points': user.loyalty_points,
                'loyalty_value_bdt': user.loyalty_points,
                'default_branch': branch_data,
            }
        }
        return api_response(
            status=True,
            message='কাস্টমার প্রোফাইল তথ্য সফলভাবে পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

    def patch(self, request):
        user = request.user
        name = request.data.get('name')
        email = request.data.get('email')
        default_branch_id = request.data.get('default_branch_id')

        if name:
            user.first_name = name
            user.username = name
        if email:
            user.email = email
        if default_branch_id:
            try:
                branch = Branch.objects.get(id=default_branch_id)
                user.branch = branch
            except Branch.DoesNotExist:
                return api_response(status=False, message='অবৈধ ব্রাঞ্চ আইডি', code=status.HTTP_404_NOT_FOUND)

        user.save()

        branch_data = {
            'id': user.branch.id,
            'name': user.branch.name_bn or user.branch.name,
            'address': user.branch.address
        } if user.branch else {
            'id': 1,
            'name': 'ধানমন্ডি শাখা',
            'address': 'হাউজ ১২, রোড ২৭, ধানমন্ডি, ঢাকা'
        }

        data = {
            'user': {
                'id': user.id,
                'name': user.first_name or user.username,
                'phone': user.phone,
                'email': user.email or 'N/A',
                'member_id': f"SS-{user.id:05d}",
                'loyalty_points': user.loyalty_points,
                'loyalty_value_bdt': user.loyalty_points,
                'default_branch': branch_data,
            }
        }
        return api_response(
            status=True,
            message='প্রোফাইল সফলভাবে আপডেট করা হয়েছে',
            data=data,
            code=status.HTTP_200_OK
        )


# ==============================================================================
#  🔔 Customer Notifications APIs
# ==============================================================================

class CustomerNotificationListView(APIView):
    """
    Image 2: কাস্টমার নোটিফিকেশন তালিকা (সব, অর্ডার ও কার্ট, অফার, পয়েন্ট)
    """
    def get(self, request):
        user = request.user
        cat = request.query_params.get('category', 'ALL').upper()

        notifications_qs = CustomerNotification.objects.filter(user=user)
        if cat in ['ORDER', 'CART', 'ORDERS']:
            notifications_qs = notifications_qs.filter(category__in=['ORDER', 'CART'])
        elif cat in ['OFFER', 'OFFERS']:
            notifications_qs = notifications_qs.filter(category='OFFER')
        elif cat in ['LOYALTY', 'POINTS', 'POINT']:
            notifications_qs = notifications_qs.filter(category='LOYALTY')

        unread_count = CustomerNotification.objects.filter(user=user, is_read=False).count()

        data = []
        for n in notifications_qs:
            data.append({
                'id': n.id,
                'title': n.title,
                'message': n.message,
                'category': n.category,
                'icon_type': n.icon_type,
                'action_type': n.action_type,
                'action_data': n.action_data,
                'is_read': n.is_read,
                'time_ago': format_bengali_time_ago(n.created_at),
                'created_at': n.created_at.isoformat()
            })

        return api_response(
            status=True,
            message='নোটিফিকেশন তালিকা পাওয়া গেছে',
            data={
                'unread_count': unread_count,
                'notifications': data
            },
            code=status.HTTP_200_OK
        )


class CustomerNotificationMarkReadView(APIView):
    """
    নোটিফিকেশন পঠিত হিসেবে চিহ্নিত করা (সিঙ্গেল বা অল মার্ক রিড)
    """
    def patch(self, request, pk=None):
        if pk:
            try:
                n = CustomerNotification.objects.get(id=pk, user=request.user)
                n.is_read = True
                n.save()
                return api_response(status=True, message='নোটিফিকেশন পঠিত হিসেবে চিহ্নিত হয়েছে', data={'id': n.id, 'is_read': True}, code=status.HTTP_200_OK)
            except CustomerNotification.DoesNotExist:
                return api_response(status=False, message='নোটিফিকেশন পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        else:
            CustomerNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
            return api_response(status=True, message='সকল নোটিফিকেশন পঠিত হিসেবে চিহ্নিত হয়েছে', data={'all_read': True}, code=status.HTTP_200_OK)

    def post(self, request):
        CustomerNotification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        return api_response(status=True, message='সকল নোটিফিকেশন পঠিত হিসেবে চিহ্নিত হয়েছে', data={'all_read': True}, code=status.HTTP_200_OK)


# ==============================================================================
#  Staff & Audit Logs
# ==============================================================================

class AdminUserManagementView(APIView):
    def get(self, request):
        users = User.objects.exclude(role=Role.CUSTOMER).order_by('-id')
        data = [{
            'id': u.id,
            'name': u.get_full_name() or u.username,
            'email': u.email,
            'phone': u.phone,
            'role': u.role,
            'branch': u.branch.name if u.branch else "Head Office",
            'is_active': u.is_active
        } for u in users]
        return api_response(
            status=True,
            message='স্টাফ তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

    def post(self, request):
        phone = request.data.get('phone')
        email = request.data.get('email')
        role = request.data.get('role')
        branch_id = request.data.get('branch_id')
        password = request.data.get('password')

        if not phone or not password or not role:
            return api_response(status=False, message='phone, password এবং role আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        user = User.objects.create_user(
            username=phone,
            phone=phone,
            email=email or '',
            role=role,
            branch_id=branch_id if branch_id else None,
            password=password
        )
        return api_response(
            status=True,
            message=f'ইউজার {role} হিসেবে তৈরি হয়েছে',
            data={'user_id': user.id},
            code=status.HTTP_201_CREATED
        )


class AuditLogListView(APIView):
    def get(self, request):
        logs = AuditLog.objects.all().order_by('-timestamp')[:50]
        data = [{
            'id': l.id,
            'user': l.user.phone if l.user else 'System',
            'action': l.action,
            'ip': l.ip_address,
            'details': l.details,
            'time': l.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        } for l in logs]
        return api_response(
            status=True,
            message='অডিট লগ তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

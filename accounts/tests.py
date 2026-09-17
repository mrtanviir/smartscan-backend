from datetime import timedelta
import time
from django.test import TestCase, RequestFactory
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, Role, AuditLog
from accounts.middleware import AuditTrailMiddleware
from branches.models import Branch

class AccountsAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.factory = RequestFactory()
        self.branch1 = Branch.objects.create(
            name='Dhanmondi Branch',
            code='DHA-01',
            latitude=23.7461,
            longitude=90.3742,
            address='Dhanmondi 27, Dhaka'
        )
        self.branch2 = Branch.objects.create(
            name='Gulshan Branch',
            code='GUL-01',
            latitude=23.7925,
            longitude=90.4078,
            address='Gulshan 2, Dhaka'
        )
        self.admin_user = User.objects.create_user(
            phone='01700000010',
            username='admin_asif',
            email='admin@smartscan.com',
            password='adminpassword123',
            role=Role.SUPER_ADMIN
        )
        self.customer_user = User.objects.create_user(
            phone='01800000010',
            username='customer_user',
            email='customer@gmail.com',
            password='customerpassword123',
            role=Role.CUSTOMER,
            branch=self.branch1,
            loyalty_points=120
        )

    def test_send_otp_success(self):
        url = reverse('send-otp')
        response = self.client.post(url, {'phone': '01911223344'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('test_otp', response.data['data'])

    def test_verify_otp_success_creates_user(self):
        send_url = reverse('send-otp')
        self.client.post(send_url, {'phone': '01999887766'}, format='json')

        verify_url = reverse('verify-otp')
        response = self.client.post(verify_url, {
            'phone': '01999887766',
            'otp': '1234',
            'name': 'Rahim'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('token', response.data['data'])
        self.assertEqual(response.data['data']['user']['phone'], '01999887766')

    def test_token_lifetime_is_30_days(self):
        refresh = RefreshToken.for_user(self.customer_user)
        access_token = refresh.access_token
        # Expiration should be roughly 30 days from now (2592000 seconds)
        exp_time = access_token['exp']
        iat_time = access_token['iat']
        duration_days = (exp_time - iat_time) / (24 * 3600)
        self.assertAlmostEqual(duration_days, 30, delta=1)

    def test_invalid_token_returns_standard_error(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION='Bearer invalid_or_expired_token_12345')
        url = reverse('customer-profile')
        response = client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertFalse(response.data['status'])
        self.assertEqual(response.data['code'], 401)
        self.assertIn('message', response.data)

    def test_admin_login_success(self):
        url = reverse('admin-login')
        response = self.client.post(url, {
            'email': 'admin@smartscan.com',
            'password': 'adminpassword123'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('access', response.data['data'])
        self.assertEqual(response.data['data']['user']['role'], 'SUPER_ADMIN')

    def test_customer_profile_get_and_patch(self):
        self.client.force_authenticate(user=self.customer_user)
        url = reverse('customer-profile')
        
        # GET profile
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['data']['user']['phone'], '01800000010')
        self.assertEqual(response.data['data']['user']['loyalty_points'], 120)

        # PATCH profile (Customer profile update)
        patch_res = self.client.patch(url, {
            'name': 'Tanvir Saheb',
            'email': 'tanvir@example.com',
            'default_branch_id': self.branch2.id
        }, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_res.data['status'])
        self.assertEqual(patch_res.data['data']['user']['name'], 'Tanvir Saheb')
        self.assertEqual(patch_res.data['data']['user']['email'], 'tanvir@example.com')
        self.assertEqual(patch_res.data['data']['user']['default_branch']['id'], self.branch2.id)

    def test_admin_user_management(self):
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-users')

        # List staff
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertTrue(response_data := res_get.data['data'])

        # Create new Branch Manager
        res_post = self.client.post(url, {
            'phone': '01755555555',
            'email': 'sadia@smartscan.com',
            'role': Role.BRANCH_MANAGER,
            'branch_id': self.branch1.id,
            'password': 'managerpassword123'
        }, format='json')
        self.assertEqual(res_post.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_post.data['status'])
        self.assertTrue(User.objects.filter(phone='01755555555').exists())

    def test_audit_logs_list(self):
        AuditLog.objects.create(
            user=self.admin_user,
            action="PRICE_CHANGE",
            ip_address="127.0.0.1",
            details="Product #1 price changed from 90 to 95"
        )
        self.client.force_authenticate(user=self.admin_user)
        url = reverse('admin-audit-logs')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['action'], 'PRICE_CHANGE')

    def test_customer_notifications_flow(self):
        from accounts.models import CustomerNotification
        
        # Create unread notifications
        n1 = CustomerNotification.objects.create(
            user=self.customer_user,
            title='গেট পাস প্রস্তুত!',
            message='আপনার ধানমন্ডি শাখার গেট পাস প্রস্তুত!',
            category='ORDER',
            icon_type='GATE_PASS',
            is_read=False
        )
        n2 = CustomerNotification.objects.create(
            user=self.customer_user,
            title='আজকের স্পেশাল অফার!',
            message='সয়াবিন তেলে বিশেষ ছাড়!',
            category='OFFER',
            icon_type='OFFER',
            is_read=False
        )

        self.client.force_authenticate(user=self.customer_user)
        url = reverse('customer-notifications')

        # 1. Get All Notifications
        res_all = self.client.get(url)
        self.assertEqual(res_all.status_code, status.HTTP_200_OK)
        self.assertTrue(res_all.data['status'])
        self.assertEqual(res_all.data['data']['unread_count'], 2)
        self.assertEqual(len(res_all.data['data']['notifications']), 2)

        # 2. Filter Category OFFER
        res_offer = self.client.get(url, {'category': 'OFFER'})
        self.assertEqual(len(res_offer.data['data']['notifications']), 1)
        self.assertEqual(res_offer.data['data']['notifications'][0]['title'], 'আজকের স্পেশাল অফার!')

        # 3. Mark Single as Read
        read_url = reverse('customer-notification-read', kwargs={'pk': n1.id})
        res_read = self.client.patch(read_url)
        self.assertEqual(res_read.status_code, status.HTTP_200_OK)
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # 4. Mark All Read
        all_read_url = reverse('customer-notifications-mark-all-read')
        res_all_read = self.client.post(all_read_url)
        self.assertEqual(res_all_read.status_code, status.HTTP_200_OK)
        n2.refresh_from_db()
        self.assertTrue(n2.is_read)

from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Role
from branches.models import Branch
from products.models import Product
from orders.models import Order, OrderFeedback, CustomerCartItem

class OrderFullFlowTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(
            phone='01711000000',
            username='order_user',
            password='testpassword123',
            role=Role.CUSTOMER,
            loyalty_points=50
        )
        self.manager = User.objects.create_user(
            phone='01722000000',
            username='manager_user',
            password='testpassword123',
            role=Role.BRANCH_MANAGER
        )
        self.client.force_authenticate(user=self.customer)

        self.branch = Branch.objects.create(
            name='Gulshan Branch',
            name_bn='গুলশান শাখা',
            code='GUL-01',
            latitude=23.7925,
            longitude=90.4078,
            address='Gulshan 2, Dhaka'
        )
        self.product1 = Product.objects.create(
            barcode='11111111',
            name='Rice 5kg',
            name_bn='মিনিকেট চাল - ৫ কেজি',
            category='Grocery',
            unit_price=350.00,
            cost_price=300.00,
            weight_grams=5000,
            discount_amount=0.00
        )
        self.product2 = Product.objects.create(
            barcode='22222222',
            name='Oil 2L',
            name_bn='রূপচাঁদা সয়াবিন তেল - ২ লিটার',
            category='Grocery',
            unit_price=380.00,
            cost_price=340.00,
            weight_grams=2000,
            discount_amount=0.00
        )

    def test_customer_cart_crud_flow(self):
        # 1. Cart is initially empty
        cart_url = reverse('cart-list')
        res_get = self.client.get(cart_url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_get.data['data']['items']), 0)
        self.assertEqual(res_get.data['data']['total_items_count'], 0)

        # 2. Add product via barcode scan
        add_url = reverse('cart-add')
        res_add = self.client.post(add_url, {
            'barcode': '11111111',
            'store_id': self.branch.id,
            'quantity': 1
        }, format='json')
        self.assertEqual(res_add.status_code, status.HTTP_200_OK)
        self.assertTrue(res_add.data['status'])

        # 3. Add second product
        self.client.post(add_url, {
            'product_id': self.product2.id,
            'store_id': self.branch.id,
            'quantity': 1
        }, format='json')

        # 4. Check cart items count
        res_get2 = self.client.get(cart_url)
        self.assertEqual(len(res_get2.data['data']['items']), 2)
        self.assertEqual(res_get2.data['data']['total_items_count'], 2)
        self.assertEqual(res_get2.data['data']['subtotal'], 730.00)

        # 5. Increment quantity
        update_url = reverse('cart-update')
        res_patch = self.client.patch(update_url, {
            'product_id': self.product1.id,
            'store_id': self.branch.id,
            'action': 'increment'
        }, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.data['data']['quantity'], 2)

        # 6. Clear cart
        clear_url = reverse('cart-clear')
        res_clear = self.client.delete(clear_url)
        self.assertEqual(res_clear.status_code, status.HTTP_200_OK)
        self.assertEqual(CustomerCartItem.objects.filter(customer=self.customer).count(), 0)

    def test_bill_review_and_calculation(self):
        url = reverse('checkout-review')
        payload = {
            'store_id': self.branch.id,
            'items': [
                {'product_id': self.product1.id, 'quantity': 1},
                {'product_id': self.product2.id, 'quantity': 1}
            ],
            'payment_method': 'bKash',
            'use_loyalty_points': True
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        data = response.data['data']
        self.assertEqual(data['subtotal'], 730.00)
        self.assertEqual(data['total_weight_grams'], 7000)
        self.assertEqual(data['payment_method_discount'], 25.00)  # bKash discount
        self.assertEqual(data['user_loyalty_points'], 50)

    def test_checkout_order_and_active_gate_pass(self):
        # 1. Checkout
        url = reverse('checkout-create')
        payload = {
            'store_id': self.branch.id,
            'items': [
                {'product_id': self.product1.id, 'quantity': 1},
                {'product_id': self.product2.id, 'quantity': 1}
            ],
            'payment_method': 'Cash'
        }
        response = self.client.post(url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['data']['expected_weight_grams'], 7000)
        self.assertIn('qr_code_image', response.data['data'])
        self.assertTrue(response.data['data']['qr_code_image'].startswith('data:image/png;base64,'))
        self.assertIn('security_qr_payload', response.data['data'])
        created_order_number = response.data['data']['order_id']

        # 2. Retrieve Receipt
        receipt_url = reverse('order-receipt', kwargs={'order_number': created_order_number})
        receipt_res = self.client.get(receipt_url)
        self.assertEqual(receipt_res.status_code, status.HTTP_200_OK)
        self.assertTrue(receipt_res.data['status'])
        self.assertEqual(receipt_res.data['data']['order_number'], created_order_number)
        self.assertEqual(len(receipt_res.data['data']['items']), 2)

        # 3. Retrieve Active Gate Pass
        active_url = reverse('active-gate-pass')
        active_res = self.client.get(active_url)
        self.assertEqual(active_res.status_code, status.HTTP_200_OK)
        self.assertTrue(active_res.data['status'])
        self.assertTrue(active_res.data['data']['has_active_pass'])
        self.assertEqual(active_res.data['data']['order_number'], created_order_number)
        self.assertEqual(active_res.data['data']['status'], 'PAID')

    @patch('orders.sslcommerz.requests.post')
    def test_sslcommerz_initiate_session(self, mock_post):
        mock_post.return_value.json.return_value = {
            'status': 'SUCCESS',
            'GatewayPageURL': 'https://sandbox.sslcommerz.com/EasyCheckOut/testcde123',
            'sessionkey': 'TEST_SESSION_KEY_123'
        }
        order = Order.objects.create(
            order_number='SS998877',
            customer=self.customer,
            branch=self.branch,
            total_amount=500.00,
            expected_weight_grams=5000,
            status='PENDING'
        )
        url = reverse('sslcommerz-initiate')
        response = self.client.post(url, {'order_number': 'SS998877'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['data']['payment_url'], 'https://sandbox.sslcommerz.com/EasyCheckOut/testcde123')

    @patch('orders.sslcommerz.requests.get')
    def test_sslcommerz_success_callback_and_validate(self, mock_get):
        mock_get.return_value.json.return_value = {
            'status': 'VALID',
            'tran_id': 'SS998877',
            'val_id': 'VAL_12345678',
            'amount': '500.00',
            'card_type': 'VISA-CityBank',
            'bank_tran_id': 'BANK_TXN_001'
        }
        order = Order.objects.create(
            order_number='SS998877',
            customer=self.customer,
            branch=self.branch,
            total_amount=500.00,
            expected_weight_grams=5000,
            status='PENDING'
        )
        # Direct API validation
        val_url = reverse('sslcommerz-validate')
        val_res = self.client.post(val_url, {'val_id': 'VAL_12345678', 'tran_id': 'SS998877'}, format='json')
        self.assertEqual(val_res.status_code, status.HTTP_200_OK)
        self.assertTrue(val_res.data['status'])
        order.refresh_from_db()
        self.assertEqual(order.status, 'PAID')
        self.assertTrue(order.qr_code_image.startswith('data:image/png;base64,'))

    def test_customer_order_history_and_feedback_flow(self):
        order = Order.objects.create(
            order_number='ORD-TEST-001',
            customer=self.customer,
            branch=self.branch,
            total_amount=730.00,
            expected_weight_grams=7000,
            status='PAID'
        )
        # Check history
        history_url = reverse('customer-orders')
        history_res = self.client.get(history_url)
        self.assertEqual(history_res.status_code, status.HTTP_200_OK)
        self.assertTrue(history_res.data['status'])
        self.assertEqual(len(history_res.data['data']), 1)

        # Submit Feedback (2 Stars -> Low Rating)
        feedback_url = reverse('customer-order-feedback', kwargs={'order_number': 'ORD-TEST-001'})
        fb_res = self.client.post(feedback_url, {
            'rating': 2,
            'complaint_text': 'One bag had a leak.'
        }, format='json')
        self.assertEqual(fb_res.status_code, status.HTTP_200_OK)
        self.assertTrue(fb_res.data['status'])

        feedback = OrderFeedback.objects.get(order=order)
        self.assertEqual(feedback.rating, 2)
        self.assertEqual(feedback.status, 'PENDING')

        # Manager portal view & resolve
        self.client.force_authenticate(user=self.manager)
        manager_url = reverse('admin-feedback-list')
        complaints_res = self.client.get(manager_url)
        self.assertEqual(complaints_res.status_code, status.HTTP_200_OK)
        self.assertTrue(complaints_res.data['status'])
        self.assertEqual(len(complaints_res.data['data']), 1)

        # Resolve complaint
        resolve_url = reverse('admin-feedback-detail', kwargs={'pk': feedback.id})
        resolve_res = self.client.patch(resolve_url, {'resolution_note': 'Refunded and apologetic voucher sent.'}, format='json')
        self.assertEqual(resolve_res.status_code, status.HTTP_200_OK)
        self.assertTrue(resolve_res.data['status'])
        feedback.refresh_from_db()
        self.assertEqual(feedback.status, 'RESOLVED')
        self.assertEqual(feedback.resolved_by, self.manager)

    def test_gate_verification_and_manual_override(self):
        order = Order.objects.create(
            order_number='ORD-TEST-002',
            customer=self.customer,
            branch=self.branch,
            total_amount=730.00,
            expected_weight_grams=7000,
            status='PAID'
        )
        # Gate verify exact match
        url = reverse('security-verify')
        res_pass = self.client.post(url, {
            'order_number': 'ORD-TEST-002',
            'actual_weight_grams': 7010
        }, format='json')
        self.assertEqual(res_pass.status_code, status.HTTP_200_OK)
        self.assertTrue(res_pass.data['status'])
        self.assertEqual(res_pass.data['data']['status'], 'MATCHED')

        # Manual Override
        override_url = reverse('security-override')
        res_override = self.client.post(override_url, {
            'order_number': 'ORD-TEST-002',
            'security_pin': '9999'
        }, format='json')
        self.assertEqual(res_override.status_code, status.HTTP_200_OK)
        self.assertTrue(res_override.data['status'])

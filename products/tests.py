from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from products.models import Product
from branches.models import Branch
from inventory.models import Inventory
from accounts.models import User, Role

class ProductAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            phone='01700000001',
            username='cashier1',
            password='testpassword123',
            role=Role.CUSTOMER
        )
        self.client.force_authenticate(user=self.user)

        self.branch = Branch.objects.create(
            name='Dhanmondi Branch',
            code='DHA-01',
            latitude=23.7461,
            longitude=90.3742,
            address='Dhanmondi 27, Dhaka'
        )
        self.product = Product.objects.create(
            barcode='8941100552211',
            name='Fresh Milk 1L',
            name_bn='তাজা দুধ ১ লিটার',
            category='Dairy',
            unit_price=90.00,
            cost_price=75.00,
            discount_amount=10.00,
            weight_grams=1030
        )
        self.inventory = Inventory.objects.create(
            branch=self.branch,
            product=self.product,
            stock_quantity=50
        )

    def test_product_scan_success(self):
        url = reverse('product-scan')
        response = self.client.get(url, {'barcode': '8941100552211', 'store_id': self.branch.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(response.data['data']['barcode'], '8941100552211')
        self.assertEqual(response.data['data']['available_stock'], 50)
        self.assertEqual(response.data['data']['weight_grams'], 1030)

    def test_today_best_offers_nearby(self):
        url = reverse('product-offers')
        # In range (30 km)
        res_near = self.client.get(url, {'lat': '23.7461', 'lng': '90.3742', 'radius_km': '30'})
        self.assertEqual(res_near.status_code, status.HTTP_200_OK)
        self.assertTrue(res_near.data['status'])
        self.assertGreaterEqual(res_near.data['data']['total_offers'], 1)
        first_offer = res_near.data['data']['offers'][0]
        self.assertEqual(first_offer['product_id'], self.product.id)
        self.assertEqual(first_offer['formatted_offer_price'], '৳80')

        # Out of range (e.g. coordinates 0,0)
        res_far = self.client.get(url, {'lat': '0.0', 'lng': '0.0', 'radius_km': '30'})
        self.assertEqual(res_far.status_code, status.HTTP_200_OK)
        self.assertEqual(res_far.data['data']['total_offers'], 0)
        self.assertIn('কোনো সুপারশপের অফার পাওয়া যায়নি', res_far.data['message'])

    def test_admin_product_list_create(self):
        url = reverse('admin-products')
        
        # Test List
        res_list = self.client.get(url)
        self.assertEqual(res_list.status_code, status.HTTP_200_OK)
        self.assertTrue(res_list.data['status'])
        self.assertEqual(len(res_list.data['data']), 1)
        self.assertEqual(res_list.data['data'][0]['margin'], 15.0)

        # Test Create
        res_create = self.client.post(url, {
            'barcode': '998877665544',
            'name': 'Basmati Rice 5kg',
            'category': 'Grocery',
            'unit_price': 550.00,
            'cost_price': 480.00,
            'weight_grams': 5000,
            'is_active': True
        }, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_create.data['status'])
        self.assertTrue(Product.objects.filter(barcode='998877665544').exists())

    def test_admin_product_detail_update(self):
        url = reverse('admin-product-detail', kwargs={'id': self.product.id})
        
        # Test Retrieve
        res_get = self.client.get(url)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertTrue(res_get.data['status'])
        self.assertEqual(res_get.data['data']['name'], 'Fresh Milk 1L')

        # Test Patch Price
        res_patch = self.client.patch(url, {'unit_price': 95.00}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.assertEqual(float(self.product.unit_price), 95.00)

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Role
from branches.models import Branch
from products.models import Product
from inventory.models import Inventory, StockTransfer, InventoryMovement
from orders.models import Order

class InventoryAndDashboardAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            phone='01711223399',
            username='admin_inventory',
            password='testpassword123',
            role=Role.SUPER_ADMIN
        )
        self.client.force_authenticate(user=self.admin)

        self.branch1 = Branch.objects.create(
            name='Dhanmondi Branch',
            code='DHA-01',
            latitude=23.7461,
            longitude=90.3742,
            address='Dhanmondi, Dhaka'
        )
        self.branch2 = Branch.objects.create(
            name='Uttara Branch',
            code='UTT-01',
            latitude=23.8759,
            longitude=90.3795,
            address='Sector 3, Uttara, Dhaka'
        )
        self.product = Product.objects.create(
            barcode='33333333',
            name='Soap 100g',
            category='Personal Care',
            unit_price=60.00,
            cost_price=45.00,
            weight_grams=100
        )
        self.inventory = Inventory.objects.create(
            branch=self.branch1,
            product=self.product,
            stock_quantity=5,  # <= min_safety_threshold (10) -> Low stock
            min_safety_threshold=10
        )
        self.order = Order.objects.create(
            order_number='ORD-DASH-001',
            customer=self.admin,
            branch=self.branch1,
            total_amount=1200.00,
            expected_weight_grams=2000,
            status='PAID'
        )

    def test_admin_dashboard_kpis(self):
        url = reverse('admin-kpis')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('kpis', response.data['data'])
        self.assertEqual(response.data['data']['kpis']['paid_orders'], 1)
        self.assertEqual(response.data['data']['kpis']['low_stock'], 1)

    def test_owner_executive_analytics(self):
        url = reverse('admin-analytics-branches')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertIn('branch_performance', response.data['data'])
        self.assertIn('top_selling_skus', response.data['data'])

    def test_low_stock_list(self):
        url = reverse('admin-low-stock')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['product_name'], 'Soap 100g')
        self.assertEqual(response.data['data'][0]['on_hand'], 5)

    def test_stock_adjustment_receipt_and_damage(self):
        url = reverse('admin-inventory-adjust')
        
        # Test RECEIPT (+20)
        res_receipt = self.client.post(url, {
            'branch_id': self.branch1.id,
            'product_id': self.product.id,
            'quantity': 20,
            'movement_type': 'RECEIPT',
            'remarks': 'Fresh shipment from central warehouse'
        }, format='json')
        self.assertEqual(res_receipt.status_code, status.HTTP_200_OK)
        self.assertTrue(res_receipt.data['status'])
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 25)

        # Test DAMAGE (-5)
        res_damage = self.client.post(url, {
            'branch_id': self.branch1.id,
            'product_id': self.product.id,
            'quantity': 5,
            'movement_type': 'DAMAGE',
            'remarks': 'Water damaged during transport'
        }, format='json')
        self.assertEqual(res_damage.status_code, status.HTTP_200_OK)
        self.assertTrue(res_damage.data['status'])
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.stock_quantity, 20)

        # Check movement history records
        movements = InventoryMovement.objects.filter(inventory=self.inventory)
        self.assertEqual(movements.count(), 2)

    def test_stock_transfer_create_and_update(self):
        url = reverse('stock-transfers')
        response = self.client.post(url, {
            'source_branch_id': self.branch1.id,
            'dest_branch_id': self.branch2.id,
            'items_count': 50
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['status'])
        transfer_id = response.data['data']['transfer_id']

        # Approve transfer
        update_url = reverse('stock-transfer-update', kwargs={'pk': transfer_id})
        patch_res = self.client.patch(update_url, {'action': 'APPROVE'}, format='json')
        self.assertEqual(patch_res.status_code, status.HTTP_200_OK)
        self.assertTrue(patch_res.data['status'])
        self.assertEqual(patch_res.data['data']['status'], 'APPROVED')

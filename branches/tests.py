from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import User, Role
from branches.models import Branch

class BranchListViewAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            phone='01700112233',
            username='admin_branch',
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

    def test_branch_list_all(self):
        url = reverse('branch-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Dhanmondi Branch')

    @patch('branches.utils.requests.get')
    def test_branch_list_nearby(self, mock_get):
        mock_get.return_value.json.return_value = {
            'status': 'OK',
            'rows': [{
                'elements': [{
                    'status': 'OK',
                    'distance': {'text': '2.4 km', 'value': 2400}
                }]
            }]
        }
        url = reverse('branch-list')
        response = self.client.get(url, {'lat': '23.7500', 'lng': '90.3800'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['status'])
        self.assertEqual(len(response.data['data']), 1)
        self.assertIn('দূরে', response.data['data'][0]['distance'])
        self.assertIn('distance_km', response.data['data'][0])

    def test_admin_branch_crud(self):
        # 1. Create new branch
        url_create = reverse('admin-branches-list-create')
        res_create = self.client.post(url_create, {
            'name': 'Uttara Branch',
            'code': 'DHAKA-UTT',
            'latitude': '23.875900',
            'longitude': '90.379500',
            'address': 'Sector 3, Uttara, Dhaka',
            'is_active': True
        }, format='json')
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        self.assertTrue(res_create.data['status'])
        new_id = res_create.data['data']['id']

        # 2. Detail & Update branch
        url_detail = reverse('admin-branch-detail', kwargs={'id': new_id})
        res_get = self.client.get(url_detail)
        self.assertEqual(res_get.status_code, status.HTTP_200_OK)
        self.assertEqual(res_get.data['data']['name'], 'Uttara Branch')

        res_patch = self.client.patch(url_detail, {'address': 'Sector 7, Uttara, Dhaka'}, format='json')
        self.assertEqual(res_patch.status_code, status.HTTP_200_OK)
        self.assertEqual(res_patch.data['data']['address'], 'Sector 7, Uttara, Dhaka')

        # 3. Delete branch
        res_del = self.client.delete(url_detail)
        self.assertEqual(res_del.status_code, status.HTTP_200_OK)
        self.assertFalse(Branch.objects.filter(id=new_id).exists())

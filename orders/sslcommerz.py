import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

def initiate_sslcommerz_payment(order, user):
    """
    Creates an SSLCommerz payment session and returns the GatewayPageURL
    """
    store_id = getattr(settings, 'SSLCOMMERZ_STORE_ID', '')
    store_pass = getattr(settings, 'SSLCOMMERZ_STORE_PASS', '')
    session_api = getattr(settings, 'SSLCOMMERZ_SESSION_API', 'https://sandbox.sslcommerz.com/gwprocess/v4/api.php')
    base_url = getattr(settings, 'BACKEND_BASE_URL', 'http://127.0.0.1:8000')

    post_data = {
        'store_id': store_id,
        'store_passwd': store_pass,
        'total_amount': float(order.total_amount),
        'currency': 'BDT',
        'tran_id': order.order_number,
        'success_url': f"{base_url}/api/v1/payment/sslcommerz/success/",
        'fail_url': f"{base_url}/api/v1/payment/sslcommerz/fail/",
        'cancel_url': f"{base_url}/api/v1/payment/sslcommerz/cancel/",
        'ipn_url': f"{base_url}/api/v1/payment/sslcommerz/ipn/",
        # Customer Info
        'cus_name': user.get_full_name() or user.username or "SmartScan Customer",
        'cus_email': user.email or "customer@smartscan.com",
        'cus_add1': order.branch.address or "Dhaka, Bangladesh",
        'cus_city': "Dhaka",
        'cus_country': "Bangladesh",
        'cus_phone': user.phone or "01700000000",
        # Product Info
        'shipping_method': 'NO',
        'product_name': f"SmartScan Order {order.order_number}",
        'product_category': "Retail Grocery",
        'product_profile': "general",
    }

    try:
        response = requests.post(session_api, data=post_data, timeout=15)
        res_json = response.json()
        
        if res_json.get('status') == 'SUCCESS':
            return {
                'success': True,
                'gateway_url': res_json.get('GatewayPageURL'),
                'sessionkey': res_json.get('sessionkey'),
                'raw_response': res_json
            }
        else:
            return {
                'success': False,
                'message': res_json.get('failedreason', 'পেমেন্ট গেটওয়ে সেশন তৈরিতে ত্রুটি হয়েছে'),
                'raw_response': res_json
            }
    except Exception as e:
        logger.error(f"SSLCommerz Session Error: {str(e)}")
        return {
            'success': False,
            'message': f"SSLCommerz সংযোগে ত্রুটি: {str(e)}"
        }


def validate_sslcommerz_payment(val_id):
    """
    Validates a transaction with SSLCommerz Validation API
    """
    store_id = getattr(settings, 'SSLCOMMERZ_STORE_ID', '')
    store_pass = getattr(settings, 'SSLCOMMERZ_STORE_PASS', '')
    validation_api = getattr(settings, 'SSLCOMMERZ_VALIDATION_API', 'https://sandbox.sslcommerz.com/validator/api/validationserverAPI.php')

    params = {
        'val_id': val_id,
        'store_id': store_id,
        'store_passwd': store_pass,
        'v': '1',
        'format': 'json'
    }

    try:
        response = requests.get(validation_api, params=params, timeout=15)
        res_json = response.json()
        
        status_val = res_json.get('status', '').upper()
        if status_val in ['VALID', 'VALIDATED']:
            return {
                'success': True,
                'tran_id': res_json.get('tran_id'),
                'amount': res_json.get('amount'),
                'card_type': res_json.get('card_type'),
                'bank_tran_id': res_json.get('bank_tran_id'),
                'raw_data': res_json
            }
        else:
            return {
                'success': False,
                'message': res_json.get('error', 'পেমেন্ট ভ্যালিডেশন ব্যর্থ হয়েছে'),
                'raw_data': res_json
            }
    except Exception as e:
        logger.error(f"SSLCommerz Validation Error: {str(e)}")
        return {
            'success': False,
            'message': f"ভ্যালিডেশন সার্ভার সংযোগে ত্রুটি: {str(e)}"
        }

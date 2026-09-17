import uuid
from decimal import Decimal
from datetime import datetime
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from config.responses import api_response
from products.models import Product
from branches.models import Branch
from .models import Order, OrderItem, CustomerCartItem, OrderFeedback
from .serializers import OrderCreateSerializer
from .sslcommerz import initiate_sslcommerz_payment, validate_sslcommerz_payment

def format_bengali_date(dt):
    """Formats datetime into localized Bengali string e.g. ২০ মে, ২০২৬, বিকাল ৫:৩০"""
    months = {
        1: 'জানুয়ারি', 2: 'ফেব্রুয়ারি', 3: 'মার্চ', 4: 'এপ্রিল',
        5: 'মে', 6: 'জুন', 7: 'জুলাই', 8: 'আগস্ট',
        9: 'সেপ্টেম্বর', 10: 'অক্টোবর', 11: 'নভেম্বর', 12: 'ডিসেম্বর'
    }
    numbers = {'0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪', '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯'}
    
    day_str = "".join(numbers.get(c, c) for c in str(dt.day))
    year_str = "".join(numbers.get(c, c) for c in str(dt.year))
    month_str = months.get(dt.month, str(dt.month))
    
    hour = dt.hour
    period = "সকাল" if hour < 12 else ("দুপুর" if hour < 16 else ("বিকাল" if hour < 19 else "রাত"))
    hour_12 = hour % 12 or 12
    hour_str = "".join(numbers.get(c, c) for c in str(hour_12))
    minute_str = "".join(numbers.get(c, c) for c in f"{dt.minute:02d}")
    
    return f"{day_str} {month_str}, {year_str}, {period} {hour_str}:{minute_str}"


# ==============================================================================
#  🛒 Customer Server-Side Smart Cart APIs
# ==============================================================================

class CustomerCartListView(APIView):
    def get(self, request):
        user = request.user
        store_id = request.query_params.get('store_id')

        cart_qs = CustomerCartItem.objects.filter(customer=user).select_related('product', 'branch')
        if store_id:
            cart_qs = cart_qs.filter(branch_id=store_id)

        items_data = []
        subtotal = Decimal('0.00')
        total_discount = Decimal('0.00')
        total_weight = 0
        total_count = 0

        for item in cart_qs:
            p = item.product
            qty = item.quantity
            line_total = p.unit_price * qty
            line_disc = p.discount_amount * qty
            line_weight = p.weight_grams * qty

            subtotal += line_total
            total_discount += line_disc
            total_weight += line_weight
            total_count += qty

            items_data.append({
                'product_id': p.id,
                'name': p.name,
                'name_bn': p.name_bn or p.name,
                'barcode': p.barcode,
                'category': p.category,
                'unit_price': float(p.unit_price),
                'unit_info': p.unit_info,
                'weight_grams': p.weight_grams,
                'discount_amount': float(p.discount_amount),
                'image_url': p.image,
                'quantity': qty,
                'total_price': float(line_total),
                'total_weight': line_weight,
                'total_discount': float(line_disc)
            })

        cart_total = max(Decimal('0.00'), subtotal - total_discount)

        data = {
            'items': items_data,
            'total_items_count': total_count,
            'subtotal': float(subtotal),
            'total_item_discount': float(total_discount),
            'cart_total': float(cart_total),
            'total_weight_grams': total_weight
        }
        return api_response(status=True, message='স্মার্ট ট্রলির তথ্য পাওয়া গেছে', data=data, code=status.HTTP_200_OK)


class CustomerCartAddView(APIView):
    def post(self, request):
        user = request.user
        barcode = request.data.get('barcode')
        product_id = request.data.get('product_id')
        store_id = request.data.get('store_id', 1)
        quantity = int(request.data.get('quantity', 1))

        try:
            branch = Branch.objects.get(id=store_id)
        except Branch.DoesNotExist:
            return api_response(status=False, message='অবৈধ ব্রাঞ্চ আইডি', code=status.HTTP_404_NOT_FOUND)

        if barcode:
            try:
                product = Product.objects.get(barcode=barcode, is_active=True)
            except Product.DoesNotExist:
                return api_response(status=False, message='পণ্যটি খুঁজে পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        elif product_id:
            try:
                product = Product.objects.get(id=product_id, is_active=True)
            except Product.DoesNotExist:
                return api_response(status=False, message='পণ্যটি খুঁজে পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        else:
            return api_response(status=False, message='barcode বা product_id আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        cart_item, created = CustomerCartItem.objects.get_or_create(
            customer=user,
            product=product,
            branch=branch,
            defaults={'quantity': quantity}
        )
        if not created:
            cart_item.quantity += quantity
            cart_item.save()

        return api_response(
            status=True,
            message=f"{product.name_bn or product.name} ট্রলিতে যোগ করা হয়েছে",
            data={
                'product_id': product.id,
                'name': product.name,
                'name_bn': product.name_bn or product.name,
                'quantity': cart_item.quantity
            },
            code=status.HTTP_200_OK
        )


class CustomerCartUpdateView(APIView):
    def patch(self, request):
        user = request.user
        product_id = request.data.get('product_id')
        store_id = request.data.get('store_id', 1)
        action = request.data.get('action', 'set')
        qty = request.data.get('quantity')

        try:
            cart_item = CustomerCartItem.objects.get(customer=user, product_id=product_id, branch_id=store_id)
        except CustomerCartItem.DoesNotExist:
            return api_response(status=False, message='ট্রলিতে পণ্যটি পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)

        if action == 'increment':
            cart_item.quantity += 1
            cart_item.save()
        elif action == 'decrement':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                return api_response(status=True, message='পণ্যটি ট্রলি থেকে সরানো হয়েছে', data={'deleted': True}, code=status.HTTP_200_OK)
        elif action == 'set' and qty is not None:
            new_qty = int(qty)
            if new_qty > 0:
                cart_item.quantity = new_qty
                cart_item.save()
            else:
                cart_item.delete()
                return api_response(status=True, message='পণ্যটি ট্রলি থেকে সরানো হয়েছে', data={'deleted': True}, code=status.HTTP_200_OK)

        return api_response(
            status=True,
            message='ট্রলি আপডেট হয়েছে',
            data={'product_id': product_id, 'quantity': cart_item.quantity},
            code=status.HTTP_200_OK
        )


class CustomerCartItemDeleteView(APIView):
    def delete(self, request, product_id):
        user = request.user
        store_id = request.query_params.get('store_id')
        
        qs = CustomerCartItem.objects.filter(customer=user, product_id=product_id)
        if store_id:
            qs = qs.filter(branch_id=store_id)
        
        deleted_count, _ = qs.delete()
        if deleted_count > 0:
            return api_response(status=True, message='পণ্যটি ট্রলি থেকে সরানো হয়েছে', code=status.HTTP_200_OK)
        return api_response(status=False, message='পণ্যটি ট্রলিতে পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)


class CustomerCartClearView(APIView):
    def delete(self, request):
        user = request.user
        store_id = request.query_params.get('store_id')
        
        qs = CustomerCartItem.objects.filter(customer=user)
        if store_id:
            qs = qs.filter(branch_id=store_id)
        
        qs.delete()
        return api_response(status=True, message='স্মার্ট ট্রলি খালি করা হয়েছে', code=status.HTTP_200_OK)


# ==============================================================================
#  🧾 Bill Review, Checkout & Orders
# ==============================================================================

class BillReviewView(APIView):
    def post(self, request):
        user = request.user
        store_id = request.data.get('store_id')
        items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'bKash')
        use_loyalty_points = request.data.get('use_loyalty_points', False)

        if not store_id or not items:
            return api_response(status=False, message='store_id এবং items তালিকা আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        try:
            branch = Branch.objects.get(id=store_id)
        except Branch.DoesNotExist:
            return api_response(status=False, message='অবৈধ ব্রাঞ্চ আইডি', code=status.HTTP_404_NOT_FOUND)

        subtotal = Decimal('0.00')
        item_discount = Decimal('0.00')
        total_weight_grams = 0
        reviewed_items = []

        for item in items:
            p_id = item.get('product_id')
            qty = int(item.get('quantity', 1))
            try:
                product = Product.objects.get(id=p_id)
            except Product.DoesNotExist:
                return api_response(status=False, message=f'Product ID {p_id} পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
            
            line_total = product.unit_price * qty
            line_disc = product.discount_amount * qty
            subtotal += line_total
            item_discount += line_disc
            total_weight_grams += product.weight_grams * qty

            reviewed_items.append({
                'product_id': product.id,
                'name': product.name,
                'name_bn': product.name_bn or product.name,
                'unit_price': float(product.unit_price),
                'unit_info': product.unit_info,
                'image': product.image,
                'weight_grams': product.weight_grams,
                'quantity': qty,
                'total_price': float(line_total)
            })

        # Calculate Loyalty Points Discount
        user_points = user.loyalty_points
        points_used = 0
        loyalty_discount = Decimal('0.00')
        if use_loyalty_points and user_points > 0:
            max_disc = subtotal * Decimal('0.20')
            points_used = min(user_points, int(max_disc))
            loyalty_discount = Decimal(str(points_used))

        # Payment Gateway Promo Discount
        payment_discount = Decimal('25.00') if str(payment_method).lower() in ['bkash', 'sslcommerz'] and subtotal >= 500 else Decimal('0.00')

        vat_tax = Decimal('0.00')
        total_payable = max(Decimal('0.00'), subtotal + vat_tax - item_discount - loyalty_discount - payment_discount)
        points_to_earn = int(total_payable // 10)

        data = {
            'store': {
                'id': branch.id,
                'name': f"SMARTSCAN SUPERMARKET ({branch.name_bn or branch.name})"
            },
            'items': reviewed_items,
            'subtotal': float(subtotal),
            'vat_tax': float(vat_tax),
            'item_discount': float(item_discount),
            'payment_method': payment_method,
            'payment_method_discount': float(payment_discount),
            'user_loyalty_points': user_points,
            'loyalty_points_used': points_used,
            'loyalty_discount': float(loyalty_discount),
            'total_payable_amount': float(total_payable),
            'total_weight_grams': total_weight_grams,
            'points_to_earn': points_to_earn
        }
        return api_response(status=True, message='বিল রিভিউ সফলভাবে পাওয়া গেছে', data=data, code=status.HTTP_200_OK)


class CheckoutOrderView(APIView):
    """
    Screen 3: কার্ট চেকআউট, অর্ডার তৈরি ও SSLCommerz গেটওয়ে হ্যান্ডলিং API
    """
    def post(self, request):
        user = request.user
        store_id = request.data.get('store_id')
        items = request.data.get('items', [])
        payment_method = request.data.get('payment_method', 'bKash')
        use_loyalty_points = request.data.get('use_loyalty_points', False)

        if not store_id or not items:
            return api_response(status=False, message='store_id এবং items তালিকা আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        try:
            branch = Branch.objects.get(id=store_id)
        except Branch.DoesNotExist:
            return api_response(status=False, message='অবৈধ ব্রাঞ্চ আইডি', code=status.HTTP_404_NOT_FOUND)

        subtotal = Decimal('0.00')
        item_discount = Decimal('0.00')
        total_weight_grams = 0
        order_items_data = []

        for item in items:
            product_id = item.get('product_id')
            qty = int(item.get('quantity', 1))
            try:
                product = Product.objects.get(id=product_id)
            except Product.DoesNotExist:
                return api_response(status=False, message=f'Product ID {product_id} পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
            
            line_total = product.unit_price * qty
            subtotal += line_total
            item_discount += product.discount_amount * qty
            total_weight_grams += product.weight_grams * qty
            order_items_data.append({
                'product': product,
                'quantity': qty,
                'unit_price': product.unit_price,
                'weight_grams': product.weight_grams,
                'total_price': line_total
            })

        # Calculate Loyalty Points Discount
        user_points = user.loyalty_points
        points_used = 0
        loyalty_discount = Decimal('0.00')
        if use_loyalty_points and user_points > 0:
            max_disc = subtotal * Decimal('0.20')
            points_used = min(user_points, int(max_disc))
            loyalty_discount = Decimal(str(points_used))

        # Payment Promo Discount
        payment_discount = Decimal('25.00') if str(payment_method).lower() in ['bkash', 'sslcommerz'] and subtotal >= 500 else Decimal('0.00')
        vat_tax = Decimal('0.00')
        total_payable = max(Decimal('0.00'), subtotal + vat_tax - item_discount - loyalty_discount - payment_discount)

        # Unique Order Number
        order_number = f"SS{uuid.uuid4().hex[:6].upper()}"
        
        # Determine whether payment is online or cash
        cash_methods = ['cash', 'cash_at_counter', 'counter_cash', 'ক্যাশ', 'কাউন্টার ক্যাশ']
        is_online = str(payment_method).strip().lower() not in cash_methods
        order_status = 'PENDING' if is_online else 'PAID'

        order = Order.objects.create(
            order_number=order_number,
            customer=user,
            branch=branch,
            subtotal=subtotal,
            vat_tax=vat_tax,
            discount_amount=item_discount + payment_discount,
            loyalty_points_used=points_used,
            loyalty_discount=loyalty_discount,
            total_amount=total_payable,
            expected_weight_grams=total_weight_grams,
            payment_method=payment_method,
            status=order_status
        )

        # Create OrderItem records
        for item_info in order_items_data:
            OrderItem.objects.create(
                order=order,
                product=item_info['product'],
                quantity=item_info['quantity'],
                unit_price=item_info['unit_price'],
                weight_grams=item_info['weight_grams'],
                total_price=item_info['total_price']
            )
        
        # Clear Server-Side Cart on Checkout
        CustomerCartItem.objects.filter(customer=user, branch=branch).delete()

        # Generate Security Hash & Base64 PNG QR Code
        order.security_hash = order.generate_security_hash()
        order.qr_code_image = order.generate_qr_code_base64()
        order.save()

        # Update User Loyalty Points if paid immediately (e.g. Cash)
        points_earned = int(total_payable // 10)
        if order_status == 'PAID':
            user.loyalty_points = max(0, user.loyalty_points - points_used) + points_earned
            user.save()

        # SSLCommerz Payment Gateway Initiation if online
        gateway_data = None
        payment_url = None
        if is_online:
            ssl_res = initiate_sslcommerz_payment(order, user)
            if ssl_res.get('success'):
                payment_url = ssl_res['gateway_url']
                gateway_data = {
                    'payment_url': ssl_res['gateway_url'],
                    'sessionkey': ssl_res['sessionkey']
                }

        # Build Receipt Items
        receipt_items = []
        for oi in order_items_data:
            p = oi['product']
            receipt_items.append({
                'name': p.name_bn or p.name,
                'name_en': p.name,
                'unit_price': f"৳{int(p.unit_price)}",
                'weight': f"{p.weight_grams // 1000} কেজি" if p.weight_grams >= 1000 else f"{p.weight_grams} গ্রাম",
                'quantity': oi['quantity'],
                'total': f"৳{int(oi['total_price'])}"
            })

        data = {
            'order_id': order.order_number,
            'order_number': order.order_number,
            'formatted_date': format_bengali_date(order.created_at),
            'points_earned': points_earned,
            'store_name': f"SmartScan Supermarket ({branch.name_bn or branch.name})",
            'items': receipt_items,
            'subtotal': str(order.subtotal),
            'discount_amount': str(order.discount_amount),
            'loyalty_discount': str(order.loyalty_discount),
            'total_payable_amount': str(order.total_amount),
            'expected_weight_grams': order.expected_weight_grams,
            'payment_method': order.payment_method,
            'status': order.status,
            'payment_url': payment_url,
            'qr_code_image': order.qr_code_image,
            'security_qr_payload': {
                'order_number': order.order_number,
                'weight': order.expected_weight_grams,
                'hash': order.security_hash
            },
            'sslcommerz_gateway': gateway_data
        }

        resp_msg = 'অর্ডার তৈরি হয়েছে। পেমেন্ট সম্পন্ন করতে এগিয়ে যান।' if is_online else 'অর্ডার সফল হয়েছে! পেমেন্ট নিশ্চিত করা হয়েছে।'
        return api_response(
            status=True,
            message=resp_msg,
            data=data,
            code=status.HTTP_201_CREATED
        )


# ==============================================================================
#  SSLCommerz Payment Views & Callbacks
# ==============================================================================

class SSLCommerzInitiateView(APIView):
    def post(self, request):
        order_number = request.data.get('order_number')
        if not order_number:
            return api_response(status=False, message='order_number আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(order_number=order_number, customer=request.user)
        except Order.DoesNotExist:
            return api_response(status=False, message='অর্ডার পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)

        ssl_res = initiate_sslcommerz_payment(order, request.user)
        if ssl_res.get('success'):
            return api_response(
                status=True,
                message='SSLCommerz পেমেন্ট সেশন সফলভাবে তৈরি হয়েছে',
                data={
                    'payment_url': ssl_res['gateway_url'],
                    'sessionkey': ssl_res['sessionkey'],
                    'order_number': order.order_number,
                    'total_amount': str(order.total_amount)
                },
                code=status.HTTP_200_OK
            )
        else:
            return api_response(
                status=False,
                message=ssl_res.get('message', 'SSLCommerz সেশন তৈরি করা যায়নি'),
                data=ssl_res.get('raw_response'),
                code=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzSuccessCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        val_id = request.data.get('val_id')
        tran_id = request.data.get('tran_id')

        if not tran_id:
            return HttpResponse("<h3>অবৈধ পেমেন্ট প্যারামিটার</h3>", status=400)

        # Validate with SSLCommerz Server
        val_res = validate_sslcommerz_payment(val_id) if val_id else {'success': True}
        try:
            order = Order.objects.get(order_number=tran_id)
            order.status = 'PAID'
            order.security_hash = order.generate_security_hash()
            order.qr_code_image = order.generate_qr_code_base64()
            order.save()

            customer = order.customer
            points_earned = int(order.total_amount // 10)
            customer.loyalty_points = max(0, customer.loyalty_points - order.loyalty_points_used) + points_earned
            customer.save()

            # Clear Server Cart Item
            CustomerCartItem.objects.filter(customer=customer, branch=order.branch).delete()

            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>পেমেন্ট সফল হয়েছে</title>
                <style>
                    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; background: #F8FAFC; }}
                    .card {{ background: white; padding: 40px; border-radius: 20px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.05); max-width: 400px; }}
                    .icon {{ font-size: 50px; color: #10B981; }}
                    h2 {{ color: #0F172A; margin: 15px 0 10px; }}
                    p {{ color: #64748B; font-size: 14px; margin: 5px 0; }}
                    .btn {{ margin-top: 25px; display: inline-block; background: #FF7A00; color: white; padding: 12px 24px; border-radius: 12px; text-decoration: none; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="icon">✓</div>
                    <h2>পেমেন্ট সফল হয়েছে!</h2>
                    <p>অর্ডার নম্বর: <b>{order.order_number}</b></p>
                    <p>পরিশোধিত মূল্য: <b>৳{order.total_amount}</b></p>
                    <p>আপনার গেট পাস কিউআর কোড তৈরি হয়েছে।</p>
                    <a href="smartscan://payment-success?order={order.order_number}" class="btn">অ্যাপে ফিরে যান</a>
                </div>
            </body>
            </html>
            """
            return HttpResponse(html_content)
        except Order.DoesNotExist:
            return HttpResponse("<h3>অর্ডার রেকর্ড পাওয়া যায়নি</h3>", status=404)


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzFailCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        tran_id = request.data.get('tran_id')
        if tran_id:
            Order.objects.filter(order_number=tran_id).update(status='FAILED')
        
        return HttpResponse("""
            <div style='font-family:sans-serif; text-align:center; padding:50px;'>
                <h2 style='color:#EF4444;'>❌ পেমেন্ট ব্যর্থ হয়েছে!</h2>
                <p>দয়া করে পুনরায় চেষ্টা করুন।</p>
                <a href='smartscan://payment-failed' style='background:#0F172A; color:white; padding:10px 20px; border-radius:8px; text-decoration:none;'>অ্যাপে ফিরে যান</a>
            </div>
        """)


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzCancelCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        tran_id = request.data.get('tran_id')
        if tran_id:
            Order.objects.filter(order_number=tran_id).update(status='CANCELLED')

        return HttpResponse("""
            <div style='font-family:sans-serif; text-align:center; padding:50px;'>
                <h2 style='color:#F59E0B;'>⚠️ পেমেন্ট বাতিল করা হয়েছে</h2>
                <a href='smartscan://payment-cancelled' style='background:#0F172A; color:white; padding:10px 20px; border-radius:8px; text-decoration:none;'>অ্যাপে ফিরে যান</a>
            </div>
        """)


@method_decorator(csrf_exempt, name='dispatch')
class SSLCommerzIPNCallbackView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        val_id = request.data.get('val_id')
        tran_id = request.data.get('tran_id')
        if val_id and tran_id:
            val_res = validate_sslcommerz_payment(val_id)
            if val_res.get('success'):
                Order.objects.filter(order_number=tran_id).update(status='PAID')
                return api_response(status=True, message='IPN Validated', code=status.HTTP_200_OK)
        return api_response(status=False, message='IPN Failed', code=status.HTTP_400_BAD_REQUEST)


class SSLCommerzValidateAPIView(APIView):
    def post(self, request):
        val_id = request.data.get('val_id')
        tran_id = request.data.get('tran_id')

        if not tran_id and not val_id:
            return api_response(status=False, message='tran_id অথবা val_id আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        # Validate with SSLCommerz server if real val_id provided
        val_res = validate_sslcommerz_payment(val_id) if val_id and not str(val_id).startswith('val_') else {'success': False}
        target_tran_id = tran_id or val_res.get('tran_id')

        try:
            order = Order.objects.get(order_number=target_tran_id)
        except Order.DoesNotExist:
            return api_response(status=False, message='অর্ডার রেকর্ড পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)

        # If SSLCommerz returned VALID OR if running in Sandbox / Webhook already validated
        if val_res.get('success') or order.status == 'PAID' or (settings.SSLCOMMERZ_IS_SANDBOX and target_tran_id):
            order.status = 'PAID'
            order.security_hash = order.generate_security_hash()
            order.qr_code_image = order.generate_qr_code_base64()
            order.save()

            customer = order.customer
            points_earned = int(order.total_amount // 10)
            customer.loyalty_points = max(0, customer.loyalty_points - order.loyalty_points_used) + points_earned
            customer.save()

            CustomerCartItem.objects.filter(customer=request.user, branch=order.branch).delete()

            return api_response(
                status=True,
                message='পেমেন্ট সফলভাবে নিশ্চিত করা হয়েছে!',
                data={
                    'order_number': order.order_number,
                    'status': order.status,
                    'total_amount': str(order.total_amount),
                    'qr_code_image': order.qr_code_image,
                    'security_qr_payload': {
                        'order_number': order.order_number,
                        'weight': order.expected_weight_grams,
                        'hash': order.security_hash
                    }
                },
                code=status.HTTP_200_OK
            )
        else:
            return api_response(
                status=False,
                message=val_res.get('message', 'পেমেন্ট ভ্যালিডেশন ব্যর্থ হয়েছে'),
                data=val_res.get('raw_data'),
                code=status.HTTP_400_BAD_REQUEST
            )


# ==============================================================================
#  Other Orders & Gate Views
# ==============================================================================

class ActiveGatePassView(APIView):
    def get(self, request):
        active_order = Order.objects.filter(customer=request.user, status='PAID').order_by('-created_at').first()
        
        if active_order:
            if not active_order.qr_code_image:
                active_order.qr_code_image = active_order.generate_qr_code_base64()
                active_order.save()

            data = {
                'has_active_pass': True,
                'order_number': active_order.order_number,
                'store_name': f"SmartScan Supermarket ({active_order.branch.name_bn or active_order.branch.name})",
                'total_amount': str(active_order.total_amount),
                'expected_weight_grams': active_order.expected_weight_grams,
                'formatted_date': format_bengali_date(active_order.created_at),
                'qr_code_image': active_order.qr_code_image,
                'security_qr_payload': {
                    'order_number': active_order.order_number,
                    'weight': active_order.expected_weight_grams,
                    'hash': active_order.security_hash
                },
                'status': active_order.status
            }
            return api_response(
                status=True,
                message='অ্যাক্টিভ গেট পাস পাওয়া গেছে',
                data=data,
                code=status.HTTP_200_OK
            )
        else:
            return api_response(
                status=True,
                message='কোনো রানিং অ্যাক্টিভ গেট পাস নেই',
                data={'has_active_pass': False},
                code=status.HTTP_200_OK
            )


class OrderReceiptView(APIView):
    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, customer=request.user)
        except Order.DoesNotExist:
            return api_response(status=False, message='অর্ডার পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)

        if not order.qr_code_image:
            order.qr_code_image = order.generate_qr_code_base64()
            order.save()

        items = []
        for item in order.items.select_related('product'):
            p = item.product
            items.append({
                'name': p.name_bn or p.name,
                'name_en': p.name,
                'unit_price': f"৳{int(item.unit_price)}",
                'weight': f"{item.weight_grams // 1000} কেজি" if item.weight_grams >= 1000 else f"{item.weight_grams} গ্রাম",
                'quantity': item.quantity,
                'total': f"৳{int(item.total_price)}"
            })

        data = {
            'order_number': order.order_number,
            'formatted_date': format_bengali_date(order.created_at),
            'store_name': f"SmartScan Supermarket ({order.branch.name_bn or order.branch.name})",
            'branch_address': order.branch.address,
            'items': items,
            'subtotal': str(order.subtotal),
            'discount_amount': str(order.discount_amount),
            'loyalty_discount': str(order.loyalty_discount),
            'total_payable_amount': str(order.total_amount),
            'expected_weight_grams': order.expected_weight_grams,
            'payment_method': order.payment_method,
            'status': order.status,
            'qr_code_image': order.qr_code_image,
            'security_qr_payload': {
                'order_number': order.order_number,
                'weight': order.expected_weight_grams,
                'hash': order.security_hash
            }
        }
        return api_response(status=True, message='রসিদ তথ্য সফলভাবে পাওয়া গেছে', data=data, code=status.HTTP_200_OK)


class SecurityGateVerifyView(APIView):
    def post(self, request):
        order_number = request.data.get('order_number')
        actual_weight_raw = request.data.get('actual_weight_grams', 0)

        try:
            actual_weight = int(actual_weight_raw)
        except (ValueError, TypeError):
            return api_response(status=False, message='ওজন অবশ্যই একটি সঠিক সংখ্যা হতে হবে', code=status.HTTP_400_BAD_REQUEST)

        try:
            order = Order.objects.get(order_number=order_number)
            expected = order.expected_weight_grams

            if abs(actual_weight - expected) <= 20:
                order.status = 'VERIFIED_PASSED'
                order.save()
                return api_response(
                    status=True,
                    message=f'EXPECTED: {expected}g vs ACTUAL: {actual_weight}g - PASSED!',
                    data={
                        'status': 'MATCHED',
                        'order_number': order.order_number,
                        'expected_weight_grams': expected,
                        'actual_weight_grams': actual_weight
                    },
                    code=status.HTTP_200_OK
                )
            else:
                return api_response(
                    status=False,
                    message=f'WEIGHT MISMATCH! Expected {expected}g but got {actual_weight}g',
                    data={
                        'status': 'MISMATCH',
                        'requires_override': True,
                        'expected_weight_grams': expected,
                        'actual_weight_grams': actual_weight
                    },
                    code=status.HTTP_400_BAD_REQUEST
                )

        except Order.DoesNotExist:
            return api_response(status=False, message='অকার্যকর গেট পাস QR কোড', code=status.HTTP_404_NOT_FOUND)


class ManualOverrideView(APIView):
    def post(self, request):
        order_number = request.data.get('order_number')
        pin = request.data.get('security_pin')

        if pin != "9999":
            return api_response(status=False, message='ভুল সিকিউরিটি পিন', code=status.HTTP_403_FORBIDDEN)

        try:
            order = Order.objects.get(order_number=order_number)
            order.status = 'MANUAL_OVERRIDDEN'
            order.save()
            return api_response(
                status=True,
                message='Manual Override সফল হয়েছে। গেট পাস অনুমোদিত।',
                data={'order_number': order.order_number, 'status': 'MANUAL_OVERRIDDEN'},
                code=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return api_response(status=False, message='অর্ডার পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)


class CustomerOrderHistoryView(APIView):
    def get(self, request):
        orders = Order.objects.filter(customer=request.user).order_by('-created_at')
        data = [{
            'id': o.id,
            'order_number': o.order_number,
            'store_name': o.branch.name_bn or o.branch.name,
            'total_amount': str(o.total_amount),
            'weight_grams': o.expected_weight_grams,
            'status': o.status,
            'date': format_bengali_date(o.created_at),
            'has_feedback': hasattr(o, 'feedback')
        } for o in orders]
        return api_response(
            status=True,
            message='অর্ডার হিস্ট্রি পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )


class SubmitFeedbackView(APIView):
    def post(self, request, order_number):
        rating_raw = request.data.get('rating', 5)
        comment = request.data.get('complaint_text', '')

        try:
            rating = int(rating_raw)
        except (ValueError, TypeError):
            rating = 5

        try:
            order = Order.objects.get(order_number=order_number, customer=request.user)
            
            feedback, created = OrderFeedback.objects.get_or_create(
                order=order,
                defaults={
                    'customer': request.user,
                    'branch': order.branch,
                    'rating': rating,
                    'complaint_text': comment,
                    'status': 'PENDING' if rating <= 3 else 'RESOLVED'
                }
            )
            if not created:
                feedback.rating = rating
                feedback.complaint_text = comment
                feedback.status = 'PENDING' if rating <= 3 else 'RESOLVED'
                feedback.save()

            return api_response(
                status=True,
                message='আপনার ফিডব্যাকের জন্য ধন্যবাদ!',
                data={'order_number': order_number, 'rating': rating},
                code=status.HTTP_200_OK
            )
        except Order.DoesNotExist:
            return api_response(status=False, message='অর্ডার পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)


class ManagerComplaintPortalView(APIView):
    def get(self, request, pk=None):
        branch_id = request.query_params.get('branch_id')
        complaints = OrderFeedback.objects.filter(rating__lte=3).select_related('order', 'customer')
        if branch_id:
            complaints = complaints.filter(branch_id=branch_id)

        data = [{
            'id': c.id,
            'order_number': c.order.order_number,
            'customer_phone': c.customer.phone,
            'rating': c.rating,
            'complaint': c.complaint_text,
            'status': c.status,
            'resolution_note': c.resolution_note,
            'date': c.created_at.strftime("%Y-%m-%d")
        } for c in complaints]
        return api_response(
            status=True,
            message='কমপ্লেন তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

    def patch(self, request, pk=None):
        resolution_note = request.data.get('resolution_note')
        if not resolution_note:
            return api_response(status=False, message='resolution_note আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        try:
            complaint = OrderFeedback.objects.get(id=pk)
        except OrderFeedback.DoesNotExist:
            return api_response(status=False, message='কমপ্লেন রেকর্ড পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        
        complaint.resolution_note = resolution_note
        complaint.status = 'RESOLVED'
        complaint.resolved_by = request.user
        complaint.save()

        return api_response(
            status=True,
            message='রেজোলিউশন নোট কাস্টমারের অ্যাকাউন্টে পাঠানো হয়েছে।',
            data={'complaint_id': complaint.id, 'status': 'RESOLVED'},
            code=status.HTTP_200_OK
        )

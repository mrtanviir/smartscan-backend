from rest_framework.views import APIView
from rest_framework import status
from django.db.models import Sum, Count, F
from config.responses import api_response
from orders.models import Order
from .models import Inventory, StockTransfer, InventoryMovement

class AdminDashboardKPIView(APIView):
    def get(self, request):
        paid_orders_count = Order.objects.filter(status__in=['PAID', 'VERIFIED_PASSED']).count()
        total_revenue = Order.objects.filter(status__in=['PAID', 'VERIFIED_PASSED']).aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # যেসব প্রডাক্টের স্টক Safety Limit-এর নিচে
        low_stock_count = Inventory.objects.filter(stock_quantity__lte=F('min_safety_threshold')).count()
        active_transfers_count = StockTransfer.objects.exclude(status__in=['RECEIVED', 'REJECTED']).count()

        # সাম্প্রতিক ৫টি অর্ডার
        recent_orders = Order.objects.all().order_by('-created_at')[:5]
        orders_data = [{
            'order_number': o.order_number,
            'customer': o.customer.email or o.customer.phone,
            'amount': str(o.total_amount),
            'status': o.status,
            'date': o.created_at.strftime("%Y-%m-%d %H:%M")
        } for o in recent_orders]

        return api_response(
            status=True,
            message='ড্যাশবোর্ড কেপিআই সফলভাবে পাওয়া গেছে',
            data={
                'kpis': {
                    'paid_orders': paid_orders_count,
                    'revenue': f"৳{total_revenue:,.2f}",
                    'low_stock': low_stock_count,
                    'transfers': active_transfers_count
                },
                'recent_orders': orders_data
            },
            code=status.HTTP_200_OK
        )

class LowStockListView(APIView):
    def get(self, request):
        low_stocks = Inventory.objects.filter(stock_quantity__lte=F('min_safety_threshold')).select_related('product')
        data = [{
            'product_name': i.product.name,
            'sku': i.product.barcode,
            'on_hand': i.stock_quantity,
            'threshold': i.min_safety_threshold,
        } for i in low_stocks]
        return api_response(
            status=True,
            message='লো-স্টক পণ্যের তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

class StockTransferView(APIView):
    def get(self, request):
        transfers = StockTransfer.objects.all().order_by('-created_at')
        data = [{
            'id': t.id,
            'from_to': f"{t.source_branch.name} → {t.dest_branch.name}",
            'items': t.items_count,
            'status': t.status
        } for t in transfers]
        return api_response(
            status=True,
            message='স্টক ট্রান্সফার তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

    def post(self, request):
        # নতুন ট্রান্সফার রিকোয়েস্ট (Manager সাদিয়া)
        source_id = request.data.get('source_branch_id')
        dest_id = request.data.get('dest_branch_id')
        items_count = request.data.get('items_count')

        if not source_id or not dest_id or items_count is None:
            return api_response(status=False, message='source_branch_id, dest_branch_id, items_count আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        transfer = StockTransfer.objects.create(
            source_branch_id=source_id,
            dest_branch_id=dest_id,
            items_count=items_count,
            status='PENDING'
        )
        return api_response(
            status=True,
            message='ট্রান্সফার রিকোয়েস্ট তৈরি হয়েছে',
            data={'transfer_id': transfer.id, 'status': 'PENDING'},
            code=status.HTTP_201_CREATED
        )

    def patch(self, request, pk=None):
        # রিকোয়েস্ট অ্যাপ্রুভ/রিজেক্ট (Super Admin আসিফ)
        action = request.data.get('action')  # 'APPROVE' or 'REJECT'
        
        try:
            transfer = StockTransfer.objects.get(id=pk)
        except StockTransfer.DoesNotExist:
            return api_response(status=False, message='ট্রান্সফার রেকর্ড পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        
        if action == 'APPROVE':
            transfer.status = 'APPROVED'
        elif action == 'REJECT':
            transfer.status = 'REJECTED'
        else:
            return api_response(status=False, message='অবৈধ অ্যাকশন। APPROVE অথবা REJECT প্রদান করুন।', code=status.HTTP_400_BAD_REQUEST)
            
        transfer.save()
        return api_response(
            status=True,
            message=f'Transfer status updated to {transfer.status}',
            data={'transfer_id': transfer.id, 'status': transfer.status},
            code=status.HTTP_200_OK
        )

class StockAdjustmentView(APIView):
    def post(self, request):
        branch_id = request.data.get('branch_id')
        product_id = request.data.get('product_id')
        qty_raw = request.data.get('quantity')
        movement_type = request.data.get('movement_type')  # e.g. 'RECEIPT', 'DAMAGE'

        if not branch_id or not product_id or qty_raw is None or not movement_type:
            return api_response(status=False, message='branch_id, product_id, quantity, movement_type আবশ্যক', code=status.HTTP_400_BAD_REQUEST)

        try:
            qty = int(qty_raw)
        except (ValueError, TypeError):
            return api_response(status=False, message='পরিমাণ (quantity) একটি সঠিক সংখ্যা হতে হবে', code=status.HTTP_400_BAD_REQUEST)

        inv, _ = Inventory.objects.get_or_create(branch_id=branch_id, product_id=product_id)

        if movement_type in ['DAMAGE', 'TRANSFER_OUT', 'SALE']:
            inv.stock_quantity -= qty
        elif movement_type == 'RECEIPT':
            inv.stock_quantity += qty
            
        inv.save()

        # হিস্ট্রি লগ তৈরি
        InventoryMovement.objects.create(
            inventory=inv,
            movement_type=movement_type,
            quantity=qty,
            remarks=request.data.get('remarks', '')
        )

        return api_response(
            status=True,
            message='স্টক সফলভাবে আপডেট হয়েছে',
            data={
                'current_on_hand': inv.stock_quantity,
                'branch_id': branch_id,
                'product_id': product_id
            },
            code=status.HTTP_200_OK
        )

class OwnerExecutiveAnalyticsView(APIView):
    def get(self, request):
        branch_sales_qs = Order.objects.filter(status__in=['PAID', 'VERIFIED_PASSED']).values('branch__id', 'branch__name').annotate(
            total_sales=Sum('total_amount'),
            total_orders=Count('id')
        )
        branch_sales = []
        for bs in branch_sales_qs:
            sales_val = float(bs.get('total_sales') or 0)
            branch_sales.append({
                'branch_id': bs.get('branch__id'),
                'branch_name': bs.get('branch__name') or 'Main Branch',
                'total_sales': sales_val,
                'formatted_sales': f"৳{sales_val:,.2f}",
                'total_orders': bs.get('total_orders') or 0
            })

        return api_response(
            status=True,
            message='এক্সিকিউটিভ অ্যানালিটিক্স ডেটা পাওয়া গেছে',
            data={
                'branch_performance': branch_sales,
                'top_selling_skus': [
                    {'name': 'মিনিকেট চাল - ৫ কেজি', 'sold_qty': 420, 'revenue': '৳2,31,000'},
                    {'name': 'রূপচাঁদা সয়াবিন তেল - ২ লিটার', 'sold_qty': 310, 'revenue': '৳1,16,250'},
                    {'name': 'প্রাণ ফ্রেশ লিকুইড মিল্ক - ১ লিটার', 'sold_qty': 190, 'revenue': '৳17,100'}
                ]
            },
            code=status.HTTP_200_OK
        )

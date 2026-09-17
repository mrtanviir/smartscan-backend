from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny
from config.responses import api_response
from .models import Product
from .serializers import ProductSerializer
from inventory.models import Inventory
from branches.utils import get_nearby_branches, calculate_haversine_distance
from branches.models import Branch

class ProductScanView(APIView):
    def get(self, request):
        barcode = request.query_params.get('barcode')
        branch_id = request.query_params.get('store_id') or request.query_params.get('branch_id')

        if not barcode:
            return api_response(
                status=False,
                message='বারকোড প্যারামিটার আবশ্যক',
                code=status.HTTP_400_BAD_REQUEST
            )

        try:
            product = Product.objects.get(barcode=barcode, is_active=True)
            
            # If store_id / branch_id is passed, get branch inventory stock
            available_stock = 0
            if branch_id:
                try:
                    inv = Inventory.objects.get(branch_id=branch_id, product=product)
                    available_stock = inv.stock_quantity
                except Inventory.DoesNotExist:
                    available_stock = 0
            else:
                # Default total stock across all branches
                inv_list = Inventory.objects.filter(product=product)
                available_stock = sum(i.stock_quantity for i in inv_list) or 100

            return api_response(
                status=True,
                message='পণ্য সফলভাবে স্ক্যান করা হয়েছে',
                data={
                    'product_id': product.id,
                    'name': product.name,
                    'name_bn': product.name_bn or product.name,
                    'barcode': product.barcode,
                    'category': product.category,
                    'unit_price': float(product.unit_price),
                    'unit_info': product.unit_info or f"৳{int(product.unit_price)}/একক",
                    'image': product.image,
                    'weight_grams': product.weight_grams,
                    'discount_amount': float(product.discount_amount),
                    'available_stock': available_stock
                },
                code=status.HTTP_200_OK
            )
        except Product.DoesNotExist:
            return api_response(status=False, message='পণ্যটি পাওয়া যায়নি বা নিষ্ক্রিয় রয়েছে', code=status.HTTP_404_NOT_FOUND)


class TodayBestOffersView(APIView):
    """
    আজকের সেরা অফার API (ইউজারের ৩০ কিমি দূরত্বের মধ্যে থাকা সুপারশপের অফার)
    """
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        radius_km = float(request.query_params.get('radius_km', 30.0))
        limit = request.query_params.get('limit')
        if limit:
            try:
                limit = int(limit)
            except ValueError:
                limit = None

        discounted_products = Product.objects.filter(is_active=True, discount_amount__gt=0).order_by('-discount_amount')

        if lat and lng:
            try:
                u_lat, u_lng = float(lat), float(lng)
            except (ValueError, TypeError):
                u_lat, u_lng = None, None

            if u_lat is not None and u_lng is not None:
                # Find all nearby branches using Google Places + DB branches
                all_nearby = get_nearby_branches(u_lat, u_lng, limit=30)
                # Filter branches within specified radius (default 30 km)
                in_range_branches = [b for b in all_nearby if b['distance_km'] <= radius_km]

                if not in_range_branches:
                    return api_response(
                        status=True,
                        message='আপনার ৩০ কিমি দূরত্বের মধ্যে কোনো সুপারশপের অফার পাওয়া যায়নি',
                        data={
                            'total_offers': 0,
                            'nearby_stores_count': 0,
                            'radius_km': radius_km,
                            'offers': []
                        },
                        code=status.HTTP_200_OK
                    )

                closest_branch = in_range_branches[0]
                offers_data = []

                for p in discounted_products:
                    orig_price = float(p.unit_price)
                    disc = float(p.discount_amount)
                    offer_price = max(0.0, orig_price - disc)
                    disc_pct = int(round((disc / orig_price) * 100)) if orig_price > 0 else 0

                    disc_text = f"(৳{int(disc)} ছাড়!)" if disc >= 20 else f"({disc_pct}% ছাড়!)"

                    offers_data.append({
                        'product_id': p.id,
                        'name': p.name,
                        'name_bn': p.name_bn or p.name,
                        'category': p.category,
                        'barcode': p.barcode,
                        'unit_price': orig_price,
                        'offer_price': offer_price,
                        'discount_amount': disc,
                        'discount_percentage': disc_pct,
                        'formatted_offer_price': f"৳{int(offer_price)}",
                        'formatted_original_price': f"৳{int(orig_price)}",
                        'discount_text': disc_text,
                        'unit_info': p.unit_info,
                        'weight_grams': p.weight_grams,
                        'image': p.image,
                        'store': {
                            'id': closest_branch['id'],
                            'name': closest_branch['name_bn'] or closest_branch['name'],
                            'distance_text': closest_branch['distance_text'],
                            'distance_km': closest_branch['distance_km']
                        }
                    })

                if limit:
                    offers_data = offers_data[:limit]

                return api_response(
                    status=True,
                    message='আজকের সেরা অফারসমূহ পাওয়া গেছে',
                    data={
                        'total_offers': len(offers_data),
                        'nearby_stores_count': len(in_range_branches),
                        'radius_km': radius_km,
                        'offers': offers_data
                    },
                    code=status.HTTP_200_OK
                )

        # Global Offers fallback (if no coordinates passed)
        offers_data = []
        for p in discounted_products:
            orig_price = float(p.unit_price)
            disc = float(p.discount_amount)
            offer_price = max(0.0, orig_price - disc)
            disc_pct = int(round((disc / orig_price) * 100)) if orig_price > 0 else 0
            disc_text = f"(৳{int(disc)} ছাড়!)" if disc >= 20 else f"({disc_pct}% ছাড়!)"

            offers_data.append({
                'product_id': p.id,
                'name': p.name,
                'name_bn': p.name_bn or p.name,
                'category': p.category,
                'barcode': p.barcode,
                'unit_price': orig_price,
                'offer_price': offer_price,
                'discount_amount': disc,
                'discount_percentage': disc_pct,
                'formatted_offer_price': f"৳{int(offer_price)}",
                'formatted_original_price': f"৳{int(orig_price)}",
                'discount_text': disc_text,
                'unit_info': p.unit_info,
                'weight_grams': p.weight_grams,
                'image': p.image,
                'store': None
            })

        if limit:
            offers_data = offers_data[:limit]

        return api_response(
            status=True,
            message='আজকের সেরা অফারসমূহ পাওয়া গেছে',
            data={
                'total_offers': len(offers_data),
                'nearby_stores_count': 0,
                'radius_km': radius_km,
                'offers': offers_data
            },
            code=status.HTTP_200_OK
        )


class AdminProductListCreateView(APIView):
    def get(self, request):
        queryset = Product.objects.all().order_by('-id')
        data = [{
            'id': p.id,
            'name': p.name,
            'name_bn': p.name_bn or p.name,
            'sku': p.barcode,
            'category': p.category,
            'price': float(p.unit_price),
            'cost': float(p.cost_price),
            'margin': float(p.unit_price - p.cost_price),
            'discount_amount': float(p.discount_amount),
            'unit_info': p.unit_info,
            'image': p.image,
            'weight_grams': p.weight_grams,
            'status': 'ACTIVE' if p.is_active else 'DRAFT'
        } for p in queryset]
        return api_response(
            status=True,
            message='পণ্য তালিকা সফলভাবে পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = ProductSerializer(data=request.data)
        if serializer.is_valid():
            product = serializer.save()
            return api_response(
                status=True,
                message='নতুন পণ্য সফলভাবে যুক্ত হয়েছে',
                data=ProductSerializer(product).data,
                code=status.HTTP_201_CREATED
            )
        errors = list(serializer.errors.values())[0] if serializer.errors else "পণ্যের তথ্য সঠিক নয়"
        error_msg = errors[0] if isinstance(errors, list) else str(errors)
        return api_response(status=False, message=error_msg, data=serializer.errors, code=status.HTTP_400_BAD_REQUEST)


class AdminProductDetailView(APIView):
    def get_object(self, pk):
        try:
            return Product.objects.get(pk=pk)
        except Product.DoesNotExist:
            return None

    def get(self, request, id):
        product = self.get_object(id)
        if not product:
            return api_response(status=False, message='পণ্য পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        return api_response(
            status=True,
            message='পণ্যের তথ্য পাওয়া গেছে',
            data=ProductSerializer(product).data,
            code=status.HTTP_200_OK
        )

    def patch(self, request, id):
        product = self.get_object(id)
        if not product:
            return api_response(status=False, message='পণ্য পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        if serializer.is_valid():
            updated = serializer.save()
            return api_response(
                status=True,
                message='পণ্য সফলভাবে আপডেট করা হয়েছে',
                data=ProductSerializer(updated).data,
                code=status.HTTP_200_OK
            )
        return api_response(status=False, message='তথ্য সঠিক নয়', data=serializer.errors, code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        product = self.get_object(id)
        if not product:
            return api_response(status=False, message='পণ্য পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        product.delete()
        return api_response(status=True, message='পণ্য সফলভাবে মুছে ফেলা হয়েছে', code=status.HTTP_200_OK)

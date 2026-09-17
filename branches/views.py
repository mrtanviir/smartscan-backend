from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from config.responses import api_response
from .models import Branch
from .serializers import BranchSerializer
from .utils import get_nearby_branches

class BranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        lat = request.query_params.get('lat')
        lng = request.query_params.get('lng')
        branches = Branch.objects.filter(is_active=True)

        if lat and lng:
            # Google Distance Matrix / Haversine দূরত্ব এবং রেটিং অনুযায়ী সেরা ১০টি ব্রাঞ্চ
            data = get_nearby_branches(lat, lng, list(branches), limit=10)
            return api_response(
                status=True,
                message='নিকটস্থ ব্রাঞ্চের তালিকা সফলভাবে পাওয়া গেছে',
                data=data,
                code=status.HTTP_200_OK
            )

        # সাধারণ লিস্ট
        data = [{
            'id': b.id,
            'name': b.name,
            'name_bn': b.name_bn or b.name,
            'code': b.code,
            'latitude': str(b.latitude),
            'longitude': str(b.longitude),
            'address': b.address,
            'rating': float(b.rating),
            'operating_hours': b.operating_hours,
            'image': b.image
        } for b in branches]
        return api_response(
            status=True,
            message='সকল সক্রিয় ব্রাঞ্চের তালিকা পাওয়া গেছে',
            data=data,
            code=status.HTTP_200_OK
        )

class AdminBranchListCreateView(APIView):
    def get(self, request):
        branches = Branch.objects.all().order_by('-id')
        serializer = BranchSerializer(branches, many=True)
        return api_response(
            status=True,
            message='ব্রাঞ্চের তালিকা পাওয়া গেছে',
            data=serializer.data,
            code=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = BranchSerializer(data=request.data)
        if serializer.is_valid():
            branch = serializer.save()
            return api_response(
                status=True,
                message='নতুন ব্রাঞ্চ সফলভাবে যুক্ত হয়েছে',
                data=BranchSerializer(branch).data,
                code=status.HTTP_201_CREATED
            )
        errors = list(serializer.errors.values())[0] if serializer.errors else "ব্রাঞ্চের তথ্য সঠিক নয়"
        error_msg = errors[0] if isinstance(errors, list) else str(errors)
        return api_response(status=False, message=error_msg, data=serializer.errors, code=status.HTTP_400_BAD_REQUEST)

class AdminBranchDetailView(APIView):
    def get_object(self, pk):
        try:
            return Branch.objects.get(pk=pk)
        except Branch.DoesNotExist:
            return None

    def get(self, request, id):
        branch = self.get_object(id)
        if not branch:
            return api_response(status=False, message='ব্রাঞ্চ পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        return api_response(
            status=True,
            message='ব্রাঞ্চের বিস্তারিত তথ্য পাওয়া গেছে',
            data=BranchSerializer(branch).data,
            code=status.HTTP_200_OK
        )

    def patch(self, request, id):
        branch = self.get_object(id)
        if not branch:
            return api_response(status=False, message='ব্রাঞ্চ পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        serializer = BranchSerializer(branch, data=request.data, partial=True)
        if serializer.is_valid():
            updated_branch = serializer.save()
            return api_response(
                status=True,
                message='ব্রাঞ্চের তথ্য সফলভাবে আপডেট হয়েছে',
                data=BranchSerializer(updated_branch).data,
                code=status.HTTP_200_OK
            )
        return api_response(status=False, message='তথ্য সঠিক নয়', data=serializer.errors, code=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        branch = self.get_object(id)
        if not branch:
            return api_response(status=False, message='ব্রাঞ্চ পাওয়া যায়নি', code=status.HTTP_404_NOT_FOUND)
        branch.delete()
        return api_response(status=True, message='ব্রাঞ্চ সফলভাবে মুছে ফেলা হয়েছে', code=status.HTTP_200_OK)

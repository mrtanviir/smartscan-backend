from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from accounts.models import User, Role, CustomerNotification
from branches.models import Branch
from products.models import Product
from inventory.models import Inventory

class Command(BaseCommand):
    help = 'Seeds complete realistic super shops, 45+ products, inventory stock, notifications, and demo users'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Starting complete SmartScan Supermarket Seeding...")

        # 1. Create Super Admin & Demo Users
        admin_user, _ = User.objects.get_or_create(
            phone='01700000000',
            defaults={
                'username': '01700000000',
                'email': 'admin@smartscan.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': Role.SUPER_ADMIN,
                'is_staff': True,
                'is_superuser': True
            }
        )
        admin_user.set_password('admin1234')
        admin_user.save()

        # Customer User (Sajib / Member SS-00002 matching Image 1)
        customer_user, _ = User.objects.get_or_create(
            phone='01711223344',
            defaults={
                'username': '01711223344',
                'first_name': 'sajib',
                'email': 'sajib@gmail.com',
                'role': Role.CUSTOMER,
                'loyalty_points': 38
            }
        )
        customer_user.set_password('1234')
        customer_user.first_name = 'sajib'
        customer_user.loyalty_points = 38
        customer_user.save()

        # 2. Create Major Super Shops (Branches)
        branches_data = [
            {
                'code': 'DHAKA-DHN',
                'name': 'Dhanmondi Branch',
                'name_bn': 'ধানমন্ডি শাখা',
                'latitude': 23.746100,
                'longitude': 90.374200,
                'address': 'হাউজ ১২, রোড ২৭, ধানমন্ডি, ঢাকা',
                'rating': 4.8,
                'operating_hours': 'সকাল ৮ - রাত ১১টা',
                'image': 'https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=400',
            },
            {
                'code': 'DHAKA-GUL',
                'name': 'Gulshan Branch',
                'name_bn': 'গুলশান শাখা',
                'latitude': 23.792500,
                'longitude': 90.407800,
                'address': 'প্লট ৪৫, গুলশান এভিনিউ, ঢাকা',
                'rating': 4.9,
                'operating_hours': 'সকাল ৯ - রাত ১০টা',
                'image': 'https://images.unsplash.com/photo-1534723452862-4c874018d66d?w=400',
            },
            {
                'code': 'DHAKA-UTT',
                'name': 'Uttara Branch',
                'name_bn': 'উত্তরা শাখা',
                'latitude': 23.875900,
                'longitude': 90.379500,
                'address': 'সেক্টর ৩, উত্তরা, ঢাকা',
                'rating': 4.7,
                'operating_hours': 'সকাল ৮ - রাত ১১টা',
                'image': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400',
            },
            {
                'code': 'DHAKA-BAN',
                'name': 'Banani Branch',
                'name_bn': 'বনানী শাখা',
                'latitude': 23.793700,
                'longitude': 90.404200,
                'address': 'রোড ১১, ব্লক ডি, বনানী, ঢাকা',
                'rating': 4.8,
                'operating_hours': 'সকাল ৮ - রাত ১১টা',
                'image': 'https://images.unsplash.com/photo-1543083477-4f785aeafaa9?w=400',
            },
            {
                'code': 'DHAKA-MIR',
                'name': 'Mirpur 10 Branch',
                'name_bn': 'মিরপুর ১০ শাখা',
                'latitude': 23.806900,
                'longitude': 90.368700,
                'address': 'মিরপুর ১০ গোলচত্বর, ঢাকা',
                'rating': 4.6,
                'operating_hours': 'সকাল ৮ - রাত ১১টা',
                'image': 'https://images.unsplash.com/photo-1588964895597-cfccd6e2dbf9?w=400',
            },
            {
                'code': 'DHAKA-BAS',
                'name': 'Bashundhara R/A Branch',
                'name_bn': 'বসুন্ধরা শাখা',
                'latitude': 23.816400,
                'longitude': 90.431200,
                'address': 'ব্লক সি, মেইন এভিনিউ, বসুন্ধরা আ/এ, ঢাকা',
                'rating': 4.9,
                'operating_hours': '২৪ ঘণ্টা খোলা',
                'image': 'https://images.unsplash.com/photo-1604719312566-8912e9227c6a?w=400',
            },
            {
                'code': 'CTG-GEC',
                'name': 'GEC Circle Branch',
                'name_bn': 'জিইসি সার্কেল শাখা (চট্টগ্রাম)',
                'latitude': 22.358500,
                'longitude': 91.821700,
                'address': 'জিইসি মোড়, ও আর নিজাম রোড, চট্টগ্রাম',
                'rating': 4.7,
                'operating_hours': 'সকাল ৯ - রাত ১০টা',
                'image': 'https://images.unsplash.com/photo-1578916171728-46686eac8d58?w=400',
            },
            {
                'code': 'SYL-ZIN',
                'name': 'Zindabazar Branch',
                'name_bn': 'জিন্দাবাজার শাখা (সিলেট)',
                'latitude': 24.894900,
                'longitude': 91.868700,
                'address': 'পূর্ব জিন্দাবাজার, সিলেট',
                'rating': 4.8,
                'operating_hours': 'সকাল ৯ - রাত ১০টা',
                'image': 'https://images.unsplash.com/photo-1534723452862-4c874018d66d?w=400',
            },
            {
                'code': 'US-SF-01',
                'name': 'SmartScan Supermarket (SF Branch)',
                'name_bn': 'সান ফ্রান্সিসকো শাখা',
                'latitude': 37.785834,
                'longitude': -122.406417,
                'address': '555 9th Street, San Francisco, CA',
                'rating': 4.9,
                'operating_hours': 'সকাল ৮ - রাত ১১টা',
                'image': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400',
            }
        ]

        created_branches = []
        for b_data in branches_data:
            b_obj, _ = Branch.objects.update_or_create(
                code=b_data['code'],
                defaults={
                    'name': b_data['name'],
                    'name_bn': b_data['name_bn'],
                    'latitude': b_data['latitude'],
                    'longitude': b_data['longitude'],
                    'address': b_data['address'],
                    'rating': b_data['rating'],
                    'operating_hours': b_data['operating_hours'],
                    'image': b_data['image'],
                    'is_active': True
                }
            )
            created_branches.append(b_obj)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(created_branches)} Super Shops / Branches seeded successfully."))

        # 3. Seed 45+ Realistic Supermarket Products
        products_data = [
            # --- 🍚 চাল, ডাল ও আটা (Grains & Flours) ---
            {
                'barcode': '8941100552211',
                'name': 'Mini-ket Rice - 5kg',
                'name_bn': 'মিনিকেট চাল - ৫ কেজি',
                'category': 'Grains',
                'unit_price': 550.00,
                'cost_price': 460.00,
                'discount_amount': 25.00,
                'unit_info': '৳১১০/কেজি',
                'weight_grams': 5000,
                'image': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400'
            },
            {
                'barcode': '8941100552212',
                'name': 'Nazirshail Rice - 5kg',
                'name_bn': 'নাজিরশাইল চাল - ৫ কেজি',
                'category': 'Grains',
                'unit_price': 580.00,
                'cost_price': 490.00,
                'discount_amount': 30.00,
                'unit_info': '৳১১৬/কেজি',
                'weight_grams': 5000,
                'image': 'https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=400'
            },
            {
                'barcode': '8941100552213',
                'name': 'Chinigura Polao Rice - 1kg',
                'name_bn': 'চিনিগুঁড়া পোলাও চাল - ১ কেজি',
                'category': 'Grains',
                'unit_price': 160.00,
                'cost_price': 130.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৬০/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400'
            },
            {
                'barcode': '8941100552214',
                'name': 'Basmati Premium Rice - 5kg',
                'name_bn': 'বাসমতি প্রিমিয়াম চাল - ৫ কেজি',
                'category': 'Grains',
                'unit_price': 850.00,
                'cost_price': 720.00,
                'discount_amount': 50.00,
                'unit_info': '৳১৭০/কেজি',
                'weight_grams': 5000,
                'image': 'https://images.unsplash.com/photo-1536304993881-ff6e9eefa2a6?w=400'
            },
            {
                'barcode': '8941100552215',
                'name': 'Fortune Atta - 2kg',
                'name_bn': 'ফরচুন আটা - ২ কেজি',
                'category': 'Grains',
                'unit_price': 130.00,
                'cost_price': 105.00,
                'discount_amount': 10.00,
                'unit_info': '৳৬৫/কেজি',
                'weight_grams': 2000,
                'image': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400'
            },
            {
                'barcode': '8941100552216',
                'name': 'Teer Premium Maida - 2kg',
                'name_bn': 'তীর ময়দা - ২ কেজি',
                'category': 'Grains',
                'unit_price': 150.00,
                'cost_price': 120.00,
                'discount_amount': 15.00,
                'unit_info': '৳৭৫/কেজি',
                'weight_grams': 2000,
                'image': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400'
            },
            {
                'barcode': '8941100552217',
                'name': 'Deshi Musur Daal - 1kg',
                'name_bn': 'দেশি মসুর ডাল - ১ কেজি',
                'category': 'Grains',
                'unit_price': 140.00,
                'cost_price': 115.00,
                'discount_amount': 10.00,
                'unit_info': '৳১৪০/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1585994192701-f1a505c817ea?w=400'
            },
            {
                'barcode': '8941100552218',
                'name': 'Moong Daal Premium - 1kg',
                'name_bn': 'মুগ ডাল প্রিমিয়াম - ১ কেজি',
                'category': 'Grains',
                'unit_price': 160.00,
                'cost_price': 130.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৬০/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1585994192701-f1a505c817ea?w=400'
            },

            # --- 🛢️ তেল ও ঘি (Oils & Ghee) ---
            {
                'barcode': '8941100552233',
                'name': 'Rupchanda Soybean Oil - 2L',
                'name_bn': 'রূপচাঁদা সয়াবিন তেল - ২ লিটার',
                'category': 'Oil & Ghee',
                'unit_price': 350.00,
                'cost_price': 300.00,
                'discount_amount': 35.00,
                'unit_info': '৳১৭৫/লিটার',
                'weight_grams': 2000,
                'image': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400'
            },
            {
                'barcode': '8941100552234',
                'name': 'Teer Soybean Oil - 5L',
                'name_bn': 'তীর সয়াবিন তেল - ৫ লিটার',
                'category': 'Oil & Ghee',
                'unit_price': 860.00,
                'cost_price': 760.00,
                'discount_amount': 45.00,
                'unit_info': '৳১৭২/লিটার',
                'weight_grams': 5000,
                'image': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400'
            },
            {
                'barcode': '8941100552235',
                'name': 'Radhuni Pure Mustard Oil - 1L',
                'name_bn': 'রাধুনী খাঁটি সরিষার তেল - ১ লিটার',
                'category': 'Oil & Ghee',
                'unit_price': 320.00,
                'cost_price': 270.00,
                'discount_amount': 25.00,
                'unit_info': '৳৩২০/লিটার',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400'
            },
            {
                'barcode': '8941100552236',
                'name': 'Aarong Pure Butter Ghee - 500g',
                'name_bn': 'আড়ং খাঁটি ঘি - ৫০০ গ্রাম',
                'category': 'Oil & Ghee',
                'unit_price': 650.00,
                'cost_price': 540.00,
                'discount_amount': 50.00,
                'unit_info': '৳৬৫০/জার',
                'weight_grams': 500,
                'image': 'https://images.unsplash.com/photo-1589927986089-35812388d1f4?w=400'
            },

            # --- 🥛 দুগ্ধ ও ডিম (Dairy & Eggs) ---
            {
                'barcode': '8941100552244',
                'name': 'Aarong Pasteurized Liquid Milk - 1L',
                'name_bn': 'আড়ং তাজা তরল দুধ - ১ লিটার',
                'category': 'Dairy',
                'unit_price': 90.00,
                'cost_price': 75.00,
                'discount_amount': 5.00,
                'unit_info': '৳৯০/লিটার',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400'
            },
            {
                'barcode': '8941100552245',
                'name': 'Dano Full Cream Milk Powder - 1kg',
                'name_bn': 'ডানো ফুল ক্রিম গুঁড়ো দুধ - ১ কেজি',
                'category': 'Dairy',
                'unit_price': 890.00,
                'cost_price': 770.00,
                'discount_amount': 60.00,
                'unit_info': '৳৮৯০/প্যাকেট',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400'
            },
            {
                'barcode': '8941100552246',
                'name': 'Farm Fresh Brown Eggs - 12 Pcs',
                'name_bn': 'ফার্ম ফ্রেশ লাল ডিম - ১২ পিস',
                'category': 'Dairy',
                'unit_price': 155.00,
                'cost_price': 130.00,
                'discount_amount': 10.00,
                'unit_info': '৳১৩০/ডজন',
                'weight_grams': 720,
                'image': 'https://images.unsplash.com/photo-1582722872445-44dc5f7e3c8f?w=400'
            },
            {
                'barcode': '8941100552247',
                'name': 'Aarong Salted Butter - 200g',
                'name_bn': 'আড়ং বাটার - ২০০ গ্রাম',
                'category': 'Dairy',
                'unit_price': 220.00,
                'cost_price': 180.00,
                'discount_amount': 15.00,
                'unit_info': '৳২২০/পিস',
                'weight_grams': 200,
                'image': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400'
            },

            # --- 🧂 মশলা ও চিনি (Spices & Sugar) ---
            {
                'barcode': '8941100552261',
                'name': 'Radhuni Turmeric Powder - 200g',
                'name_bn': 'রাধুনী হলুদের গুঁড়া - ২০০ গ্রাম',
                'category': 'Spices',
                'unit_price': 95.00,
                'cost_price': 75.00,
                'discount_amount': 8.00,
                'unit_info': '৳৯৫/প্যাকেট',
                'weight_grams': 200,
                'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400'
            },
            {
                'barcode': '8941100552262',
                'name': 'Radhuni Chilli Powder - 200g',
                'name_bn': 'রাধুনী মরিচের গুঁড়া - ২০০ গ্রাম',
                'category': 'Spices',
                'unit_price': 110.00,
                'cost_price': 88.00,
                'discount_amount': 10.00,
                'unit_info': '৳১১০/প্যাকেট',
                'weight_grams': 200,
                'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400'
            },
            {
                'barcode': '8941100552263',
                'name': 'Radhuni Biryani Masala - 40g',
                'name_bn': 'রাধুনী বিরিয়ানি মশলা - ৪০ গ্রাম',
                'category': 'Spices',
                'unit_price': 65.00,
                'cost_price': 50.00,
                'discount_amount': 5.00,
                'unit_info': '৳৬৫/প্যাকেট',
                'weight_grams': 40,
                'image': 'https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400'
            },
            {
                'barcode': '8941100552264',
                'name': 'Fresh Refined Sugar - 1kg',
                'name_bn': 'ফ্রেশ পরিশোধিত চিনি - ১ কেজি',
                'category': 'Spices',
                'unit_price': 140.00,
                'cost_price': 120.00,
                'discount_amount': 10.00,
                'unit_info': '৳১৪০/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1581441363689-1f3c3c414635?w=400'
            },
            {
                'barcode': '8941100552265',
                'name': 'Teer Vacuum Iodized Salt - 1kg',
                'name_bn': 'তীর আয়োডিনযুক্ত লবণ - ১ কেজি',
                'category': 'Spices',
                'unit_price': 42.00,
                'cost_price': 32.00,
                'discount_amount': 4.00,
                'unit_info': '৳৪২/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?w=400'
            },

            # --- ☕ চা ও কোমল পানীয় (Tea & Beverages) ---
            {
                'barcode': '8941100552271',
                'name': 'Ispahani Mirzapore Tea Bag - 100 Pcs',
                'name_bn': 'ইস্পাহানি মির্জাপুর টি ব্যাগ - ১০০ পিস',
                'category': 'Beverages',
                'unit_price': 190.00,
                'cost_price': 155.00,
                'discount_amount': 20.00,
                'unit_info': '৳১৯০/বক্স',
                'weight_grams': 200,
                'image': 'https://images.unsplash.com/photo-1576092768241-dec231879fc3?w=400'
            },
            {
                'barcode': '8941100552272',
                'name': 'Nescafe Classic Coffee Jar - 100g',
                'name_bn': 'নেসক্যাফে কফি জার - ১০০ গ্রাম',
                'category': 'Beverages',
                'unit_price': 420.00,
                'cost_price': 340.00,
                'discount_amount': 30.00,
                'unit_info': '৳৪২০/জার',
                'weight_grams': 100,
                'image': 'https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=400'
            },
            {
                'barcode': '8941100552273',
                'name': 'Coca-Cola Bottle - 1.5L',
                'name_bn': 'কোকাকোলা - ১.৫ লিটার',
                'category': 'Beverages',
                'unit_price': 110.00,
                'cost_price': 90.00,
                'discount_amount': 10.00,
                'unit_info': '৳১১০/বোতল',
                'weight_grams': 1500,
                'image': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400'
            },
            {
                'barcode': '8941100552274',
                'name': 'Pran Mango Fruit Drink - 1L',
                'name_bn': 'প্রাণ ম্যাঙ্গো জুস - ১ লিটার',
                'category': 'Beverages',
                'unit_price': 120.00,
                'cost_price': 95.00,
                'discount_amount': 15.00,
                'unit_info': '৳১২০/বোতল',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1534353473418-4cfa6c56fd38?w=400'
            },

            # --- 🍪 বিস্কুট, স্ন্যাক্স ও চকলেট (Biscuits & Snacks) ---
            {
                'barcode': '8941100552281',
                'name': 'Oreo Original Sandwich Biscuits - 120g',
                'name_bn': 'ওরিও স্যান্ডউইচ বিস্কুট - ১২০ গ্রাম',
                'category': 'Snacks',
                'unit_price': 60.00,
                'cost_price': 48.00,
                'discount_amount': 5.00,
                'unit_info': '৳৬০/প্যাকেট',
                'weight_grams': 120,
                'image': 'https://images.unsplash.com/photo-1563729784474-d77dbb933a9e?w=400'
            },
            {
                'barcode': '8941100552282',
                'name': 'Pran Dry Cake Toast - 350g',
                'name_bn': 'প্রাণ ড্রাই কেক টোস্ট - ৩৫০ গ্রাম',
                'category': 'Snacks',
                'unit_price': 110.00,
                'cost_price': 85.00,
                'discount_amount': 10.00,
                'unit_info': '৳১১০/প্যাকেট',
                'weight_grams': 350,
                'image': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400'
            },
            {
                'barcode': '8941100552283',
                'name': 'Lays Classic Salted Potato Chips - 50g',
                'name_bn': 'লেইস পটেটো চিপস - ৫০ গ্রাম',
                'category': 'Snacks',
                'unit_price': 50.00,
                'cost_price': 38.00,
                'discount_amount': 5.00,
                'unit_info': '৳৫০/প্যাকেট',
                'weight_grams': 50,
                'image': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400'
            },
            {
                'barcode': '8941100552284',
                'name': 'Cadbury Dairy Milk Silk - 60g',
                'name_bn': 'ক্যাডবেরি ডেইরি মিল্ক সিল্ক - ৬০ গ্রাম',
                'category': 'Snacks',
                'unit_price': 180.00,
                'cost_price': 140.00,
                'discount_amount': 20.00,
                'unit_info': '৳১৮০/বার',
                'weight_grams': 60,
                'image': 'https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=400'
            },

            # --- 🧼 প্রসাধন ও ক্লিনিং (Toiletries & Cleaning) ---
            {
                'barcode': '8941100552291',
                'name': 'Surf Excel Detergent Powder - 1kg',
                'name_bn': 'সার্ফ এক্সেল ডিটারজেন্ট - ১ কেজি',
                'category': 'Cleaning',
                'unit_price': 240.00,
                'cost_price': 195.00,
                'discount_amount': 25.00,
                'unit_info': '৳২৪০/প্যাকেট',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1585421514738-01798e348b17?w=400'
            },
            {
                'barcode': '8941100552292',
                'name': 'Harpic Power Plus Toilet Cleaner - 750ml',
                'name_bn': 'হারপিক টয়লেট ক্লিনার - ৭৫০ মিলি',
                'category': 'Cleaning',
                'unit_price': 185.00,
                'cost_price': 150.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৮৫/বোতল',
                'weight_grams': 750,
                'image': 'https://images.unsplash.com/photo-1584813470613-5b1c1cad3d69?w=400'
            },
            {
                'barcode': '8941100552293',
                'name': 'Sunsilk Black Shine Shampoo - 375ml',
                'name_bn': 'সানসিল্ক ব্ল্যাক শাইন শ্যাম্পু - ৩৭৫ মিলি',
                'category': 'Personal Care',
                'unit_price': 380.00,
                'cost_price': 310.00,
                'discount_amount': 30.00,
                'unit_info': '৳৩৮০/বোতল',
                'weight_grams': 375,
                'image': 'https://images.unsplash.com/photo-1535585209827-a15fcdbc4c2d?w=400'
            },
            {
                'barcode': '8941100552294',
                'name': 'Close Up Red Hot Toothpaste - 150g',
                'name_bn': 'ক্লোজ আপ টুথপেস্ট - ১৫০ গ্রাম',
                'category': 'Personal Care',
                'unit_price': 145.00,
                'cost_price': 115.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৪৫/পিস',
                'weight_grams': 150,
                'image': 'https://images.unsplash.com/photo-1559563458-527698bf5295?w=400'
            },
            {
                'barcode': '8941100552295',
                'name': 'Savlon Antiseptic Handwash - 250ml',
                'name_bn': 'স্যাভলন হ্যান্ডওয়াশ - ২৫০ মিলি',
                'category': 'Personal Care',
                'unit_price': 115.00,
                'cost_price': 90.00,
                'discount_amount': 10.00,
                'unit_info': '৳১১৫/বোতল',
                'weight_grams': 250,
                'image': 'https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=400'
            },
            {
                'barcode': '8941100552296',
                'name': 'Dettol Original Soap (3 Pcs Pack)',
                'name_bn': 'ডেটল সাবান (৩ পিস প্যাক)',
                'category': 'Personal Care',
                'unit_price': 180.00,
                'cost_price': 145.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৮০/প্যাক',
                'weight_grams': 300,
                'image': 'https://images.unsplash.com/photo-1600857544200-b2f666a9a2ec?w=400'
            },
            {
                'barcode': '8941100552297',
                'name': 'Vim Dishwash Liquid Gel - 500ml',
                'name_bn': 'ভিম ডিশওয়াশ লিকুইড - ৫০০ মিলি',
                'category': 'Cleaning',
                'unit_price': 150.00,
                'cost_price': 120.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৫০/বোতল',
                'weight_grams': 500,
                'image': 'https://images.unsplash.com/photo-1584813470613-5b1c1cad3d69?w=400'
            },
            {
                'barcode': '8941100552298',
                'name': 'Maggi 2-Minute Noodles Masala (8 Pack)',
                'name_bn': 'ম্যাগি ২-মিনিট নুডলস (৮ প্যাক)',
                'category': 'Snacks',
                'unit_price': 190.00,
                'cost_price': 155.00,
                'discount_amount': 20.00,
                'unit_info': '৳১৯০/প্যাক',
                'weight_grams': 496,
                'image': 'https://images.unsplash.com/photo-1612927601601-6638404737ce?w=400'
            },
            {
                'barcode': '8941100552299',
                'name': 'Pran Tomato Ketchup - 350g',
                'name_bn': 'প্রাণ টমেটো কেচাপ - ৩৫০ গ্রাম',
                'category': 'Spices',
                'unit_price': 90.00,
                'cost_price': 70.00,
                'discount_amount': 10.00,
                'unit_info': '৳৯০/বোতল',
                'weight_grams': 350,
                'image': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400'
            },
            {
                'barcode': '8941100552301',
                'name': 'Fresh Red Onion - 1kg',
                'name_bn': 'দেশি লাল পেঁয়াজ - ১ কেজি',
                'category': 'Fresh Produce',
                'unit_price': 80.00,
                'cost_price': 60.00,
                'discount_amount': 10.00,
                'unit_info': '৳৮০/কেজি',
                'weight_grams': 1000,
                'image': 'https://images.unsplash.com/photo-1508747703725-719777637510?w=400'
            },
            {
                'barcode': '8941100552302',
                'name': 'Fresh Diamond Potato - 2kg',
                'name_bn': 'ফ্রেশ ডায়মন্ড গোল আলু - ২ কেজি',
                'category': 'Fresh Produce',
                'unit_price': 90.00,
                'cost_price': 70.00,
                'discount_amount': 10.00,
                'unit_info': '৳৪৫/কেজি',
                'weight_grams': 2000,
                'image': 'https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=400'
            },
            {
                'barcode': '8941100552303',
                'name': 'Pran Mustard Kasundi - 250g',
                'name_bn': 'প্রাণ সরিষার কাসুন্দি - ২৫০ গ্রাম',
                'category': 'Spices',
                'unit_price': 75.00,
                'cost_price': 55.00,
                'discount_amount': 5.00,
                'unit_info': '৳৭৫/বোতল',
                'weight_grams': 250,
                'image': 'https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400'
            },
            {
                'barcode': '8941100552304',
                'name': 'Mr. Noodles Instant Chicken (8 Pack)',
                'name_bn': 'মিস্টার নুডলস চিকেন (৮ প্যাক)',
                'category': 'Snacks',
                'unit_price': 180.00,
                'cost_price': 140.00,
                'discount_amount': 20.00,
                'unit_info': '৳১৮০/প্যাক',
                'weight_grams': 496,
                'image': 'https://images.unsplash.com/photo-1612927601601-6638404737ce?w=400'
            },
            {
                'barcode': '8941100552305',
                'name': 'KitKat 4 Finger Chocolate - 41.5g',
                'name_bn': 'কিটক্যাট চকলেট - ৪১.৫ গ্রাম',
                'category': 'Snacks',
                'unit_price': 95.00,
                'cost_price': 75.00,
                'discount_amount': 10.00,
                'unit_info': '৳৯৫/বার',
                'weight_grams': 42,
                'image': 'https://images.unsplash.com/photo-1541781774459-bb2af2f05b55?w=400'
            },
            {
                'barcode': '8941100552306',
                'name': 'Aarong Sweet Curd (Misti Doi) - 500g',
                'name_bn': 'আড়ং মিষ্টি দই - ৫০০ গ্রাম',
                'category': 'Dairy',
                'unit_price': 140.00,
                'cost_price': 110.00,
                'discount_amount': 15.00,
                'unit_info': '৳১৪০/কাপ',
                'weight_grams': 500,
                'image': 'https://images.unsplash.com/photo-1550583724-b2692b85b150?w=400'
            }
        ]

        created_products = []
        for p_data in products_data:
            p_obj, _ = Product.objects.update_or_create(
                barcode=p_data['barcode'],
                defaults={
                    'name': p_data['name'],
                    'name_bn': p_data['name_bn'],
                    'category': p_data['category'],
                    'unit_price': p_data['unit_price'],
                    'cost_price': p_data['cost_price'],
                    'discount_amount': p_data['discount_amount'],
                    'unit_info': p_data['unit_info'],
                    'weight_grams': p_data['weight_grams'],
                    'image': p_data['image'],
                    'is_active': True
                }
            )
            created_products.append(p_obj)

        self.stdout.write(self.style.SUCCESS(f"✓ {len(created_products)} Realistic Supermarket Products seeded."))

        # 4. Create Inventory Stock in all Branches
        for branch in created_branches:
            for p in created_products:
                Inventory.objects.update_or_create(
                    branch=branch,
                    product=p,
                    defaults={
                        'stock_quantity': 120,
                        'min_safety_threshold': 15
                    }
                )
        self.stdout.write(self.style.SUCCESS("✓ Inventory stock linked to all Super Shops."))

        # 5. Create Customer Notifications matching Image 2
        now = timezone.now()
        customer_users = [customer_user]

        user_sajib, _ = User.objects.get_or_create(
            phone='01521771457',
            defaults={
                'username': '01521771457',
                'first_name': 'sajib',
                'email': 'sajib@gmail.com',
                'role': Role.CUSTOMER,
                'loyalty_points': 38
            }
        )
        user_sajib.first_name = 'sajib'
        user_sajib.loyalty_points = 38
        user_sajib.save()
        customer_users.append(user_sajib)

        for u in customer_users:
            notifications_data = [
                {
                    'user': u,
                    'title': 'গেট পাস প্রস্তুত!',
                    'message': 'আপনার ধানমন্ডি শাখার গেট পাস প্রস্তুত! অর্ডার #SS753EB1 এর কিউআর কোড স্ক্যান করে দ্রুত ট্রলি বের করুন।',
                    'category': 'ORDER',
                    'icon_type': 'GATE_PASS',
                    'action_type': 'OPEN_GATE_PASS',
                    'action_data': {'order_number': 'SS753EB1'},
                    'is_read': False,
                    'created_at': now - timedelta(minutes=5)
                },
                {
                    'user': u,
                    'title': 'আজকের স্পেশাল অফার!',
                    'message': 'চিনিগুঁড়া পোলাও চাল ও সয়াবিন তেলে বিশেষ ছাড়! আজকের কেনাকাটায় পেয়ে যান আকর্ষণীয় ক্যাশব্যাক।',
                    'category': 'OFFER',
                    'icon_type': 'OFFER',
                    'action_type': 'OPEN_OFFER',
                    'action_data': {'category': 'Grains'},
                    'is_read': False,
                    'created_at': now - timedelta(hours=2)
                },
                {
                    'user': u,
                    'title': '+১২০ লয়ালটি পয়েন্ট যোগ হয়েছে!',
                    'message': 'অভিনন্দন! আপনার অ্যাকাউন্টে নতুন ১২০ পয়েন্ট যোগ হয়েছে। পরবর্তী কেনাকাটায় ছাড় পেতে রিডিম করুন।',
                    'category': 'LOYALTY',
                    'icon_type': 'LOYALTY',
                    'action_type': 'REDEEM_POINTS',
                    'action_data': {'points': 120},
                    'is_read': True,
                    'created_at': now - timedelta(days=1, hours=3)
                },
                {
                    'user': u,
                    'title': 'স্মার্ট কার্ট আপডেট',
                    'message': 'আপনার ট্রলিতে পণ্য সফলভাবে যুক্ত করা হয়েছে। বিল রিভিউ ও দ্রুত পেমেন্ট সম্পন্ন করতে ট্যাপ করুন।',
                    'category': 'CART',
                    'icon_type': 'CART',
                    'action_type': 'OPEN_CART',
                    'action_data': {},
                    'is_read': True,
                    'created_at': now - timedelta(days=2)
                },
                {
                    'user': u,
                    'title': 'উইকএন্ড ধামাকা অফার!',
                    'message': 'এই শুক্র ও শনিবার ১০০০ টাকার বেশি কেনাকাটায় পাবেন বিনামূল্যে হোম ডেলিভারি ও ৫০ লয়ালটি পয়েন্ট!',
                    'category': 'OFFER',
                    'icon_type': 'OFFER',
                    'action_type': 'OPEN_OFFER',
                    'action_data': {'discount_pct': 15},
                    'is_read': True,
                    'created_at': now - timedelta(days=3)
                }
            ]

            for n_data in notifications_data:
                created_at = n_data.pop('created_at')
                notif, created = CustomerNotification.objects.get_or_create(
                    user=n_data['user'],
                    title=n_data['title'],
                    defaults=n_data
                )
                if created:
                    notif.created_at = created_at
                    notif.save()

        self.stdout.write(self.style.SUCCESS("✓ Customer Notifications seeded matching Image 2."))
        self.stdout.write(self.style.SUCCESS("🎉 Seeding completed successfully!"))

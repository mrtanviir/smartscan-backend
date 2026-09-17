import math
import requests
import re
from decimal import Decimal
from django.conf import settings
from .models import Branch

def calculate_haversine_distance(lat1, lon1, lat2, lon2):
    """
    Haversine formula to calculate straight-line distance in km and meters
    """
    try:
        lat1, lon1, lat2, lon2 = map(float, [lat1, lon1, lat2, lon2])
        R = 6371  # Earth radius in kilometers
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = math.sin(dLat / 2) * math.sin(dLat / 2) + \
            math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * \
            math.sin(dLon / 2) * math.sin(dLon / 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        d_km = R * c
        return round(d_km, 1), int(d_km * 1000)
    except Exception:
        return 999.0, 999000

def get_nearby_branches(user_lat, user_lng, branches=None, limit=10):
    """
    Returns up to 10 nearby supermarkets and stores dynamically taken directly from Google Places API
    based on the user's exact current GPS location (lat, lng).
    """
    try:
        u_lat = float(user_lat)
        u_lng = float(user_lng)
    except (ValueError, TypeError):
        return []

    google_api_key = getattr(settings, 'GOOGLE_MAPS_API_KEY', '')
    google_places_list = []
    seen_store_names = set()

    # 1. Live Dynamic Search directly from Google Places API
    if google_api_key:
        try:
            places_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={u_lat},{u_lng}&radius=15000&type=supermarket|grocery_or_supermarket&keyword=supermarket|grocery|supershop&key={google_api_key}"
            response = requests.get(places_url, timeout=6).json()
            if response.get('status') == 'OK' and response.get('results'):
                for place in response['results']:
                    loc = place.get('geometry', {}).get('location', {})
                    p_lat = loc.get('lat')
                    p_lng = loc.get('lng')
                    if not p_lat or not p_lng:
                        continue

                    p_name = place.get('name', 'Supermarket')
                    p_vicinity = place.get('vicinity') or place.get('formatted_address') or 'Supermarket Area'
                    
                    norm_name = p_name.strip().lower()
                    if norm_name in seen_store_names:
                        continue
                    seen_store_names.add(norm_name)

                    p_rating = float(place.get('rating', 4.5))
                    place_id = place.get('place_id', '')

                    # Generate clean branch code
                    clean_name = re.sub(r'[^A-Za-z0-9]', '', p_name)[:6].upper() or 'SHOP'
                    branch_code = f"GP-{clean_name}-{place_id[:4]}"

                    # Ensure it exists in Branch model so it has a valid database ID for Cart & Checkout
                    branch_obj, _ = Branch.objects.get_or_create(
                        code=branch_code,
                        defaults={
                            'name': p_name,
                            'name_bn': p_name,
                            'latitude': Decimal(str(round(p_lat, 6))),
                            'longitude': Decimal(str(round(p_lng, 6))),
                            'address': p_vicinity,
                            'rating': Decimal(str(round(p_rating, 1))),
                            'operating_hours': 'সকাল ৮ - রাত ১১টা' if '24' not in p_name else '২৪ ঘণ্টা খোলা',
                            'image': 'https://images.unsplash.com/photo-1542838132-92c53300491e?w=400',
                            'is_active': True
                        }
                    )

                    dist_km, dist_meters = calculate_haversine_distance(u_lat, u_lng, p_lat, p_lng)
                    dist_text = f"{dist_km} কিমি দূরে" if dist_km >= 1.0 else f"{dist_meters} মিটার দূরে"

                    google_places_list.append({
                        'id': branch_obj.id,
                        'name': p_name,
                        'name_bn': p_name,
                        'code': branch_obj.code,
                        'latitude': str(p_lat),
                        'longitude': str(p_lng),
                        'address': p_vicinity,
                        'distance': dist_text,
                        'distance_text': dist_text,
                        'distance_km': dist_km,
                        'distance_meters': dist_meters,
                        'rating': p_rating,
                        'operating_hours': branch_obj.operating_hours,
                        'image': branch_obj.image
                    })
        except Exception:
            pass

    # If Google Places returned live nearby stores, sort by distance & rating and return
    if google_places_list:
        google_places_list.sort(key=lambda x: (x['distance_meters'], -x['rating']))
        return google_places_list[:limit]

    # Fallback to database branches only if Google API had 0 results / offline
    if branches is None:
        branches = list(Branch.objects.filter(is_active=True))

    db_results = []
    for b in branches:
        dist_km, dist_meters = calculate_haversine_distance(u_lat, u_lng, b.latitude, b.longitude)
        dist_text = f"{dist_km} কিমি দূরে" if dist_km >= 1.0 else f"{dist_meters} মিটার দূরে"
        db_results.append({
            'id': b.id,
            'name': b.name,
            'name_bn': b.name_bn or b.name,
            'code': b.code,
            'latitude': str(b.latitude),
            'longitude': str(b.longitude),
            'address': b.address,
            'distance': dist_text,
            'distance_text': dist_text,
            'distance_km': dist_km,
            'distance_meters': dist_meters,
            'rating': float(b.rating),
            'operating_hours': b.operating_hours,
            'image': b.image
        })

    db_results.sort(key=lambda x: (x['distance_meters'], -x['rating']))
    return db_results[:limit]

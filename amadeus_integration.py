"""
Amadeus Hotel API Integration
Provides real-time hotel availability, pricing, and booking data
"""

import os
import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()


class AmadeusHotelAPI:
    """
    Integration with Amadeus Hotel API for real-time hotel data
    Free tier: 2,000 API calls/month
    Sign up: https://developers.amadeus.com
    """
    
    def __init__(self, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_key = api_key or os.getenv("AMADEUS_API_KEY")
        self.api_secret = api_secret or os.getenv("AMADEUS_API_SECRET")
        self.base_url = "https://test.api.amadeus.com/v1"  # Test environment
        # For production: https://api.amadeus.com/v1
        self.access_token = None
        self.token_expires_at = None
        
    def _get_access_token(self) -> str:
        """Get or refresh OAuth access token"""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at:
            if datetime.now() < self.token_expires_at:
                return self.access_token
        
        # Get new token
        auth_url = "https://test.api.amadeus.com/v1/security/oauth2/token"
        
        data = {
            'grant_type': 'client_credentials',
            'client_id': self.api_key,
            'client_secret': self.api_secret
        }
        
        try:
            response = requests.post(auth_url, data=data, timeout=10)
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data['access_token']
            expires_in = token_data['expires_in']
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 60)
            
            return self.access_token
        except Exception as e:
            raise Exception(f"Failed to get Amadeus access token: {e}")
    
    def search_hotels_by_city(self, city_code: str, radius: int = 5, 
                              radius_unit: str = "MILE") -> List[Dict]:
        """
        Search for hotels by city
        
        Args:
            city_code: IATA city code (e.g., 'CLT' for Charlotte, 'NYC' for New York)
            radius: Search radius
            radius_unit: MILE or KM
        
        Returns:
            List of hotels with basic info
        """
        token = self._get_access_token()
        
        url = f"{self.base_url}/reference-data/locations/hotels/by-city"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "cityCode": city_code,
            "radius": radius,
            "radiusUnit": radius_unit
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"Error searching hotels: {e}")
            return []
    
    def get_hotel_offers(self, hotel_ids: List[str], check_in: str, 
                        check_out: str, adults: int = 1, 
                        room_quantity: int = 1) -> List[Dict]:
        """
        Get hotel room offers with pricing
        
        Args:
            hotel_ids: List of Amadeus hotel IDs
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            adults: Number of adults
            room_quantity: Number of rooms
        
        Returns:
            List of hotel offers with rooms and pricing
        """
        token = self._get_access_token()
        
        url = f"{self.base_url}/shopping/hotel-offers"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        params = {
            "hotelIds": ",".join(hotel_ids),
            "checkInDate": check_in,
            "checkOutDate": check_out,
            "adults": adults,
            "roomQuantity": room_quantity
        }
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            return data.get('data', [])
        except Exception as e:
            print(f"Error getting hotel offers: {e}")
            return []
    
    def search_charlotte_airport_hotels(self, check_in: str, check_out: str, 
                                       guests: int = 1) -> List[Dict]:
        """
        Search ONLY for Hyatt House Charlotte Airport hotel
        This is a single-hotel focused system
        
        Args:
            check_in: Check-in date (YYYY-MM-DD)
            check_out: Check-out date (YYYY-MM-DD)
            guests: Number of guests
        
        Returns:
            Formatted hotel data for Hyatt House Charlotte Airport only
        """
        # Search specifically for Hyatt House Charlotte Airport
        # Hotel ID: HYCLTCHA
        hotels = self.search_hotels_by_city("CLT", radius=5)
        
        if not hotels:
            # No hotels found - will use static fallback
            return []
        
        # Search for the SPECIFIC Hyatt House Airport hotel
        hyatt_airport = None
        for h in hotels:
            if h.get('hotelId') == 'HYCLTCHA':  # Exact Hyatt House Charlotte Airport
                hyatt_airport = h
                break
        
        if not hyatt_airport:
            # Fallback: any Hyatt House property
            hyatt_hotels = [h for h in hotels if h.get('chainCode') == 'HY']
            if hyatt_hotels:
                hyatt_airport = hyatt_hotels[0]
        
        if not hyatt_airport:
            # No Hyatt found - will use static data
            return []
        
        # Use ONLY this specific hotel
        hotel_ids = [hyatt_airport['hotelId']]
        
        # Get offers with pricing
        offers = self.get_hotel_offers(hotel_ids, check_in, check_out, adults=guests)
        
        # Format as our standard room format
        formatted_rooms = []
        
        for hotel_offer in offers:
            hotel = hotel_offer.get('hotel', {})
            offers_list = hotel_offer.get('offers', [])
            
            for offer in offers_list[:5]:  # Get up to 5 room types
                room = offer.get('room', {})
                price = offer.get('price', {})
                
                formatted_room = {
                    'id': offer.get('id', '')[:6],
                    'hotel_name': 'Hyatt House Charlotte Airport',  # Fixed hotel name
                    'type': room.get('typeEstimated', {}).get('category', 'Standard Room'),
                    'description': room.get('description', {}).get('text', 'Comfortable room'),
                    'amenities': self._extract_amenities(room),
                    'price_per_night': float(price.get('total', 0)),
                    'currency': price.get('currency', 'USD'),
                    'capacity': room.get('typeEstimated', {}).get('beds', 2),
                    'available': True,
                    'source': 'amadeus'
                }
                formatted_rooms.append(formatted_room)
        
        return formatted_rooms
    
    def _extract_amenities(self, room: Dict) -> List[str]:
        """Extract amenities from room data"""
        amenities = []
        
        # Standard amenities
        amenities.append("Free WiFi")
        
        # Extract from description if available
        desc = room.get('description', {}).get('text', '').lower()
        
        if 'tv' in desc or 'television' in desc:
            amenities.append("Flat-screen TV")
        if 'coffee' in desc or 'keurig' in desc:
            amenities.append("Coffee maker")
        if 'minibar' in desc or 'mini-bar' in desc or 'fridge' in desc:
            amenities.append("Mini-fridge")
        if 'desk' in desc or 'workspace' in desc:
            amenities.append("Work desk")
        if 'view' in desc:
            amenities.append("Room view")
        
        # Add bed info
        bed_type = room.get('typeEstimated', {}).get('bedType', '')
        if bed_type:
            amenities.append(f"{bed_type} bed")
        
        return amenities if amenities else ["Standard amenities"]
    
    def is_configured(self) -> bool:
        """Check if Amadeus API is configured"""
        return bool(self.api_key and self.api_secret)


# Singleton instance
amadeus_api = None

def get_amadeus_api() -> AmadeusHotelAPI:
    """Get or create Amadeus API instance"""
    global amadeus_api
    if amadeus_api is None:
        amadeus_api = AmadeusHotelAPI()
    return amadeus_api


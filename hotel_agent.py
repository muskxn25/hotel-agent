"""
Hotel Front Desk Agent - Main Logic
Handles intent recognition, booking operations, and response generation
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import re


class HotelAgent:
    def __init__(self, data_file='hotel_data.json'):
        self.data_file = data_file
        self.load_data()
        
    def load_data(self):
        """Load hotel data from JSON file"""
        with open(self.data_file, 'r') as f:
            self.data = json.load(f)
    
    def save_data(self):
        """Save hotel data back to JSON file"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def get_greeting(self) -> str:
        """Return a friendly greeting message"""
        return (
            f"Welcome to Hyatt House Charlotte Airport! ✈️\n\n"
            "I'm Sarah from the front desk. How can I help you today?\n\n"
            "**1.** Check room availability\n"
            "**2.** Book a reservation\n"
            "**3.** Cancel a reservation\n"
            "**4.** View amenities & facilities\n"
            "**5.** Hotel policies & FAQ\n\n"
            "**Please select a number (1-5) or type your question.**"
        )
    
    def process_message(self, message: str, use_llm: bool = False, llm_api_key: str = None) -> str:
        """
        Process user message and return appropriate response
        
        Args:
            message: User's message
            use_llm: Whether to use LLM for intent recognition
            llm_api_key: API key for LLM service
        
        Returns:
            Agent's response
        """
        message_lower = message.lower().strip()
        
        # Handle numbered menu options
        if message_lower in ['1', 'option 1', '1.']:
            return self._handle_availability({})
        elif message_lower in ['2', 'option 2', '2.']:
            return "I'd be happy to help you book a room! 🏨\n\nTo find the perfect room for you, I need a few details:\n\n**1.** How many guests will be staying?\n**2.** What are your check-in and check-out dates?\n\nYou can respond like: \"2 guests, checking in Oct 15, checking out Oct 17\"\n\nOr answer one at a time!"
        elif message_lower in ['3', 'option 3', '3.']:
            return self._handle_cancellation({})
        elif message_lower in ['4', 'option 4', '4.']:
            return self._handle_amenities({})
        elif message_lower in ['5', 'option 5', '5.']:
            return self._handle_policies({})
        
        # Intent detection
        if use_llm and llm_api_key:
            intent, entities = self._detect_intent_llm(message, llm_api_key)
        else:
            intent, entities = self._detect_intent_rule_based(message_lower)
        
        # Route to appropriate handler
        if intent == 'check_availability':
            return self._handle_availability(entities)
        elif intent == 'book_room':
            return self._handle_booking(entities)
        elif intent == 'cancel_booking':
            return self._handle_cancellation(entities)
        elif intent == 'amenities':
            return self._handle_amenities(entities)
        elif intent == 'policies':
            return self._handle_policies(entities)
        elif intent == 'faq':
            return self._handle_faq(message)
        elif intent == 'greeting':
            return "Hello! Welcome to Hyatt House Charlotte Airport. I'm Sarah from the front desk. How can I assist you today?"
        else:
            return self._handle_general_inquiry(message)
    
    def _detect_intent_rule_based(self, message: str) -> Tuple[str, Dict]:
        """Simple rule-based intent detection"""
        entities = {}
        
        # Greeting
        if any(word in message for word in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
            return 'greeting', entities
        
        # Check if message is just a room type (for booking context)
        room_types = ['queen', 'king', 'suite', 'executive', 'accessible', 'standard', 'deluxe', 'family']
        if message in room_types or (len(message.split()) <= 3 and any(rt in message for rt in room_types)):
            for room_type in room_types:
                if room_type in message:
                    entities['room_type'] = room_type
            # If it's just a room type, assume they want to book
            return 'book_room', entities
        
        # Check if message looks like a name (2-3 words, capitalized, no special chars)
        words = message.split()
        if (2 <= len(words) <= 4 and 
            all(word.replace("'", "").isalpha() for word in words) and
            any(word[0].isupper() for word in words)):
            entities['guest_name'] = message.title()
            # Assume they're providing name for booking
            return 'book_room', entities
        
        # Check availability
        if any(phrase in message for phrase in ['available', 'availability', 'check room', 'any rooms', 'do you have']):
            # Extract room type if mentioned
            for room_type in room_types:
                if room_type in message:
                    entities['room_type'] = room_type
            
            # Extract dates if mentioned
            date_patterns = [
                r'(\d{1,2}[-/]\d{1,2})',  # MM/DD or MM-DD
                r'(oct|nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep)\s*\d{1,2}',  # Month DD
            ]
            for pattern in date_patterns:
                matches = re.findall(pattern, message)
                if matches:
                    entities['dates'] = matches
            
            return 'check_availability', entities
        
        # Booking
        if any(phrase in message for phrase in ['book', 'reserve', 'reservation', "i'd like to book", 'i want to book']):
            # Extract guest name
            name_match = re.search(r'(?:name is|i am|i\'m)\s+([a-zA-Z\s]+)', message)
            if name_match:
                entities['guest_name'] = name_match.group(1).strip()
            
            # Extract room type
            for room_type in room_types:
                if room_type in message:
                    entities['room_type'] = room_type
            
            return 'book_room', entities
        
        # Cancellation
        if any(phrase in message for phrase in ['cancel', 'cancellation', 'cancel my reservation', 'cancel booking']):
            # Extract booking ID
            booking_match = re.search(r'(?:booking|reservation|id)\s*#?\s*([A-Z0-9]+)', message)
            if booking_match:
                entities['booking_id'] = booking_match.group(1)
            
            return 'cancel_booking', entities
        
        # Amenities
        if any(phrase in message for phrase in ['amenities', 'facilities', 'pool', 'gym', 'fitness', 'parking', 
                                                 'wifi', 'breakfast', 'restaurant', 'what do you have']):
            # Extract specific amenity
            amenity_keywords = {
                'pool': 'pool',
                'gym': 'fitness_center',
                'fitness': 'fitness_center',
                'parking': 'parking',
                'wifi': 'wifi',
                'internet': 'wifi',
                'breakfast': 'breakfast',
                'restaurant': 'restaurant',
                'business': 'business_center',
                'concierge': 'concierge'
            }
            for keyword, amenity in amenity_keywords.items():
                if keyword in message:
                    entities['amenity'] = amenity
                    break
            
            return 'amenities', entities
        
        # Policies
        if any(phrase in message for phrase in ['policy', 'policies', 'check-in', 'checkout', 'check in', 
                                                 'check out', 'pet', 'smoking', 'payment', 'cancellation policy']):
            policy_keywords = {
                'check-in': 'check_in',
                'check in': 'check_in',
                'checkout': 'check_out',
                'check out': 'check_out',
                'pet': 'pets',
                'smoking': 'smoking',
                'payment': 'payment',
                'pay': 'payment',
                'cancel': 'cancellation'
            }
            for keyword, policy in policy_keywords.items():
                if keyword in message:
                    entities['policy'] = policy
                    break
            
            return 'policies', entities
        
        # FAQ
        if '?' in message:
            return 'faq', entities
        
        return 'general', entities
    
    def _detect_intent_llm(self, message: str, api_key: str) -> Tuple[str, Dict]:
        """Use LLM for more sophisticated intent detection"""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            prompt = f"""Analyze this hotel guest message and extract:
1. Intent: greeting, check_availability, book_room, cancel_booking, amenities, policies, faq, or general
2. Entities: guest_name, room_type, dates, booking_id, amenity, policy, etc.

Guest message: "{message}"

Respond in JSON format:
{{"intent": "...", "entities": {{...}}}}"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result.get('intent', 'general'), result.get('entities', {})
        except Exception as e:
            print(f"LLM intent detection failed: {e}, falling back to rule-based")
            return self._detect_intent_rule_based(message.lower())
    
    def _handle_availability(self, entities: Dict) -> str:
        """Handle room availability inquiries"""
        room_type = entities.get('room_type', '').lower()
        
        available_rooms = [r for r in self.data['rooms'] if r['available']]
        
        if room_type:
            # Filter by room type
            filtered_rooms = [r for r in available_rooms if room_type in r['type'].lower()]
        else:
            filtered_rooms = available_rooms
        
        if not filtered_rooms:
            return "I apologize, but we don't have any rooms available matching your criteria at the moment. Would you like me to check other room types?"
        
        response = "Here are our available rooms:\n\n"
        for room in filtered_rooms:
            response += f"**{room['type']}** (Room #{room['id']})\n"
            response += f"• {room['description']}\n"
            response += f"• Price: ${room['price_per_night']}/night\n"
            response += f"• Capacity: {room['capacity']} guests\n"
            response += f"• Amenities: {', '.join(room['amenities'])}\n\n"
        
        response += "Would you like to book any of these rooms?"
        return response
    
    def _handle_booking(self, entities: Dict) -> str:
        """Handle room booking requests"""
        guest_name = entities.get('guest_name')
        room_type = entities.get('room_type', '').lower()
        
        # If only room type provided, ask for name
        if room_type and not guest_name:
            # Check if room type is available first
            available_rooms = [r for r in self.data['rooms'] if r['available']]
            room = next((r for r in available_rooms if room_type in r['type'].lower()), None)
            
            if not room:
                return f"I apologize, but we don't have {room_type.title()} rooms available at the moment. Here are our available options:\n\n" + self._handle_availability({})
            
            # Store the pending room type in a way the next message can use
            return (
                f"**Excellent choice!** ✨\n\n"
                f"**Room:** {room['type']}\n"
                f"**Rate:** ${room['price_per_night']}/night\n"
                f"**Includes:** {', '.join(room['amenities'][:4])}\n\n"
                f"To complete your reservation, please provide your full name."
            )
        
        # If we have a name but no room type, try to find the last available room type from conversation
        if guest_name and not room_type:
            # Default to first available room for now
            available_rooms = [r for r in self.data['rooms'] if r['available']]
            room = available_rooms[0] if available_rooms else None
            
            if room:
                room_type = room['type'].lower()
            else:
                return "I apologize, but we don't have any rooms available at the moment."
        
        # If no name or room type, ask for details
        if not guest_name and not room_type:
            return "I'd be happy to help you book a room! Could you please provide your name and preferred room type?\n\nAvailable types:\n• Queen Guest Room ($139/night)\n• King Guest Room ($149/night)\n• 2 Queen Beds ($159/night)\n• Executive King ($189/night)\n• One-Bedroom Suite ($259/night)"
        
        # Find available room
        available_rooms = [r for r in self.data['rooms'] if r['available']]
        
        if room_type:
            room = next((r for r in available_rooms if room_type in r['type'].lower()), None)
        else:
            room = available_rooms[0] if available_rooms else None
        
        if not room:
            return "I apologize, but we don't have that room type available. Would you like to see our available rooms?"
        
        # Create booking
        booking_id = f"BK{len(self.data['bookings']) + 1:04d}"
        booking = {
            "booking_id": booking_id,
            "guest_name": guest_name,
            "room_id": room['id'],
            "room_type": room['type'],
            "price_per_night": room['price_per_night'],
            "check_in": entities.get('check_in', 'TBD'),
            "check_out": entities.get('check_out', 'TBD'),
            "created_at": datetime.now().isoformat()
        }
        
        # Update data
        self.data['bookings'].append(booking)
        room['available'] = False
        self.save_data()
        
        return (
            f"✅ Booking confirmed!\n\n"
            f"**Booking ID:** {booking_id}\n"
            f"**Guest:** {guest_name}\n"
            f"**Room:** {room['type']} (#{room['id']})\n"
            f"**Rate:** ${room['price_per_night']}/night\n\n"
            f"Please note your booking ID for future reference. "
            f"Is there anything else I can help you with?"
        )
    
    def _handle_cancellation(self, entities: Dict) -> str:
        """Handle booking cancellations"""
        booking_id = entities.get('booking_id')
        
        if not booking_id:
            # List all bookings
            if not self.data['bookings']:
                return "There are no active bookings in the system."
            
            response = "Here are the current bookings:\n\n"
            for booking in self.data['bookings']:
                response += f"• **{booking['booking_id']}** - {booking['guest_name']} - {booking['room_type']}\n"
            response += "\nPlease provide the booking ID you'd like to cancel."
            return response
        
        # Find and cancel booking
        booking = next((b for b in self.data['bookings'] if b['booking_id'] == booking_id), None)
        
        if not booking:
            return f"I couldn't find a booking with ID {booking_id}. Please check the booking ID and try again."
        
        # Remove booking and mark room as available
        self.data['bookings'].remove(booking)
        room = next((r for r in self.data['rooms'] if r['id'] == booking['room_id']), None)
        if room:
            room['available'] = True
        
        self.save_data()
        
        return (
            f"✅ Booking {booking_id} has been successfully cancelled.\n\n"
            f"Guest: {booking['guest_name']}\n"
            f"Room: {booking['room_type']}\n\n"
            f"As per our cancellation policy, please note that cancellations within 48 hours of arrival may incur charges. "
            f"Is there anything else I can help you with?"
        )
    
    def _handle_amenities(self, entities: Dict) -> str:
        """Handle amenity inquiries"""
        specific_amenity = entities.get('amenity')
        
        if specific_amenity and specific_amenity in self.data['amenities']:
            return self.data['amenities'][specific_amenity]
        
        response = "Here are our hotel amenities:\n\n"
        for amenity, description in self.data['amenities'].items():
            amenity_name = amenity.replace('_', ' ').title()
            response += f"**{amenity_name}:** {description}\n\n"
        
        return response
    
    def _handle_policies(self, entities: Dict) -> str:
        """Handle policy inquiries"""
        specific_policy = entities.get('policy')
        
        if specific_policy and specific_policy in self.data['policies']:
            policy_name = specific_policy.replace('_', ' ').title()
            return f"**{policy_name}:** {self.data['policies'][specific_policy]}"
        
        response = "Here are our hotel policies:\n\n"
        for policy, description in self.data['policies'].items():
            policy_name = policy.replace('_', ' ').title()
            response += f"**{policy_name}:** {description}\n\n"
        
        return response
    
    def _handle_faq(self, message: str) -> str:
        """Handle FAQ using simple text matching"""
        message_lower = message.lower()
        
        # Find best matching FAQ
        best_match = None
        best_score = 0
        
        for faq in self.data['faqs']:
            # Simple scoring based on word overlap
            question_words = set(faq['question'].lower().split())
            message_words = set(message_lower.split())
            overlap = len(question_words & message_words)
            
            if overlap > best_score:
                best_score = overlap
                best_match = faq
        
        if best_match and best_score >= 2:
            return best_match['answer']
        
        return self._handle_general_inquiry(message)
    
    def _handle_general_inquiry(self, message: str) -> str:
        """Handle general inquiries that don't match specific intents"""
        # Check if they're asking who we are or what hotel
        message_lower = message.lower()
        if any(word in message_lower for word in ['who are you', 'what are you', 'are you ai', 'are you a bot']):
            return (
                "I'm Sarah from the front desk here at Hyatt House Charlotte Airport. "
                "I'm here to help with reservations, questions about our hotel, or anything else you need!"
            )
        elif any(word in message_lower for word in ['which hotel', 'what hotel', 'where are you located', 'your location']):
            return (
                "This is Hyatt House Charlotte Airport, located at 4920 South Tryon Street, Charlotte, NC. "
                "We're just minutes from Charlotte Douglas International Airport. "
                "How can I help you today?"
            )
        else:
            return (
                "I'm here to help! I can assist you with:\n"
                "• Checking room availability at our hotel\n"
                "• Booking or cancelling reservations\n"
                "• Information about our amenities (pool, gym, parking, airport shuttle, etc.)\n"
                "• Hotel policies (check-in/out times, cancellation, pets, etc.)\n\n"
                "What would you like help with?"
            )


if __name__ == "__main__":
    # Simple CLI test
    agent = HotelAgent()
    print(agent.get_greeting())
    print("\nType 'quit' to exit\n")
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("Thank you for choosing Hyatt House Charlotte Airport! Have a great day!")
            break
        
        response = agent.process_message(user_input)
        print(f"\nAgent: {response}\n")


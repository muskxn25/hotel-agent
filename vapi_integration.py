"""
VAPI Integration for Hotel Front Desk Agent
Handles phone call interactions using VAPI's voice AI platform via REST API
"""

import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VAPIHotelAgent:
    """
    Manages voice call interactions for hotel front desk using VAPI REST API
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("VAPI_API_KEY")
        self.base_url = "https://api.vapi.ai"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.assistant_id = os.getenv("VAPI_ASSISTANT_ID")
        self.phone_number_id = os.getenv("VAPI_PHONE_NUMBER_ID")
        
    @property
    def client(self):
        """Check if API key is configured"""
        return self.api_key is not None
        
    def create_hotel_assistant(self) -> str:
        """
        Create a VAPI assistant configured for hotel front desk operations
        Returns the assistant ID
        """
        if not self.client:
            raise ValueError("VAPI API key not configured. Set VAPI_API_KEY")
        
        assistant_config = {
            "name": "Hyatt House Charlotte Airport Front Desk",
            "model": {
                "provider": "openai",
                "model": "gpt-4o-mini",  # Faster model for better performance
                "messages": [
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    }
                ],
                "temperature": 0.3,  # Lower temperature for more consistent responses
                "functions": self._get_functions(),
            },
            "voice": {
                "provider": "azure",
                "voiceId": "en-US-JennyNeural",
                "speed": 1.0,  # Normal speed
                "stability": 0.5,  # Balanced stability
                "clarity": 0.5  # Balanced clarity
            },
            "firstMessage": "Thank you for calling Hyatt House Charlotte Airport! This is Sarah from the front desk. May I have your name please?",
            "endCallMessage": "Thank you for calling Hyatt House Charlotte Airport! Have a wonderful day!",
            "endCallPhrases": ["goodbye", "bye", "that's all", "nothing else"],
            "clientMessages": ["function-call", "tool-calls"],
            "maxDurationSeconds": 300,  # 5 minute max call duration
            "silenceTimeoutSeconds": 2,  # Shorter silence timeout for faster responses
            "responseDelaySeconds": 0.5,  # Faster response delay
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/assistant",
                headers=self.headers,
                json=assistant_config,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('id', str(data))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to create assistant: {e}")
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the hotel assistant"""
        return """You are Sarah, a front desk agent at Hyatt House Charlotte Airport.

IDENTITY: You work at Hyatt House Charlotte Airport (4920 South Tryon Street, Charlotte, NC). Never say you're an AI.

CONVERSATION FLOW:
1. Greet: "Thank you for calling Hyatt House Charlotte Airport! This is Sarah from the front desk. May I have your name please?"
2. Get name, then ask: "How can I help you today?"
3. For room booking: Offer date options and ask for guest count
4. IMMEDIATELY call check_room_availability function when you have all three
5. Present available rooms and ask which they prefer

BOOKING PROCESS:
After getting their name and they want to book:
- Say: "Great! Let me help you with that. For your check-in date, we have availability starting from tomorrow. Would you prefer:
  * Tomorrow (November 28th)
  * This weekend (November 29th-30th) 
  * Next week (December 1st-7th)
  * Or do you have specific dates in mind?"
- Wait for their choice
- Then ask: "And for your check-out date, how many nights would you like to stay? We typically see guests staying 1-3 nights."
- Wait for their response
- Ask: "How many guests will be staying?"
- IMMEDIATELY call check_room_availability function when you have all three

CRITICAL RULES:
- You MUST call check_room_availability function as soon as you have: check-in date (YYYY-MM-DD), check-out date (YYYY-MM-DD), and guest count
- Do NOT continue conversation without calling this function
- Offer specific date options to make it easier for guests
- Use their name only 2-3 times max
- Be friendly but concise

HOTEL INFO:
- Address: 4920 South Tryon Street, Charlotte, NC
- Near Charlotte Douglas International Airport
- Check-in: 3:00 PM | Check-out: 12:00 PM
- Amenities: Free WiFi, fitness center, indoor pool, free parking, airport shuttle, breakfast"""

    def _get_functions(self) -> list:
        """Define function calls the assistant can make"""
        return [
            {
                "name": "check_room_availability",
                "description": "Return available room types and nightly rates for given dates and guest count at Hyatt House Charlotte Airport.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "check_in": {
                            "type": "string", 
                            "description": "Check-in date in YYYY-MM-DD format"
                        },
                        "check_out": {
                            "type": "string", 
                            "description": "Check-out date in YYYY-MM-DD format"
                        },
                        "guests": {
                            "type": "integer", 
                            "minimum": 1, 
                            "description": "Total number of guests"
                        }
                    },
                    "required": ["check_in", "check_out", "guests"]
                },
            },
            {
                "name": "create_booking",
                "description": "Create a new room reservation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "guest_name": {
                            "type": "string",
                            "description": "Full name of the guest",
                        },
                        "guest_phone": {
                            "type": "string",
                            "description": "Guest's phone number",
                        },
                        "guest_email": {
                            "type": "string",
                            "description": "Guest's email address",
                        },
                        "room_type": {
                            "type": "string",
                            "description": "Type of room to book",
                        },
                        "check_in": {
                            "type": "string",
                            "description": "Check-in date",
                        },
                        "check_out": {
                            "type": "string",
                            "description": "Check-out date",
                        },
                        "guests": {
                            "type": "integer",
                            "description": "Number of guests",
                        },
                        "special_requests": {
                            "type": "string",
                            "description": "Any special requests or notes",
                        },
                    },
                    "required": ["guest_name", "guest_phone", "room_type", "check_in", "check_out"],
                },
            },
            {
                "name": "cancel_booking",
                "description": "Cancel an existing reservation",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking confirmation number",
                        },
                        "guest_name": {
                            "type": "string",
                            "description": "Guest name for verification",
                        },
                    },
                    "required": ["booking_id"],
                },
            },
            {
                "name": "get_booking_details",
                "description": "Retrieve details of an existing booking",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "booking_id": {
                            "type": "string",
                            "description": "The booking confirmation number",
                        },
                    },
                    "required": ["booking_id"],
                },
            },
            {
                "name": "transfer_to_agent",
                "description": "Transfer call to a human agent for complex requests",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "reason": {
                            "type": "string",
                            "description": "Reason for transfer",
                        },
                    },
                    "required": ["reason"],
                },
            },
        ]
    
    def start_inbound_call(self, phone_number: str, metadata: Optional[Dict] = None) -> str:
        """
        Handle an inbound call from a guest
        Returns call ID
        """
        if not self.client or not self.assistant_id:
            raise ValueError("VAPI not configured properly. Need API key and assistant ID.")
        
        call_config = {
            "assistantId": self.assistant_id,
            "customer": {"number": phone_number},
            "assistantOverrides": {
                "variableValues": {
                    "caller_number": phone_number,
                    **(metadata or {}),
                }
            },
        }
        
        if self.phone_number_id:
            call_config["phoneNumberId"] = self.phone_number_id
        
        try:
            response = requests.post(
                f"{self.base_url}/call",
                headers=self.headers,
                json=call_config,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('id', str(data))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to start call: {e}")
    
    def start_outbound_call(
        self,
        to_number: str,
        guest_name: Optional[str] = None,
        purpose: str = "booking_confirmation",
        metadata: Optional[Dict] = None,
    ) -> str:
        """
        Make an outbound call to a guest (e.g., booking confirmations, reminders)
        
        Args:
            to_number: Phone number to call
            guest_name: Guest's name
            purpose: booking_confirmation, reminder, follow_up
            metadata: Additional context
        
        Returns:
            Call ID
        """
        if not self.client or not self.assistant_id or not self.phone_number_id:
            raise ValueError("VAPI not configured for outbound calls. Need API key, assistant ID, and phone number ID.")
        
        # Customize first message based on purpose
        first_messages = {
            "booking_confirmation": f"Hello{' ' + guest_name if guest_name else ''}! This is Sarah calling from Grand Plaza Hotel to confirm your reservation.",
            "reminder": f"Hello{' ' + guest_name if guest_name else ''}! This is a friendly reminder about your upcoming stay at Grand Plaza Hotel.",
            "follow_up": f"Hello{' ' + guest_name if guest_name else ''}! This is Sarah from Grand Plaza Hotel. I'm calling to follow up on your recent stay.",
        }
        
        call_config = {
            "assistantId": self.assistant_id,
            "phoneNumberId": self.phone_number_id,
            "customer": {"number": to_number},
            "assistantOverrides": {
                "firstMessage": first_messages.get(purpose, first_messages["booking_confirmation"]),
                "variableValues": {
                    "guest_name": guest_name or "valued guest",
                    "purpose": purpose,
                    **(metadata or {}),
                },
            },
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/call",
                headers=self.headers,
                json=call_config,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            return data.get('id', str(data))
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to start outbound call: {e}")
    
    def get_call_status(self, call_id: str) -> Dict:
        """Get status and details of a call"""
        if not self.client:
            raise ValueError("VAPI API key not configured")
        
        try:
            response = requests.get(
                f"{self.base_url}/call/{call_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to get call status: {e}")
    
    def end_call(self, call_id: str) -> bool:
        """End an ongoing call"""
        if not self.client:
            raise ValueError("VAPI API key not configured")
        
        try:
            # Use VAPI's API to end the call
            response = requests.post(
                f"{self.base_url}/call/{call_id}/end",
                headers=self.headers,
                timeout=30
            )
            return response.ok
        except Exception as e:
            print(f"Error ending call: {e}")
            return False


# Singleton instance
vapi_agent = None

def get_vapi_agent() -> VAPIHotelAgent:
    """Get or create VAPI agent instance"""
    global vapi_agent
    if vapi_agent is None:
        vapi_agent = VAPIHotelAgent()
    return vapi_agent


"""
Flask API Server for Hotel Front Desk Agent
Provides REST API and serves web interface
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from hotel_agent import HotelAgent
from vapi_integration import get_vapi_agent
from amadeus_integration import get_amadeus_api
import os
import uuid
from datetime import datetime, timedelta
import re
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_natural_date(date_str):
    """
    Parse natural language dates like:
    - "2nd november" -> "2024-11-02"
    - "nov 5th" -> "2024-11-05" 
    - "november 2" -> "2024-11-02"
    - "5th nov" -> "2024-11-05"
    """
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    current_year = datetime.now().year
    
    # Month mapping
    months = {
        'jan': '01', 'january': '01',
        'feb': '02', 'february': '02', 
        'mar': '03', 'march': '03',
        'apr': '04', 'april': '04',
        'may': '05',
        'jun': '06', 'june': '06',
        'jul': '07', 'july': '07',
        'aug': '08', 'august': '08',
        'sep': '09', 'september': '09',
        'oct': '10', 'october': '10',
        'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }
    
    # Patterns to match
    patterns = [
        # "2nd november", "5th nov", "1st jan"
        r'(\d+)(?:st|nd|rd|th)?\s+(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)',
        # "november 2", "nov 5"
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d+)',
        # "nov 2nd", "jan 5th"
        r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d+)(?:st|nd|rd|th)?'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                if groups[0].isdigit():
                    # Format: "2nd november"
                    day = groups[0]
                    month_name = groups[1]
                else:
                    # Format: "november 2" or "nov 2nd"
                    month_name = groups[0]
                    day = groups[1]
                
                if month_name in months:
                    month_num = months[month_name]
                    try:
                        day_num = int(day)
                        if 1 <= day_num <= 31:
                            return f"{current_year}-{month_num}-{day_num:02d}"
                    except ValueError:
                        continue
    
    return None

def parse_date_range(date_range_str):
    """
    Parse date ranges like:
    - "2nd november till 5th nov" -> ("2024-11-02", "2024-11-05")
    - "nov 2 to nov 5" -> ("2024-11-02", "2024-11-05")
    """
    if not date_range_str:
        return None, None
        
    date_range_str = date_range_str.lower().strip()
    
    # Split by common separators
    separators = [' till ', ' to ', ' - ', ' through ', ' until ']
    for sep in separators:
        if sep in date_range_str:
            parts = date_range_str.split(sep)
            if len(parts) == 2:
                start_date = parse_natural_date(parts[0].strip())
                end_date = parse_natural_date(parts[1].strip())
                return start_date, end_date
    
    # Try to parse as single date
    single_date = parse_natural_date(date_range_str)
    if single_date:
        return single_date, None
    
    return None, None

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Initialize agent
agent = HotelAgent()

# Session storage for active calls and conversations
call_sessions = {}
conversation_sessions = {}  # Store conversation context

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')

@app.route('/api/greeting', methods=['GET'])
def greeting():
    """Get greeting message"""
    return jsonify({
        'success': True,
        'message': agent.get_greeting()
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process chat message"""
    data = request.json
    message = data.get('message', '')
    use_llm = data.get('use_llm', False)
    api_key = data.get('api_key')
    session_id = data.get('session_id', 'default')
    
    if not message:
        return jsonify({
            'success': False,
            'error': 'Message is required'
        }), 400
    
    try:
        # Get or create session context
        if session_id not in conversation_sessions:
            conversation_sessions[session_id] = {
                'step': None,
                'booking_data': {}
            }
        
        session = conversation_sessions[session_id]
        message_lower = message.lower().strip()
        
        # Debug logging
        print(f"[DEBUG] Session step: {session['step']}, Message: {message_lower[:50]}")
        
        # Multi-step availability check flow
        if session['step'] == 'awaiting_availability_dates':
            # Parse dates from message
            import re
            from datetime import datetime as dt
            
            # Extract dates (simple patterns)
            dates = re.findall(r'(?:oct|nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep)[a-z]*\s*\d{1,2}', message_lower)
            
            # Calculate nights if we have dates
            nights = len(dates) if len(dates) > 1 else None
            if not nights and re.search(r'(\d+)\s*(?:night|day)', message_lower):
                night_match = re.search(r'(\d+)\s*(?:night|day)', message_lower)
                nights = int(night_match.group(1))
            
            # Try to extract actual date patterns like "Oct 14 to Oct 18" or "from ... to ..."
            check_in_str = None
            check_out_str = None
            
            if dates and len(dates) >= 2:
                check_in_str = dates[0]
                check_out_str = dates[1]
            elif dates and len(dates) == 1 and nights:
                check_in_str = dates[0]
            
            # If we don't have clear dates, ask for clarification
            if not check_in_str:
                return jsonify({
                    'success': True,
                    'message': "Please provide your check-in and check-out dates.\n\nFor example: \"Oct 15 to Oct 18\" or \"October 15 for 3 nights\""
                })
            
            # Convert to proper date format
            current_year = datetime.now().year
            
            # Parse check-in date
            try:
                check_in_dt = dt.strptime(f"{check_in_str} {current_year}", '%b %d %Y')
                check_in_date = check_in_dt.strftime('%Y-%m-%d')
            except:
                # Default to tomorrow if parsing fails
                tomorrow = datetime.now() + timedelta(days=1)
                check_in_date = tomorrow.strftime('%Y-%m-%d')
                check_in_dt = tomorrow
            
            # Calculate nights and check-out date
            if not nights:
                nights = 1
            
            check_out_dt = check_in_dt + timedelta(days=nights)
            check_out_date = check_out_dt.strftime('%Y-%m-%d')
            
            # Try to fetch from Amadeus API first
            amadeus = get_amadeus_api()
            available_rooms = []
            num_guests = 2  # Default for availability check
            
            if amadeus.is_configured():
                try:
                    print(f"Checking availability via Amadeus API: {check_in_date} to {check_out_date}")
                    available_rooms = amadeus.search_charlotte_airport_hotels(
                        check_in_date, check_out_date, num_guests
                    )
                except Exception as e:
                    print(f"Amadeus API error: {e}")
            
            # Fallback to static data
            if not available_rooms:
                # For demo purposes, show ALL rooms regardless of availability status
                available_rooms = agent.data['rooms'][:8]  # Show first 8 rooms as demo
            
            if not available_rooms:
                return jsonify({
                    'success': True,
                    'message': "I apologize, but we don't have any rooms available for those dates. Would you like to check different dates?"
                })
            
            response = f"**Available Rooms** for {check_in_str} to {check_out_str}:\n\n"
            
            for room in available_rooms[:5]:
                total_price = room['price_per_night'] * nights
                hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
                response += f"**{room['type']}**"
                if room.get('source') == 'amadeus':
                    response += f" at {hotel_name}\n"
                else:
                    response += f" (Room #{room['id']})\n"
                response += f"• Capacity: {room['capacity']} guests\n"
                response += f"• ${room['price_per_night']:.2f}/night × {nights} nights = **${total_price:.2f} total**\n"
                response += f"• Amenities: {', '.join(room['amenities'][:4])}\n\n"
            
            response += "\nWould you like to book any of these rooms? Reply 'book' or select option 2 to start a reservation."
            
            # Clear the step
            session['step'] = None
            
            return jsonify({'success': True, 'message': response})
        
        # Multi-step booking flow
        if session['step'] == 'awaiting_guests_dates':
            # Parse guests and dates from message
            import re
            
            # Extract number of guests
            guest_match = re.search(r'(\d+)\s*(?:guest|people|person)', message_lower)
            if not guest_match:
                guest_match = re.search(r'^(\d+)', message_lower)
            
            num_guests = int(guest_match.group(1)) if guest_match else None
            
            # Extract dates (simple patterns)
            dates = re.findall(r'(?:oct|nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep)[a-z]*\s*\d{1,2}', message_lower)
            
            # Calculate nights if we have dates
            nights = len(dates) if len(dates) > 1 else None
            if not nights and re.search(r'(\d+)\s*(?:night|day)', message_lower):
                night_match = re.search(r'(\d+)\s*(?:night|day)', message_lower)
                nights = int(night_match.group(1))
            
            if not num_guests:
                return jsonify({
                    'success': True,
                    'message': "How many guests will be staying? Please provide the number of guests."
                })
            
            if not nights:
                nights = 1  # Default to 1 night
            
            # Store in session
            session['booking_data']['guests'] = num_guests
            session['booking_data']['nights'] = nights
            session['booking_data']['check_in'] = dates[0] if dates else "TBD"
            session['booking_data']['check_out'] = dates[1] if len(dates) > 1 else "TBD"
            
            # Calculate proper dates for Amadeus API
            check_in_date = session['booking_data']['check_in']
            check_out_date = session['booking_data']['check_out']
            
            # Convert date strings like "oct 25" to YYYY-MM-DD format
            from datetime import datetime as dt
            
            if check_in_date != "TBD" and not check_in_date.count('-') == 2:
                # Parse dates like "oct 25" or "october 25"
                try:
                    # Add current year
                    current_year = datetime.now().year
                    check_in_dt = dt.strptime(f"{check_in_date} {current_year}", '%b %d %Y')
                    check_in_date = check_in_dt.strftime('%Y-%m-%d')
                    session['booking_data']['check_in'] = check_in_date
                except:
                    # If parsing fails, default to tomorrow
                    tomorrow = datetime.now() + timedelta(days=1)
                    check_in_date = tomorrow.strftime('%Y-%m-%d')
                    session['booking_data']['check_in'] = check_in_date
            elif check_in_date == "TBD":
                # Set to tomorrow
                tomorrow = datetime.now() + timedelta(days=1)
                check_in_date = tomorrow.strftime('%Y-%m-%d')
                session['booking_data']['check_in'] = check_in_date
            
            # Always calculate check-out based on check-in + nights
            check_in_dt = dt.strptime(check_in_date, '%Y-%m-%d')
            checkout_dt = check_in_dt + timedelta(days=nights)
            check_out_date = checkout_dt.strftime('%Y-%m-%d')
            session['booking_data']['check_out'] = check_out_date
            
            # Try to fetch from Amadeus API first
            amadeus = get_amadeus_api()
            available_rooms = []
            
            if amadeus.is_configured():
                try:
                    print(f"Fetching hotels from Amadeus API for {num_guests} guests, {check_in_date} to {check_out_date}")
                    available_rooms = amadeus.search_charlotte_airport_hotels(
                        check_in_date, check_out_date, num_guests
                    )
                    session['booking_data']['using_amadeus'] = True
                    print(f"Found {len(available_rooms)} rooms from Amadeus")
                except Exception as e:
                    print(f"Amadeus API error: {e}")
            
            # Fallback to static data if Amadeus fails or not configured
            if not available_rooms:
                # For demo purposes, show ALL rooms regardless of availability status
                available_rooms = [r for r in agent.data['rooms'] if r['capacity'] >= num_guests]
                # If still no rooms, show all rooms
                if not available_rooms:
                    available_rooms = agent.data['rooms'][:5]  # Show first 5 rooms as demo
                session['booking_data']['using_amadeus'] = False
                print(f"Using static data (demo mode): {len(available_rooms)} rooms")
            
            if not available_rooms:
                return jsonify({
                    'success': True,
                    'message': f"I apologize, but we don't have rooms available for {num_guests} guests. Would you like to see all our available rooms?"
                })
            
            response = f"Perfect! For **{num_guests} guest(s)** staying **{nights} night(s)**, here are your options:\n\n"
            
            for room in available_rooms[:5]:  # Show top 5
                total_price = room['price_per_night'] * nights
                hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
                response += f"**{room['type']}**"
                if room.get('source') == 'amadeus':
                    response += f" at {hotel_name}\n"
                else:
                    response += f" (Room #{room['id']})\n"
                response += f"• Capacity: {room['capacity']} guests\n"
                response += f"• ${room['price_per_night']:.2f}/night × {nights} nights = **${total_price:.2f} total**\n"
                response += f"• Amenities: {', '.join(room['amenities'][:4])}\n\n"
            
            response += "Which room would you like? (Type the room type, e.g., 'Queen Guest Room' or 'King')"
            
            # Store available rooms for later selection
            session['booking_data']['available_rooms'] = available_rooms
            session['step'] = 'awaiting_room_selection'
            
            return jsonify({'success': True, 'message': response})
        
        elif session['step'] == 'awaiting_room_selection':
            # Check if user is updating nights/dates or guest count
            import re
            night_match = re.search(r'(\d+)\s*(?:night|day)', message_lower)
            guest_match = re.search(r'(\d+)\s*(?:guest|people|person)', message_lower)
            
            # Track if anything was updated
            updated = False
            num_guests = session['booking_data'].get('guests', 1)
            nights = session['booking_data'].get('nights', 1)
            
            if night_match:
                # User wants to update nights
                nights = int(night_match.group(1))
                session['booking_data']['nights'] = nights
                updated = True
            
            if guest_match:
                # User wants to update guest count
                num_guests = int(guest_match.group(1))
                session['booking_data']['guests'] = num_guests
                updated = True
            
            if updated:
                # Calculate dates for Amadeus API
                check_in_date = session['booking_data'].get('check_in')
                check_out_date = session['booking_data'].get('check_out')
                
                # If check-in date is TBD, set it to tomorrow
                if check_in_date == "TBD" or not check_in_date:
                    tomorrow = datetime.now() + timedelta(days=1)
                    check_in_date = tomorrow.strftime('%Y-%m-%d')
                    session['booking_data']['check_in'] = check_in_date
                
                # Always recalculate check-out based on check-in + nights
                from datetime import datetime as dt
                check_in_dt = dt.strptime(check_in_date, '%Y-%m-%d')
                checkout_dt = check_in_dt + timedelta(days=nights)
                check_out_date = checkout_dt.strftime('%Y-%m-%d')
                session['booking_data']['check_out'] = check_out_date
                
                # Try to fetch from Amadeus API first
                amadeus = get_amadeus_api()
                available_rooms = []
                
                if amadeus.is_configured():
                    try:
                        available_rooms = amadeus.search_charlotte_airport_hotels(
                            check_in_date, check_out_date, num_guests
                        )
                        # Store that we're using Amadeus data
                        session['booking_data']['using_amadeus'] = True
                    except Exception as e:
                        print(f"Amadeus API error: {e}")
                
                # Fallback to static data if Amadeus fails or not configured
                if not available_rooms:
                    # For demo purposes, show ALL rooms regardless of availability status
                    available_rooms = [r for r in agent.data['rooms'] if r['capacity'] >= num_guests]
                    # If still no rooms, show all rooms
                    if not available_rooms:
                        available_rooms = agent.data['rooms'][:5]  # Show first 5 rooms as demo
                    session['booking_data']['using_amadeus'] = False
                
                if not available_rooms:
                    return jsonify({
                        'success': True,
                        'message': f"I apologize, but we don't have rooms available for {num_guests} guests. Would you like to see all our available rooms?"
                    })
                
                response = f"Perfect! Updated to **{num_guests} guest(s)** for **{nights} night(s)**. Here are your options:\n\n"
                
                for room in available_rooms[:5]:  # Show top 5
                    total_price = room['price_per_night'] * nights
                    hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
                    response += f"**{room['type']}**"
                    if room.get('source') == 'amadeus':
                        response += f" at {hotel_name}\n"
                    else:
                        response += f" (Room #{room['id']})\n"
                    response += f"• Capacity: {room['capacity']} guests\n"
                    response += f"• ${room['price_per_night']:.2f}/night × {nights} nights = **${total_price:.2f} total**\n"
                    response += f"• Amenities: {', '.join(room['amenities'][:4])}\n\n"
                
                response += "Which room would you like? (Type the room type, e.g., 'Queen Guest Room' or 'King')"
                
                # Store the available rooms for selection
                session['booking_data']['available_rooms'] = available_rooms
                
                return jsonify({'success': True, 'message': response})
            
            # User selected a room type
            room_types = ['queen', 'king', 'suite', 'executive', 'accessible', 'standard', 'deluxe']
            selected_type = None
            for rt in room_types:
                if rt in message_lower:
                    selected_type = rt
                    break
            
            if not selected_type:
                return jsonify({
                    'success': True,
                    'message': "Please select a room type from the options above (e.g., Queen, King, Suite)."
                })
            
            # Get the stored available rooms (might be from Amadeus or static data)
            available_rooms = session['booking_data'].get('available_rooms', [])
            
            # If not stored, fall back to static data  
            if not available_rooms:
                available_rooms = agent.data['rooms'][:5]  # Demo mode - show rooms
            
            # Find the room matching the selected type
            room = next((r for r in available_rooms if selected_type in r['type'].lower()), None)
            
            if not room:
                return jsonify({
                    'success': True,
                    'message': "That room is no longer available. Please choose another option from above."
                })
            
            session['booking_data']['room'] = room
            
            nights = session['booking_data'].get('nights', 1)
            total = room['price_per_night'] * nights
            hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
            is_amadeus = room.get('source') == 'amadeus'
            
            response = f"✨ **Excellent choice!**\n\n"
            
            if is_amadeus:
                response += f"**Hotel:** {hotel_name}\n"
            
            response += (
                f"**Room:** {room['type']}\n"
            )
            
            if not is_amadeus:
                response += f"**Room Number:** {room['id']}\n"
            
            response += (
                f"**Nightly Rate:** ${room['price_per_night']:.2f}\n"
                f"**Total Cost:** ${total:.2f} for {nights} night(s)\n\n"
                f"**Room Features:**\n"
            )
            
            for amenity in room['amenities']:
                response += f"✓ {amenity}\n"
            
            response += f"\n**Next step:** Please provide your contact details:"
            
            session['step'] = 'awaiting_contact_details'
            
            return jsonify({'success': True, 'message': response})
        
        elif session['step'] == 'awaiting_contact_details':
            # Parse contact details and payment info
            # Format: "Name, Phone, Email (optional), Requests (optional), Payment: Name ****1234"
            import re
            
            # Extract name (first part before first comma)
            parts = message.split(',', 1)
            guest_name = parts[0].strip() if parts else None
            remaining = parts[1] if len(parts) > 1 else ''
            
            # Extract phone (various formats)
            phone_match = re.search(r'[\+\d][\d\s\-\(\)]{8,}', message)
            phone = phone_match.group(0).strip() if phone_match else None
            
            # Extract email
            email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', message)
            email = email_match.group(0) if email_match else None
            
            # Extract payment info (masked card)
            payment_match = re.search(r'Payment:\s*(.+?)\s*\*\*\*\*(\d{4})', message)
            payment_name = payment_match.group(1).strip() if payment_match else None
            card_last4 = payment_match.group(2) if payment_match else None
            
            # Extract special requests (everything between phone/email and payment, or just after email if no payment)
            special_requests = message
            if guest_name:
                special_requests = special_requests.replace(guest_name, '', 1)
            if email:
                special_requests = special_requests.replace(email, '')
            if phone:
                special_requests = special_requests.replace(phone, '')
            if payment_match:
                special_requests = special_requests.replace(payment_match.group(0), '')
            special_requests = special_requests.replace(',', '').strip()
            
            if not guest_name or not phone:
                return jsonify({
                    'success': True,
                    'message': "Please provide your name and phone number to continue with your reservation."
                })
            
            # Store all details including name
            session['booking_data']['guest_name'] = guest_name
            session['booking_data']['email'] = email if email else 'Not provided'
            session['booking_data']['phone'] = phone
            session['booking_data']['special_requests'] = special_requests if special_requests else 'None'
            session['booking_data']['payment_method'] = f"{payment_name} ****{card_last4}" if payment_name and card_last4 else 'Not provided'
            
            # Now complete the booking directly (skip awaiting_name step)
            booking_data = session['booking_data']
            room = booking_data['room']
            nights = booking_data.get('nights', 1)
            total_cost = room['price_per_night'] * nights
            
            # Create booking
            booking_id = f"BK{len(agent.data['bookings']) + 1:04d}"
            is_amadeus = room.get('source') == 'amadeus'
            hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
            
            booking = {
                "booking_id": booking_id,
                "guest_name": guest_name,
                "guest_email": email if email else 'Not provided',
                "guest_phone": phone,
                "special_requests": special_requests if special_requests else 'None',
                "payment_method": f"{payment_name} ****{card_last4}" if payment_name and card_last4 else 'Not provided',
                "room_id": room.get('id', 'TBD'),
                "room_type": room['type'],
                "hotel_name": hotel_name,
                "price_per_night": room['price_per_night'],
                "nights": nights,
                "total_cost": total_cost,
                "num_guests": booking_data.get('guests', 1),
                "check_in": booking_data.get('check_in', 'TBD'),
                "check_out": booking_data.get('check_out', 'TBD'),
                "created_at": datetime.now().isoformat(),
                "source": "amadeus" if is_amadeus else "web_chat"
            }
            
            agent.data['bookings'].append(booking)
            
            # Only mark as unavailable if it's static data (not Amadeus)
            if not is_amadeus and 'available' in room:
                room['available'] = False
            
            agent.save_data()
            
            # Clear session
            session['step'] = None
            session['booking_data'] = {}
            
            response = f"✅ **RESERVATION CONFIRMED!**\n\n"
            response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"**Confirmation #:** {booking_id}\n"
            response += f"**Guest:** {guest_name}\n"
            
            if is_amadeus:
                response += f"**Hotel:** {hotel_name}\n"
            
            response += f"**Room:** {room['type']}\n"
            
            if not is_amadeus and room.get('id'):
                response += f"**Room #:** {room['id']}\n"
            
            response += (
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                f"**Guest Information:**\n"
                f"• Phone: {phone}\n"
            )
            
            if email:
                response += f"• Email: {email}\n"
            
            if payment_name and card_last4:
                response += f"• Payment: {payment_name} ending in {card_last4}\n"
            
            if special_requests:
                response += f"• Special Requests: {special_requests}\n"
            
            response += (
                f"\n**Reservation Details:**\n"
                f"• Guests: {booking_data.get('guests', 1)}\n"
                f"• Check-in: {booking_data.get('check_in', 'TBD')}\n"
                f"• Check-out: {booking_data.get('check_out', 'TBD')}\n"
                f"• Nights: {nights}\n"
                f"• Rate: ${room['price_per_night']:.2f}/night\n"
                f"• **Total: ${total_cost:.2f}**\n\n"
                f"**Included Amenities:**\n"
            )
            
            for amenity in room['amenities']:
                response += f"✓ {amenity}\n"
            
            response += (
                f"\n**Important Information:**\n"
                f"• Check-in time: 3:00 PM\n"
                f"• Check-out time: 12:00 PM\n"
                f"• Free 24/7 airport shuttle to CLT\n"
                f"• Free parking & WiFi included\n"
                f"• Cancellation: Free up to 48 hours before arrival\n\n"
            )
            
            if email:
                response += f"📧 A confirmation email has been sent to **{email}**\n\n"
            else:
                response += f"📱 A confirmation SMS will be sent to **{phone}**\n\n"
            
            response += f"Thank you for choosing Hilton Charlotte Airport! Anything else I can help with?"
            
            return jsonify({'success': True, 'message': response})
        
        elif session['step'] == 'awaiting_name':
            # Complete the booking
            words = message.split()
            if len(words) >= 1 and all(word.replace("'", "").replace("-", "").isalpha() for word in words):
                guest_name = message.title()
                booking_data = session['booking_data']
                room = booking_data['room']
                nights = booking_data.get('nights', 1)
                total_cost = room['price_per_night'] * nights
                
                # Create booking
                booking_id = f"BK{len(agent.data['bookings']) + 1:04d}"
                is_amadeus = room.get('source') == 'amadeus'
                hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
                
                booking = {
                    "booking_id": booking_id,
                    "guest_name": guest_name,
                    "guest_email": booking_data.get('email', 'Not provided'),
                    "guest_phone": booking_data.get('phone', 'Not provided'),
                    "special_requests": booking_data.get('special_requests', 'None'),
                    "payment_method": booking_data.get('payment_method', 'Not provided'),
                    "room_id": room.get('id', 'TBD'),
                    "room_type": room['type'],
                    "hotel_name": hotel_name,
                    "price_per_night": room['price_per_night'],
                    "nights": nights,
                    "total_cost": total_cost,
                    "num_guests": booking_data.get('guests', 1),
                    "check_in": booking_data.get('check_in', 'TBD'),
                    "check_out": booking_data.get('check_out', 'TBD'),
                    "created_at": datetime.now().isoformat(),
                    "source": "amadeus" if is_amadeus else "web_chat"
                }
                
                agent.data['bookings'].append(booking)
                
                # Only mark as unavailable if it's static data (not Amadeus)
                if not is_amadeus:
                    if 'available' in room:
                        room['available'] = False
                
                agent.save_data()
                
                # Clear session
                session['step'] = None
                session['booking_data'] = {}
                
                response = f"✅ **RESERVATION CONFIRMED!**\n\n"
                response += f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                response += f"**Confirmation #:** {booking_id}\n"
                response += f"**Guest:** {guest_name}\n"
                
                if is_amadeus:
                    response += f"**Hotel:** {hotel_name}\n"
                
                response += f"**Room:** {room['type']}\n"
                
                if not is_amadeus and room.get('id'):
                    response += f"**Room #:** {room['id']}\n"
                
                response += (
                    f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                    f"**Guest Information:**\n"
                    f"• Email: {booking_data.get('email', 'Not provided')}\n"
                    f"• Phone: {booking_data.get('phone', 'Not provided')}\n"
                )
                
                if booking_data.get('payment_method') and booking_data.get('payment_method') != 'Not provided':
                    response += f"• Payment: {booking_data.get('payment_method')}\n"
                
                if booking_data.get('special_requests') and booking_data.get('special_requests') != 'None':
                    response += f"• Special Requests: {booking_data.get('special_requests')}\n"
                
                response += (
                    f"\n**Reservation Details:**\n"
                    f"• Guests: {booking_data.get('guests', 1)}\n"
                    f"• Check-in: {booking_data.get('check_in', 'TBD')}\n"
                    f"• Check-out: {booking_data.get('check_out', 'TBD')}\n"
                    f"• Nights: {nights}\n"
                    f"• Rate: ${room['price_per_night']:.2f}/night\n"
                    f"• **Total: ${total_cost:.2f}**\n\n"
                    f"**Included Amenities:**\n"
                )
                
                for amenity in room['amenities']:
                    response += f"✓ {amenity}\n"
                
                response += (
                    f"\n**Important Information:**\n"
                    f"• Check-in time: 3:00 PM\n"
                    f"• Check-out time: 12:00 PM\n"
                    f"• Free 24/7 airport shuttle to CLT\n"
                    f"• Free parking & WiFi included\n"
                    f"• Cancellation: Free up to 48 hours before arrival\n\n"
                    f"📧 A confirmation email has been sent to **{booking_data.get('email', 'your email')}**\n\n"
                    f"Thank you for choosing Hilton Charlotte Airport! Anything else I can help with?"
                )
                
                return jsonify({'success': True, 'message': response})
        
        # Handle menu option 1 - Check room availability
        if message_lower in ['1', 'option 1', '1.', 'check rooms', 'check availability', 'availability']:
            session['step'] = 'awaiting_availability_dates'
            return jsonify({
                'success': True,
                'message': "I'd be happy to check room availability for you! 🏨\n\n**What dates would you like to check?**\n\nPlease provide your check-in and check-out dates.\n\nFor example:\n• \"Oct 15 to Oct 18\"\n• \"October 20 for 3 nights\"\n• \"Nov 1 to Nov 5\""
            })
        
        # Handle direct booking requests with dates (from booking widget)
        import re
        # Check if message has guests + dates (from booking widget format: "X guests, Month Day to Month Day")
        has_guests = re.search(r'\d+\s*(?:guest|people|person)', message_lower)
        has_dates = re.search(r'(?:oct|nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep)[a-z]*\s*\d{1,2}', message_lower)
        
        if has_guests and has_dates and session['step'] is None:
            # This is a direct booking request from the widget, process it immediately
            session['step'] = 'awaiting_guests_dates'
            # Now the next section will process it
            # Re-route to the booking flow handler by jumping back
            # We'll fall through and let the awaiting_guests_dates handler process it
        
        # Check if we need to process as booking (after setting step above)
        if session['step'] == 'awaiting_guests_dates' and has_guests and has_dates:
            # Parse the message same as the booking flow
            guest_match = re.search(r'(\d+)\s*(?:guest|people|person)', message_lower)
            num_guests = int(guest_match.group(1)) if guest_match else 2
            
            # Extract dates
            dates = re.findall(r'(?:oct|nov|dec|jan|feb|mar|apr|may|jun|jul|aug|sep)[a-z]*\s*\d{1,2}', message_lower)
            
            # Calculate nights
            nights = 1
            if len(dates) >= 2:
                nights = 1  # Default, could calculate from dates
            night_match = re.search(r'(\d+)\s*(?:night|day)', message_lower)
            if night_match:
                nights = int(night_match.group(1))
            
            # Store in session
            session['booking_data']['guests'] = num_guests
            session['booking_data']['nights'] = nights
            session['booking_data']['check_in'] = dates[0] if dates else "TBD"
            session['booking_data']['check_out'] = dates[1] if len(dates) > 1 else "TBD"
            
            # Calculate proper dates
            tomorrow = datetime.now() + timedelta(days=1)
            check_in_date = tomorrow.strftime('%Y-%m-%d')
            check_out_date = (tomorrow + timedelta(days=nights)).strftime('%Y-%m-%d')
            session['booking_data']['check_in'] = check_in_date
            session['booking_data']['check_out'] = check_out_date
            
            # Try Amadeus
            amadeus = get_amadeus_api()
            available_rooms = []
            
            if amadeus.is_configured():
                try:
                    print(f"Fetching hotels from Amadeus API for {num_guests} guests, {check_in_date} to {check_out_date}")
                    available_rooms = amadeus.search_charlotte_airport_hotels(check_in_date, check_out_date, num_guests)
                    session['booking_data']['using_amadeus'] = True
                    print(f"Found {len(available_rooms)} rooms from Amadeus")
                except Exception as e:
                    print(f"Amadeus API error: {e}")
            
            # Fallback to static data
            if not available_rooms:
                available_rooms = [r for r in agent.data['rooms'] if r['capacity'] >= num_guests]
                if not available_rooms:
                    available_rooms = agent.data['rooms'][:5]
                session['booking_data']['using_amadeus'] = False
                print(f"Using static data (demo mode): {len(available_rooms)} rooms")
            
            response = f"Perfect! For **{num_guests} guest(s)** staying **{nights} night(s)**, here are your options:\n\n"
            
            for room in available_rooms[:5]:
                total_price = room['price_per_night'] * nights
                hotel_name = room.get('hotel_name', 'Hilton Charlotte Airport')
                response += f"**{room['type']}**"
                if room.get('source') == 'amadeus':
                    response += f" at {hotel_name}\n"
                else:
                    response += f" (Room #{room['id']})\n"
                response += f"• Capacity: {room['capacity']} guests\n"
                response += f"• ${room['price_per_night']:.2f}/night × {nights} nights = **${total_price:.2f} total**\n"
                response += f"• Amenities: {', '.join(room['amenities'][:4])}\n\n"
            
            response += "Which room would you like? (Type the room type, e.g., 'Queen Guest Room' or 'King')"
            
            session['booking_data']['available_rooms'] = available_rooms
            session['step'] = 'awaiting_room_selection'
            
            return jsonify({'success': True, 'message': response})
        
        # Process message normally
        response = agent.process_message(message, use_llm=use_llm, llm_api_key=api_key)
        
        # Update session context based on response
        if "how many guests will be staying" in response.lower():
            session['step'] = 'awaiting_guests_dates'
        elif "provide your full name" in response.lower():
            session['step'] = 'awaiting_name'
            # Extract room type from the response
            for room in agent.data['rooms']:
                if room['type'] in response:
                    session['booking_data']['room'] = room
                    break
        
        return jsonify({
            'success': True,
            'message': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/rooms', methods=['GET'])
def get_rooms():
    """Get all rooms"""
    return jsonify({
        'success': True,
        'rooms': agent.data['rooms']
    })

@app.route('/api/bookings', methods=['GET'])
def get_bookings():
    """Get all bookings"""
    return jsonify({
        'success': True,
        'bookings': agent.data['bookings']
    })

@app.route('/api/amenities', methods=['GET'])
def get_amenities():
    """Get all amenities"""
    return jsonify({
        'success': True,
        'amenities': agent.data['amenities']
    })

@app.route('/api/policies', methods=['GET'])
def get_policies():
    """Get all policies"""
    return jsonify({
        'success': True,
        'policies': agent.data['policies']
    })

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech to text using Web Speech API or external service"""
    # This endpoint can be extended to use services like OpenAI Whisper
    # For now, we'll rely on browser's Web Speech API
    return jsonify({
        'success': False,
        'error': 'Server-side STT not implemented. Use browser Web Speech API.'
    }), 501

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    """Convert text to speech"""
    # This endpoint can be extended to use services like OpenAI TTS
    # For now, we'll rely on browser's Web Speech API
    return jsonify({
        'success': False,
        'error': 'Server-side TTS not implemented. Use browser Web Speech API.'
    }), 501

# ==================== VAPI PHONE CALL ENDPOINTS ====================

@app.route('/api/vapi/public-key', methods=['GET'])
def get_vapi_public_key():
    """Get VAPI public key for web calls"""
    try:
        # VAPI public key would be separate from API key in production
        # For now, return indicator if VAPI is configured
        vapi = get_vapi_agent()
        if not vapi.client:
            return jsonify({
                'configured': False,
                'public_key': None
            })
        
        # Return the API key for web SDK (in production, use separate public key)
        return jsonify({
            'configured': True,
            'public_key': vapi.api_key
        })
    except Exception as e:
        return jsonify({
            'configured': False,
            'error': str(e)
        })

@app.route('/api/vapi/web-call-config', methods=['GET'])
def get_web_call_config():
    """Get assistant configuration for web-based voice calls"""
    try:
        vapi = get_vapi_agent()
        if not vapi.client:
            return jsonify({
                'success': False,
                'error': 'VAPI not configured'
            }), 400
        
        # Get or create assistant
        assistant_id = vapi.assistant_id
        if not assistant_id:
            assistant_id = vapi.create_hotel_assistant()
        
        # Return configuration for VAPI Web SDK
        config = {
            'assistant': {
                'firstMessage': 'Hello! Thank you for calling Hilton Charlotte Airport. I\'m Sarah, your AI front desk assistant. I can help you with room bookings, amenities, and hotel information. If I can\'t assist you, I\'ll connect you with one of our human agents. How can I help you today?',
                'model': {
                    'provider': 'openai',
                    'model': 'gpt-4',
                    'messages': [{
                        'role': 'system',
                        'content': """You are Sarah, a professional AI front desk agent for Hilton Charlotte Airport.

Your Primary Role:
- Handle common hotel inquiries (room availability, pricing, amenities, policies)
- Process simple room bookings when you have all required information
- Provide friendly, professional service

WHEN TO TRANSFER TO HUMAN AGENT:
Transfer immediately if the guest:
1. Explicitly asks to speak with a human/person/agent
2. Has a complex special request (group bookings, events, modifications)
3. Is frustrated or upset
4. Has payment/billing issues
5. Needs immediate assistance you cannot provide
6. Says they don't understand or asks to repeat multiple times

How to Transfer:
- Acknowledge their request professionally
- Use the transfer_to_agent function with the reason
- Say: "I understand. Let me connect you with one of our customer support specialists who can better assist you. Please hold for just a moment."

Your Capabilities:
✅ Check room availability (use check_room_availability function)
✅ Create simple bookings (use create_booking function)
✅ Answer questions about amenities and policies
✅ Provide hotel information
❌ Handle complex requests → TRANSFER
❌ Process refunds/billing → TRANSFER
❌ Modify existing bookings (unless simple) → TRANSFER

Conversation Style:
- Warm, professional, and concise
- Speak naturally (use contractions, conversational tone)
- Confirm important details (dates, names, room types)
- Listen carefully and be patient
- Never pretend you can do something you can't

Hotel Info:
- Hilton Charlotte Airport (near CLT airport)
- Check-in: 3:00 PM | Check-out: 12:00 PM
- Free 24/7 airport shuttle, parking, WiFi
- Pet-friendly (restrictions apply)
- Indoor pool, 24-hour fitness center
- Business center, meeting rooms

Remember: Your job is to help with simple requests and transfer complex ones to humans. Don't try to handle everything yourself."""
                    }],
                    'functions': vapi._get_functions(),
                    'temperature': 0.7
                },
                'voice': {
                    'provider': 'eleven_labs',
                    'voiceId': 'rachel'  # Professional female voice
                },
                'serverUrl': f"{request.url_root}api/vapi/webhook",
                'endCallFunctionEnabled': True
            }
        }
        
        return jsonify(config)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/setup-assistant', methods=['POST'])
def setup_vapi_assistant():
    """Create or update the VAPI assistant for hotel calls"""
    try:
        vapi = get_vapi_agent()
        if not vapi.client:
            return jsonify({
                'success': False,
                'error': 'VAPI not configured. Set VAPI_API_KEY environment variable.'
            }), 400
        
        assistant_id = vapi.create_hotel_assistant()
        return jsonify({
            'success': True,
            'assistant_id': assistant_id,
            'message': 'VAPI assistant created successfully'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/call/inbound', methods=['POST'])
def handle_inbound_call():
    """Handle incoming phone call"""
    try:
        data = request.json
        phone_number = data.get('phone_number')
        
        if not phone_number:
            return jsonify({
                'success': False,
                'error': 'phone_number is required'
            }), 400
        
        vapi = get_vapi_agent()
        call_id = vapi.start_inbound_call(phone_number, metadata=data.get('metadata'))
        
        # Store session
        session_id = str(uuid.uuid4())
        call_sessions[session_id] = {
            'call_id': call_id,
            'phone_number': phone_number,
            'started_at': datetime.now().isoformat(),
            'status': 'active',
            'type': 'inbound'
        }
        
        return jsonify({
            'success': True,
            'call_id': call_id,
            'session_id': session_id,
            'message': f'Call initiated to {phone_number}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/call/outbound', methods=['POST'])
def handle_outbound_call():
    """Make outbound call to guest"""
    try:
        data = request.json
        to_number = data.get('to_number')
        guest_name = data.get('guest_name')
        purpose = data.get('purpose', 'booking_confirmation')
        
        if not to_number:
            return jsonify({
                'success': False,
                'error': 'to_number is required'
            }), 400
        
        vapi = get_vapi_agent()
        call_id = vapi.start_outbound_call(
            to_number=to_number,
            guest_name=guest_name,
            purpose=purpose,
            metadata=data.get('metadata')
        )
        
        # Store session
        session_id = str(uuid.uuid4())
        call_sessions[session_id] = {
            'call_id': call_id,
            'phone_number': to_number,
            'guest_name': guest_name,
            'purpose': purpose,
            'started_at': datetime.now().isoformat(),
            'status': 'active',
            'type': 'outbound'
        }
        
        return jsonify({
            'success': True,
            'call_id': call_id,
            'session_id': session_id,
            'message': f'Calling {guest_name or to_number}...'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/call/status/<call_id>', methods=['GET'])
def get_call_status(call_id):
    """Get status of a specific call"""
    try:
        vapi = get_vapi_agent()
        status = vapi.get_call_status(call_id)
        
        return jsonify({
            'success': True,
            'call_status': status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/call/end', methods=['POST'])
def end_call():
    """End an ongoing call"""
    try:
        data = request.json
        call_id = data.get('call_id')
        session_id = data.get('session_id')
        
        # Find call_id from session if not provided
        if not call_id and session_id:
            session = call_sessions.get(session_id)
            if session:
                call_id = session.get('call_id')
        
        if not call_id:
            return jsonify({
                'success': False,
                'error': 'call_id or session_id required'
            }), 400
        
        vapi = get_vapi_agent()
        success = vapi.end_call(call_id)
        
        # Update session status
        if session_id and session_id in call_sessions:
            call_sessions[session_id]['status'] = 'ended'
            call_sessions[session_id]['ended_at'] = datetime.now().isoformat()
        
        return jsonify({
            'success': success,
            'message': 'Call ended' if success else 'Failed to end call'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/vapi/webhook', methods=['POST'])
def vapi_webhook():
    """
    Webhook endpoint for VAPI events
    Receives updates about call status, transcripts, function calls, etc.
    """
    print("🔥 WEBHOOK CALLED!", flush=True)
    try:
        payload = request.json
        print(f"\n\n[VAPI Webhook] Received event", flush=True)
        print(f"Event type: {payload.get('type') or payload.get('message', {}).get('type')}", flush=True)
        print(f"Full payload: {json.dumps(payload, indent=2)}", flush=True)
        
        # Extract call_id
        call_id = (
            payload.get('call_id')
            or payload.get('id')
            or (payload.get('call') or {}).get('id')
            or (payload.get('message') or {}).get('callId')
        )
        
        # Handle different event types
        event_type = payload.get('type') or payload.get('message', {}).get('type')
        
        # Find associated session
        session_id = None
        for sid, sess in call_sessions.items():
            if sess.get('call_id') == call_id:
                session_id = sid
                break
        
        # Process function calls from the assistant
        # Check for different function call formats
        function_name = None
        function_args = None
        
        if event_type == 'function-call':
            function_name = payload.get('function', {}).get('name')
            function_args = payload.get('function', {}).get('parameters', {})
        elif 'toolCalls' in payload:
            # Handle toolCalls format
            tool_calls = payload.get('toolCalls', [])
            if tool_calls:
                function_name = tool_calls[0].get('function', {}).get('name')
                function_args = tool_calls[0].get('function', {}).get('arguments', {})
                if isinstance(function_args, str):
                    try:
                        function_args = json.loads(function_args)
                    except:
                        function_args = {}
        
        if function_name:
            print(f"\n[Function Call] {function_name} with args: {function_args}", flush=True)
            
            try:
                # Handle hotel-specific function calls
                result = handle_vapi_function_call(function_name, function_args)
                
                print(f"[Function Result] {function_name}: {result}", flush=True)
                
                # Return result to VAPI in the expected format
                return jsonify({
                    'success': True,
                    'result': result
                })
            except Exception as e:
                print(f"[Function Error] {function_name}: {str(e)}")
                return jsonify({
                    'available': False,
                    'message': f'Sorry, I encountered an error: {str(e)}'
                })
        
        # Handle call status updates
        elif event_type in ['call-started', 'call-ended']:
            if session_id:
                call_sessions[session_id]['status'] = 'ended' if event_type == 'call-ended' else 'active'
                if event_type == 'call-ended':
                    call_sessions[session_id]['ended_at'] = datetime.now().isoformat()
                    
                    # Extract call summary/transcript
                    summary = (
                        (payload.get('message') or {}).get('analysis', {}).get('summary')
                        or payload.get('summary')
                        or "Call completed"
                    )
                    call_sessions[session_id]['summary'] = summary
        
        return jsonify({'success': True, 'received': True})
        
    except Exception as e:
        print(f"[VAPI Webhook Error] {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def handle_vapi_function_call(function_name: str, args: dict) -> dict:
    """
    Handle function calls made by the VAPI assistant during calls
    """
    try:
        if function_name == 'check_room_availability':
            # Check room availability - TRY AMADEUS FIRST (real-time data!)
            check_in = args.get('check_in')
            check_out = args.get('check_out')
            guests = args.get('guests', 1)
            room_type = args.get('room_type', '').lower()
            
            # Parse natural language dates if needed
            if check_in and not re.match(r'\d{4}-\d{2}-\d{2}', check_in):
                parsed_date = parse_natural_date(check_in)
                if parsed_date:
                    check_in = parsed_date
                    print(f"📞 PHONE CALL: Parsed check-in date: {check_in}")
            
            if check_out and not re.match(r'\d{4}-\d{2}-\d{2}', check_out):
                parsed_date = parse_natural_date(check_out)
                if parsed_date:
                    check_out = parsed_date
                    print(f"📞 PHONE CALL: Parsed check-out date: {check_out}")
            
            # If we have a date range string, try to parse it
            if not check_in and not check_out:
                date_range = args.get('date_range') or args.get('dates')
                if date_range:
                    parsed_start, parsed_end = parse_date_range(date_range)
                    if parsed_start:
                        check_in = parsed_start
                    if parsed_end:
                        check_out = parsed_end
                    print(f"📞 PHONE CALL: Parsed date range: {check_in} to {check_out}")
            
            available_rooms = []
            
            # Try to get REAL hotel data from Amadeus
            amadeus = get_amadeus_api()
            if amadeus.is_configured() and check_in and check_out:
                try:
                    print(f"📞 PHONE CALL: Fetching real-time data from Amadeus for {check_in} to {check_out}")
                    available_rooms = amadeus.search_charlotte_airport_hotels(
                        check_in, check_out, guests
                    )
                    print(f"📞 PHONE CALL: Found {len(available_rooms)} real hotels from Amadeus")
                except Exception as e:
                    print(f"📞 PHONE CALL: Amadeus error: {e}, using static data")
            
            # Fallback to static data if Amadeus failed or not configured
            if not available_rooms:
                # Filter for available rooms only
                available_rooms = [room for room in agent.data['rooms'] if room.get('available', True)]
                print(f"📞 PHONE CALL: Using static data - {len(available_rooms)} available rooms")
            
            if room_type:
                available_rooms = [r for r in available_rooms if room_type in r['type'].lower()]
            
            if not available_rooms:
                return {
                    'available': False,
                    'message': 'No rooms available for your dates'
                }
            
            # Return multiple room options
            room_options = []
            for room in available_rooms[:3]:
                room_options.append({
                    'type': room['type'],
                    'price': room['price_per_night'],
                    'capacity': room['capacity']
                })
            
            room_info = available_rooms[0]
            return {
                'available': True,
                'rooms': room_options,
                'room_type': room_info['type'],
                'price': room_info['price_per_night'],
                'room_id': room_info['id'],
                'message': f"Yes, we have several rooms available. For example, our {room_info['type']} is ${room_info['price_per_night']} per night. We also have other options available."
            }
        
        elif function_name == 'create_booking':
            # Create booking
            guest_name = args.get('guest_name')
            room_type = args.get('room_type', '').lower()
            
            # Find room (demo mode - use available rooms only)
            available_rooms = [room for room in agent.data['rooms'] if room.get('available', True)]
            if room_type:
                room = next((r for r in available_rooms if room_type in r['type'].lower()), None)
            else:
                room = available_rooms[0] if available_rooms else None
            
            if not room:
                return {
                    'success': False,
                    'message': 'Sorry, no rooms of that type are currently available. Would you like to hear about other room types?'
                }
            
            # Create booking
            booking_id = f"BK{len(agent.data['bookings']) + 1:04d}"
            booking = {
                'booking_id': booking_id,
                'guest_name': guest_name,
                'guest_phone': args.get('guest_phone'),
                'guest_email': args.get('guest_email'),
                'room_id': room['id'],
                'room_type': room['type'],
                'price_per_night': room['price_per_night'],
                'check_in': args.get('check_in'),
                'check_out': args.get('check_out'),
                'guests': args.get('guests', 1),
                'special_requests': args.get('special_requests'),
                'created_at': datetime.now().isoformat(),
                'source': 'phone_call'
            }
            
            agent.data['bookings'].append(booking)
            room['available'] = False
            agent.save_data()
            
            return {
                'success': True,
                'booking_id': booking_id,
                'room_type': room['type'],
                'price': room['price_per_night'],
                'message': f"Perfect! Your reservation is confirmed. Your booking number is {booking_id}"
            }
        
        elif function_name == 'cancel_booking':
            booking_id = args.get('booking_id')
            booking = next((b for b in agent.data['bookings'] if b['booking_id'] == booking_id), None)
            
            if not booking:
                return {
                    'success': False,
                    'message': f'I could not find booking {booking_id}'
                }
            
            # Cancel booking
            agent.data['bookings'].remove(booking)
            room = next((r for r in agent.data['rooms'] if r['id'] == booking['room_id']), None)
            if room:
                room['available'] = True
            agent.save_data()
            
            return {
                'success': True,
                'message': f'Your booking {booking_id} has been successfully cancelled'
            }
        
        elif function_name == 'get_booking_details':
            booking_id = args.get('booking_id')
            booking = next((b for b in agent.data['bookings'] if b['booking_id'] == booking_id), None)
            
            if not booking:
                return {
                    'found': False,
                    'message': 'Booking not found'
                }
            
            return {
                'found': True,
                'booking': booking,
                'message': f"Found your booking: {booking['room_type']} for {booking['guest_name']}"
            }
        
        elif function_name == 'transfer_to_agent':
            reason = args.get('reason', 'General assistance')
            return {
                'success': True,
                'transfer': True,
                'reason': reason,
                'message': f'I understand you need help with {reason}. Let me transfer you to one of our human agents who can better assist you. Please hold for just a moment.'
            }
        
        return {
            'success': False,
            'message': 'Function not recognized'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': 'An error occurred processing your request'
        }

@app.route('/api/vapi/sessions', methods=['GET'])
def get_call_sessions():
    """Get all call sessions"""
    return jsonify({
        'success': True,
        'sessions': call_sessions
    })

# ==================== AMADEUS REAL-TIME HOTEL DATA ====================

@app.route('/api/amadeus/search', methods=['POST'])
def search_amadeus_hotels():
    """
    Search for real hotels using Amadeus API
    """
    try:
        data = request.json
        city_code = data.get('city_code', 'CLT')  # Default to Charlotte
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        guests = data.get('guests', 1)
        
        # Validate dates
        if not check_in or not check_out:
            # Default to tomorrow for 1 night
            tomorrow = datetime.now() + timedelta(days=1)
            day_after = datetime.now() + timedelta(days=2)
            check_in = tomorrow.strftime('%Y-%m-%d')
            check_out = day_after.strftime('%Y-%m-%d')
        
        amadeus = get_amadeus_api()
        
        if not amadeus.is_configured():
            return jsonify({
                'success': False,
                'error': 'Amadeus API not configured. Using static data.',
                'using_static': True
            }), 200
        
        # Search for hotels
        hotels = amadeus.search_charlotte_airport_hotels(check_in, check_out, guests)
        
        return jsonify({
            'success': True,
            'hotels': hotels,
            'source': 'amadeus',
            'check_in': check_in,
            'check_out': check_out
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'using_static': True
        }), 200

@app.route('/api/amadeus/status', methods=['GET'])
def amadeus_status():
    """Check if Amadeus API is configured and working"""
    amadeus = get_amadeus_api()
    
    if not amadeus.is_configured():
        return jsonify({
            'configured': False,
            'message': 'Amadeus API keys not set. Add AMADEUS_API_KEY and AMADEUS_API_SECRET to .env'
        })
    
    try:
        # Test authentication
        token = amadeus._get_access_token()
        return jsonify({
            'configured': True,
            'authenticated': True,
            'message': 'Amadeus API ready to use!'
        })
    except Exception as e:
        return jsonify({
            'configured': True,
            'authenticated': False,
            'error': str(e)
        })

if __name__ == '__main__':
    # Ensure templates directory exists
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    print("🏨 Hotel Front Desk Agent Server Starting...")
    print("📍 Server running at: http://localhost:5000")
    print("\n💬 Chat API endpoints:")
    print("   - GET  /api/greeting")
    print("   - POST /api/chat")
    print("   - GET  /api/rooms")
    print("   - GET  /api/bookings")
    print("   - GET  /api/amenities")
    print("   - GET  /api/policies")
    print("\n🏨 Amadeus Hotel API endpoints (Real-time data):")
    print("   - POST /api/amadeus/search")
    print("   - GET  /api/amadeus/status")
    print("\n📞 VAPI Phone Call endpoints:")
    print("   - POST /api/vapi/setup-assistant")
    print("   - POST /api/vapi/call/inbound")
    print("   - POST /api/vapi/call/outbound")
    print("   - GET  /api/vapi/call/status/<call_id>")
    print("   - POST /api/vapi/call/end")
    print("   - POST /api/vapi/webhook")
    print("   - GET  /api/vapi/sessions")
    print("\n✨ Open http://localhost:5000 in your browser to start!")
    print("📖 Setup guides:")
    print("   - Amadeus (real data): AMADEUS_SETUP.md")
    print("   - Phone calls: VAPI_SETUP.md\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)


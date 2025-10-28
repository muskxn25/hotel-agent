# Booking Flow Improvements

## Overview
Enhanced the hotel booking system with dynamic updates and real-time hotel data integration via Amadeus API.

## New Features

### 1. Visual Booking Widget (Interactive UI)
When users select "Check Rooms" (option 1) or "Book Room" (option 2), an interactive booking widget appears with:
- **📅 Calendar Date Pickers**: Select check-in and check-out dates visually
- **👥 Guest Selector**: Dropdown to choose number of guests (1-8)
- **🌙 Auto-calculated Nights**: Automatically calculates nights between dates
- **Modern UI**: Clean, professional interface with validation

**Benefits:**
- No typing required - just click and select
- Prevents date entry errors
- Instant visual feedback
- Mobile-friendly interface
- Calculates nights automatically

### 2. Date-Based Availability Check
When users check room availability (option 1), the system now asks for dates first before showing available rooms.

**Example Flow:**
```
You: "1" (Check room availability)
Agent: "What dates would you like to check?"

You: "Oct 15 to Oct 18"
Agent: Shows available rooms for those specific dates with pricing
```

This ensures users see accurate availability and pricing for their specific travel dates.

### 2. Dynamic Guest Count Updates
Users can now update the number of guests during room selection without restarting the booking process.

**Example Flow:**
```
You: "3 guests"
Agent: Shows rooms for 3 guests

You: "5 guests"  
Agent: Updates search and shows rooms for 5 guests
```

### 3. Dynamic Night Count Updates
Users can update the number of nights during room selection, and all pricing is automatically recalculated.

**Example Flow:**
```
You: "2 guests"
Agent: Shows rooms for 2 guests, 1 night (default)

You: "3 nights"  
Agent: Updates to 3 nights with recalculated pricing
```

### 4. Enhanced Guest Information & Payment Collection
The booking flow now collects comprehensive guest details and payment via a professional form:

**Required Information:**
- ✅ **Full Name** - guest identification
- ✅ **Phone Number** - primary contact method
- ✅ **Card Number** - payment (can skip)
- ✅ **Expiry & CVV** - payment validation

**Optional Information:**
- 📧 **Email Address** - for email confirmations (optional)
- 💬 **Special Requests** - late check-in, accessible room, etc.

**Form Features:**
- Clean, professional UI matching the design aesthetic
- Auto-formatting for card number (1234 5678 9012 3456)
- Auto-formatting for expiry (MM/YY)
- Real-time validation for all fields
- Card security (only last 4 digits stored)
- "Skip Payment" option for pay-at-hotel

**Benefits:**
- One-step form completion
- Professional booking experience
- Secure payment handling
- Complete guest records
- Flexible payment options

### 5. Amadeus API Integration
The system now fetches **real-time hotel data** from the Amadeus API when configured.

**Features:**
- Real hotel availability near Charlotte Airport
- Live pricing data
- Multiple hotel options (not just static Hilton data)
- Automatic fallback to static data if Amadeus is unavailable

## How It Works

### Availability Check Flow

1. **Initial Request**: User selects "Check room availability" (option 1)
   ```
   You: "1"
   ```

2. **Date Input**: System asks for check-in and check-out dates
   ```
   Agent: "What dates would you like to check?"
   ```

3. **User Provides Dates**: Various formats supported
   ```
   You: "Oct 15 to Oct 18"
   OR
   You: "October 20 for 3 nights"
   OR  
   You: "Nov 1 to Nov 5"
   ```

4. **Display Results**: System shows available rooms with:
   - Room type and hotel name (if Amadeus)
   - Capacity
   - Price per night × number of nights = total
   - Top amenities
   - Prompt to book if interested

### Booking Flow

1. **Initial Request**: User selects "Book a room" (option 2)

2. **Guest Input**: System asks for number of guests
   ```
   You: "3 guests"
   ```

3. **Room Display**: System shows available rooms
   - If Amadeus is configured: Shows real hotels from API
   - Otherwise: Shows static Hilton Charlotte Airport rooms

4. **Dynamic Updates**: User can update:
   - Number of nights: "2 nights", "3 days", etc.
   - Number of guests: "4 guests", "2 people", etc.
   - System recalculates and re-displays options

5. **Room Selection**: User selects room type
   ```
   You: "Queen"
   ```

6. **Guest & Payment Form**: Interactive form collects:
   - **Full Name** (required)
   - **Phone Number** (required)
   - **Email Address** (optional)
   - **Special Requests** (optional)
   - **Card Number** (required)
   - **Expiry & CVV** (required)
   - **"Skip Payment"** option available

7. **Instant Confirmation**: Booking completes immediately with all details:
   - Guest contact information
   - Payment method (masked for security)
   - Special requests
   - Reservation details
   - Confirmation sent via email or SMS

### Amadeus Integration

#### Setup
To use real hotel data, configure Amadeus API credentials in `.env`:

```bash
AMADEUS_API_KEY=your_api_key_here
AMADEUS_API_SECRET=your_api_secret_here
```

See `AMADEUS_SETUP.md` for detailed setup instructions.

#### How It Works

1. **Check Configuration**: System checks if Amadeus credentials are set
2. **API Call**: If configured, fetches real hotel data for:
   - Location: Charlotte Airport (CLT)
   - Dates: Calculated from nights or provided dates
   - Guests: Number of guests specified
3. **Fallback**: If API fails or not configured, uses static hotel data
4. **Display**: Shows hotel name for Amadeus results

#### Data Differences

**Amadeus Data:**
- Shows actual hotel name (e.g., "Holiday Inn Charlotte Airport")
- No static room numbers
- Real-time pricing
- Source marked as "amadeus"

**Static Data:**
- Hilton Charlotte Airport only
- Room numbers (e.g., Room #203)
- Fixed pricing
- Source marked as "web_chat"

## Technical Implementation

### Key Changes in `app.py`

1. **Guest/Night Updates** (`awaiting_room_selection` state):
   - Detects patterns like "X guests", "Y nights"
   - Updates session data
   - Refetches/recalculates rooms
   - Redisplays with updated pricing

2. **Amadeus Integration**:
   - Calls `amadeus.search_charlotte_airport_hotels()` with dates and guests
   - Stores results in session for later selection
   - Handles both Amadeus and static room data uniformly

3. **Booking Creation**:
   - Stores hotel name for Amadeus bookings
   - Marks source as "amadeus" or "web_chat"
   - Only marks static rooms as unavailable (Amadeus rooms are real-time)

### Session Data Structure

```python
session['booking_data'] = {
    'guests': 3,
    'nights': 2,
    'check_in': '2025-10-13',
    'check_out': '2025-10-15',
    'available_rooms': [...],  # Cached room list
    'using_amadeus': True,     # Flag for data source
    'room': {...}              # Selected room
}
```

## Example Conversations

### Scenario 1: Static Data with Updates
```
Agent: How many guests will be staying?
You: 2 guests
Agent: [Shows 2-guest rooms for 1 night]

You: 3 nights
Agent: Updated to 3 night(s). [Shows rooms with 3-night pricing]

You: 4 guests
Agent: Updated to 4 guest(s) for 3 night(s). [Shows 4-guest rooms]

You: Queen
Agent: [Shows Queen room confirmation]

You: John Smith
Agent: ✅ RESERVATION CONFIRMED! [Details]
```

### Scenario 2: Amadeus API Data
```
Agent: How many guests will be staying?
You: 2 guests
Agent: Perfect! For 2 guest(s) staying 1 night(s):

**Standard Room** at Holiday Inn Charlotte Airport
• Capacity: 2 guests
• $125.00/night × 1 nights = $125.00 total
• Amenities: Free WiFi, Flat-screen TV, Coffee maker

**Deluxe Room** at Hilton Charlotte Airport
• Capacity: 2 guests  
• $159.00/night × 1 nights = $159.00 total
• Amenities: Free WiFi, Flat-screen TV, Mini-fridge

Which room would you like?

You: Standard
Agent: ✨ Excellent choice!

**Hotel:** Holiday Inn Charlotte Airport
**Room:** Standard Room
**Nightly Rate:** $125.00
**Total Cost:** $125.00 for 1 night(s)
...
```

## Benefits

1. **Flexibility**: Users can adjust booking details without restarting
2. **Real Data**: Live hotel availability and pricing via Amadeus
3. **More Options**: Shows multiple hotels, not just one property
4. **Seamless Fallback**: Works with or without Amadeus API
5. **Better UX**: Natural conversation flow with dynamic updates

## Testing

### Test Availability Check with Dates
1. Select availability: "1"
2. Agent asks: "What dates would you like to check?"
3. Provide dates: "Oct 15 to Oct 18"
4. Verify: Should show available rooms for those specific dates with pricing
5. Check: Should calculate correct number of nights and total price

### Test Guest Updates
1. Start booking: "2"
2. Enter guests: "2 guests"
3. Update guests: "4 guests"
4. Verify: Should show 4-guest rooms

### Test Night Updates  
1. Start booking: "2"
2. Enter guests: "2 guests"
3. Update nights: "3 nights"
4. Verify: Prices should reflect 3 nights
5. Check: Check-out date should be check-in + 3 nights

### Test Amadeus Integration
1. Configure Amadeus credentials in `.env`
2. Check availability: "1"
3. Provide dates: "Oct 20 to Oct 23"
4. Verify: Should show real hotel names from Amadeus API
5. Check server logs: Should see "Checking availability via Amadeus API"

## Bug Fixes

### Date Calculation Fix
**Issue**: When updating nights during room selection, the check-out date wasn't recalculated, causing inconsistency:
```
Check-in: Oct 13
Check-out: Oct 14 (1 day)
Nights: 3 ❌ Wrong!
```

**Fix**: Now always recalculates check-out date based on: `check-in + nights`
```
Check-in: Oct 13
Nights: 3
Check-out: Oct 16 ✅ Correct!
```

## Notes

- **Demo Mode**: System always shows rooms from static data for demonstration purposes, even if marked as unavailable
- Date parsing is simplified (looks for month + day patterns)
- Default dates are tomorrow + specified nights if not provided
- Check-out date is always calculated as: check-in date + number of nights
- Amadeus test API has a limit of 2,000 calls/month
- If Amadeus API fails or returns no data, system automatically falls back to showing static demo rooms
- Room capacity matching is approximate for Amadeus data
- System maintains conversation state across the booking flow
- Booking widget prevents invalid date selections (checkout must be after checkin)

## Future Enhancements

- [ ] Better date parsing (full date formats)
- [ ] Support for specific date ranges
- [ ] Filter by price range
- [ ] Filter by amenities
- [ ] Multiple room booking
- [ ] Payment integration
- [ ] Email confirmations
- [ ] SMS notifications via VAPI


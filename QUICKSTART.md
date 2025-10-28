# Quick Start Guide

Get the hotel front desk agent running in 5 minutes!

## Basic Setup (Text & Web Voice)

### 1. Install Dependencies
```bash
cd "hotel agent"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python app.py
```

### 3. Open Web Interface
Open your browser to: **http://localhost:5000**

### 4. Try It Out!

Type or speak these queries:
- "Show me available rooms"
- "I'd like to book a deluxe room, my name is John Smith"
- "What time is check-in?"
- "Do you have parking?"
- "Tell me about your amenities"

## Advanced Setup (Real Phone Calls)

Want to handle actual phone calls? Follow the [VAPI Setup Guide](VAPI_SETUP.md)

### Quick VAPI Setup:

1. **Sign up** at [https://vapi.ai](https://vapi.ai)
2. **Get API key** from dashboard
3. **Configure environment**:
   ```bash
   cp env.template .env
   # Edit .env with your VAPI_API_KEY
   ```
4. **Create assistant**:
   ```bash
   curl -X POST http://localhost:5000/api/vapi/setup-assistant
   ```
5. **Make a test call**:
   ```bash
   curl -X POST http://localhost:5000/api/vapi/call/outbound \
     -H "Content-Type: application/json" \
     -d '{
       "to_number": "+1234567890",
       "guest_name": "Test",
       "purpose": "booking_confirmation"
     }'
   ```

## API Examples

### Check Room Availability
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Do you have any deluxe rooms available?"}'
```

### Create Booking
```bash
curl -X POST http://localhost:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "I want to book a suite, my name is Jane Doe"}'
```

### Get All Rooms
```bash
curl http://localhost:5000/api/rooms
```

### Get All Bookings
```bash
curl http://localhost:5000/api/bookings
```

## Testing the Agent

### Conversation Flow Testing

**Test 1: Room Inquiry**
```
You: "Hi, do you have any rooms available?"
Agent: [Shows available rooms with prices]
```

**Test 2: Booking Flow**
```
You: "I'd like to book a deluxe king room"
Agent: [Asks for your name]
You: "My name is Michael Chen"
Agent: [Confirms booking with booking ID]
```

**Test 3: FAQs**
```
You: "What time is checkout?"
Agent: "Check-out time is 11:00 AM..."
```

**Test 4: Amenities**
```
You: "What amenities do you offer?"
Agent: [Lists all amenities]
```

### Voice Mode Testing (Browser)

1. Click **🎤 Voice Mode** button
2. Speak: "Show me available rooms"
3. Listen to the agent's response
4. Continue the conversation

## Common Issues

### Port Already in Use
```bash
# Change port in app.py (line with app.run)
app.run(debug=True, host='0.0.0.0', port=5001)
```

### Voice Mode Not Working
- Use Chrome or Edge browser
- Grant microphone permissions
- Must use HTTPS or localhost

### VAPI "Client not initialized"
- Set `VAPI_API_KEY` in `.env` file
- Restart the server

## Project Files

- **hotel_data.json** - Hotel database (rooms, bookings, policies)
- **hotel_agent.py** - Core AI logic
- **app.py** - API server
- **vapi_integration.py** - Phone call handling
- **templates/index.html** - Web UI

## Next Steps

✅ Basic demo working  
⬜ Customize hotel data in `hotel_data.json`  
⬜ Modify UI in `templates/index.html`  
⬜ Add VAPI for phone calls  
⬜ Deploy to production  

## Resources

- **Full README**: [README.md](README.md)
- **VAPI Phone Setup**: [VAPI_SETUP.md](VAPI_SETUP.md)
- **Environment Template**: [env.template](env.template)

## Support

Need help? Check:
1. Server console for error messages
2. Browser console (F12) for frontend errors
3. README.md for detailed documentation
4. VAPI_SETUP.md for phone call issues

---

**Happy building! 🏨🤖**


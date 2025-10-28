# VAPI Phone Call Integration Guide

This guide explains how to set up and use the VAPI (Voice AI Platform Integration) for handling real phone calls with the hotel front desk agent.

## What is VAPI?

VAPI is a voice AI platform that allows you to create AI agents that can:
- **Handle phone calls** (inbound and outbound)
- **Understand natural speech** using speech-to-text
- **Respond with voice** using text-to-speech
- **Execute actions** through function calling
- **Integrate with existing systems** via webhooks

## Architecture

```
Guest Phone Call
       ↓
   VAPI Platform (Voice AI)
       ↓
   Hotel Agent Server (Flask)
       ↓
   Hotel Database (JSON)
```

## Setup Instructions

### 1. Create VAPI Account

1. Go to [https://vapi.ai](https://vapi.ai)
2. Sign up for an account
3. Navigate to your dashboard

### 2. Get Your API Keys

1. In VAPI dashboard, go to **Settings** → **API Keys**
2. Create a new API key
3. Copy the key - you'll need it for `.env`

### 3. Configure Phone Number

1. In VAPI dashboard, go to **Phone Numbers**
2. Purchase a phone number or configure your existing one
3. Copy the **Phone Number ID** (not the actual phone number)

### 4. Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit `.env` and add your credentials:

```env
VAPI_API_KEY=your_actual_vapi_api_key
VAPI_PHONE_NUMBER_ID=your_phone_number_id
```

### 5. Install Dependencies

```bash
source venv/bin/activate
pip install -r requirements.txt
```

### 6. Create the Assistant

Run the server and create the VAPI assistant:

```bash
python app.py
```

In another terminal:

```bash
curl -X POST http://localhost:5000/api/vapi/setup-assistant
```

This will create a VAPI assistant configured for hotel operations. Save the returned `assistant_id` and add it to your `.env`:

```env
VAPI_ASSISTANT_ID=your_assistant_id_here
```

### 7. Configure Webhook

1. Make sure your server is publicly accessible (use ngrok for testing):
   ```bash
   ngrok http 5000
   ```

2. In VAPI dashboard, go to your assistant settings
3. Set **Webhook URL** to: `https://your-domain.com/api/vapi/webhook`
4. Enable webhook events:
   - `call-started`
   - `call-ended`
   - `function-call`
   - `transcript`

## Usage

### Inbound Calls

When someone calls your VAPI phone number, they'll automatically be connected to the hotel front desk agent.

The agent can:
- Greet callers
- Check room availability
- Process bookings
- Answer questions about amenities and policies
- Transfer to human agents

### Outbound Calls

Make outbound calls to guests:

```bash
curl -X POST http://localhost:5000/api/vapi/call/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+1234567890",
    "guest_name": "John Doe",
    "purpose": "booking_confirmation"
  }'
```

**Purpose options:**
- `booking_confirmation` - Confirm a reservation
- `reminder` - Send a reminder about upcoming stay
- `follow_up` - Follow up after checkout

### Check Call Status

```bash
curl http://localhost:5000/api/vapi/call/status/CALL_ID
```

### End a Call

```bash
curl -X POST http://localhost:5000/api/vapi/call/end \
  -H "Content-Type: application/json" \
  -d '{"call_id": "CALL_ID"}'
```

### View All Sessions

```bash
curl http://localhost:5000/api/vapi/sessions
```

## How It Works

### 1. Call Flow

```
1. Guest calls hotel number
2. VAPI answers with greeting
3. Guest speaks request
4. VAPI transcribes speech
5. AI processes request
6. If booking needed, calls function
7. Function updates database
8. AI responds to guest
9. VAPI speaks response
10. Call ends or continues
```

### 2. Function Calling

The AI assistant can execute these functions during calls:

| Function | Description | Example |
|----------|-------------|---------|
| `check_room_availability` | Check if rooms are available | "Do you have any deluxe rooms available next weekend?" |
| `create_booking` | Book a room | "I'd like to book a suite for 3 nights" |
| `cancel_booking` | Cancel a reservation | "I need to cancel booking BK0001" |
| `get_booking_details` | Retrieve booking info | "What's my booking number?" |
| `transfer_to_agent` | Transfer to human | "I need to speak with someone" |

### 3. Conversation Examples

**Example 1: Room Booking**
```
Agent: "Thank you for calling Grand Plaza Hotel! This is Sarah. How may I help you?"
Guest: "Hi, I'd like to book a deluxe king room for this Friday and Saturday."
Agent: "Perfect! May I have your name please?"
Guest: "It's Michael Chen."
Agent: "Thank you Michael. Let me check availability for this Friday and Saturday..."
[AI calls check_room_availability function]
Agent: "Great news! We have a Deluxe King room available at $180 per night. Would you like me to book that for you?"
Guest: "Yes please."
Agent: "Wonderful! May I have a phone number for the reservation?"
Guest: "555-1234"
[AI calls create_booking function]
Agent: "Perfect! Your reservation is confirmed. Your booking number is BK0002. Is there anything else I can help you with?"
```

**Example 2: Information Query**
```
Agent: "Thank you for calling Grand Plaza Hotel!"
Guest: "Do you have parking?"
Agent: "Yes! We offer complimentary self-parking for all guests. Valet parking is also available for $25 per day. Is there anything else you'd like to know?"
```

## Testing

### Test with Postman/cURL

1. **Start a test call:**
```bash
curl -X POST http://localhost:5000/api/vapi/call/outbound \
  -H "Content-Type: application/json" \
  -d '{
    "to_number": "+YOUR_PHONE_NUMBER",
    "guest_name": "Test Guest",
    "purpose": "booking_confirmation"
  }'
```

2. **Answer the call and test the conversation**

3. **Check the webhook logs** in your server console

### Test Webhook Locally

Use ngrok to expose your local server:

```bash
# Terminal 1: Run the server
python app.py

# Terminal 2: Run ngrok
ngrok http 5000

# Copy the https URL (e.g., https://abc123.ngrok.io)
# Update VAPI webhook URL to: https://abc123.ngrok.io/api/vapi/webhook
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/vapi/setup-assistant` | POST | Create/update VAPI assistant |
| `/api/vapi/call/inbound` | POST | Handle inbound call |
| `/api/vapi/call/outbound` | POST | Make outbound call |
| `/api/vapi/call/status/<call_id>` | GET | Get call status |
| `/api/vapi/call/end` | POST | End active call |
| `/api/vapi/webhook` | POST | Webhook for VAPI events |
| `/api/vapi/sessions` | GET | List all call sessions |

## Customization

### Modify Assistant Personality

Edit the system prompt in `vapi_integration.py`:

```python
def _get_system_prompt(self) -> str:
    return """You are [YOUR CUSTOM PERSONALITY]...
    [YOUR CUSTOM INSTRUCTIONS]
    """
```

### Add New Functions

In `vapi_integration.py`, add to `_get_functions()`:

```python
{
    "name": "your_function_name",
    "description": "What it does",
    "parameters": {
        "type": "object",
        "properties": {
            "param1": {"type": "string", "description": "..."},
        },
        "required": ["param1"],
    },
}
```

Then handle it in `app.py` → `handle_vapi_function_call()`:

```python
elif function_name == 'your_function_name':
    # Your logic here
    return {'success': True, 'message': 'Done!'}
```

### Change Voice

Modify the voice settings in `vapi_integration.py`:

```python
"voice": {
    "provider": "11labs",  # or "playht", "deepgram"
    "voiceId": "rachel",   # Choose from available voices
}
```

Available voices:
- `rachel` - Professional female
- `josh` - Professional male
- `adam` - Friendly male
- `bella` - Warm female

## Troubleshooting

### Issue: "VAPI client not initialized"

**Solution:** Make sure you've set `VAPI_API_KEY` in your `.env` file and restarted the server.

### Issue: Calls not connecting

**Solutions:**
1. Verify phone number format includes country code (e.g., +1234567890)
2. Check VAPI dashboard for call logs
3. Ensure you have sufficient VAPI credits

### Issue: Webhook not receiving events

**Solutions:**
1. Verify webhook URL is publicly accessible
2. Check webhook URL in VAPI dashboard
3. Ensure webhook URL ends with `/api/vapi/webhook`
4. Check server logs for incoming webhook requests

### Issue: Functions not executing

**Solutions:**
1. Check server logs for function call errors
2. Verify function is defined in `_get_functions()`
3. Ensure handler exists in `handle_vapi_function_call()`
4. Check function parameter types match

## Costs

VAPI pricing (as of 2025):
- **Inbound calls**: ~$0.01-0.02 per minute
- **Outbound calls**: ~$0.02-0.03 per minute
- **Phone number**: ~$2-5 per month

For exact pricing, visit [https://vapi.ai/pricing](https://vapi.ai/pricing)

## Production Deployment

### 1. Use a production WSGI server

Replace Flask's development server with Gunicorn:

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 2. Set up HTTPS

VAPI requires HTTPS for webhooks. Use:
- **Nginx** with Let's Encrypt SSL
- **Cloud provider** SSL termination (AWS ALB, Google Cloud Load Balancer)

### 3. Use persistent storage

Replace JSON file with a database:
- PostgreSQL for production
- MongoDB for flexibility
- Redis for caching

### 4. Monitor calls

Set up logging and monitoring:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### 5. Handle errors gracefully

```python
try:
    # Your call logic
except Exception as e:
    logging.error(f"Call error: {e}")
    # Send notification to ops team
```

## Alternative: Twilio Integration

If you prefer Twilio over VAPI:

1. Get Twilio credentials from [https://twilio.com](https://twilio.com)
2. Install Twilio SDK: `pip install twilio`
3. Use the example code in `AutoCallerBot-main/agent_backend/server/twilio_driver.py`

## Support

- **VAPI Docs**: https://docs.vapi.ai
- **VAPI Discord**: https://discord.gg/vapi
- **Hotel Agent Issues**: Create an issue in this repository

## Next Steps

1. ✅ Set up VAPI account
2. ✅ Configure environment variables  
3. ✅ Create assistant
4. ✅ Test with a phone call
5. ⬜ Customize voice and personality
6. ⬜ Add more functions
7. ⬜ Deploy to production

---

**Questions?** Check the main README.md or create an issue!


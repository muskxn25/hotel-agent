# Hotel Front Desk Agent - Complete System Architecture

## 🏗️ System Overview

You've built a **full-featured AI hotel booking system** with:
- 💬 Text chat interface
- 📞 Voice calling with AI-to-human transfer
- 📅 Interactive booking widgets
- 💳 Payment processing
- 🌐 Real-time hotel data from Amadeus API

## 🧩 Technology Stack

### Frontend (Browser)
- **HTML5** - Structure
- **CSS3** - Styling (gradients, animations, responsive design)
- **Vanilla JavaScript** - All interactions, no frameworks
- **Web Speech API** - Browser's built-in speech recognition & synthesis
- **VAPI Web SDK** - Professional voice AI (optional)

### Backend (Server)
- **Python 3** - Programming language
- **Flask** - Web framework for API and serving pages
- **OpenAI GPT** - AI intelligence (optional, for advanced intent detection)
- **Amadeus API** - Real hotel data from worldwide database
- **VAPI API** - Professional voice AI platform

### Data Storage
- **JSON file** (`hotel_data.json`) - Simple file-based database
- Stores: rooms, bookings, amenities, policies

---

## 🔄 How The System Works

### 1️⃣ **Text Chat Flow**

```
User types message
       ↓
Frontend (JavaScript)
       ↓
POST /api/chat
       ↓
Flask Backend (app.py)
       ↓
Session Management (tracks conversation state)
       ↓
Intent Detection (what user wants)
       ↓
hotel_agent.py (processes request)
       ↓
hotel_data.json (gets/updates data)
       ↓
Response sent back
       ↓
Frontend displays message
```

#### Example: Booking a Room

**Step 1: User clicks "Book Room"**
```javascript
// Frontend (index.html)
function selectOption('2') {
    showBookingWidget('book');  // Shows calendar widget
}
```

**Step 2: User selects dates and guests**
```javascript
submitBookingWidget() {
    message = "2 guests, Oct 15 to Oct 17";
    sendMessage();  // Sends to backend
}
```

**Step 3: Backend processes**
```python
# Backend (app.py line ~520)
@app.route('/api/chat', methods=['POST'])
def chat():
    message = request.json.get('message')
    session = conversation_sessions[session_id]
    
    # Detects: "X guests, Date to Date"
    has_guests = re.search(r'\d+\s*guest', message)
    has_dates = re.search(r'Oct|Nov|Dec...', message)
    
    if has_guests and has_dates:
        # Extract info
        num_guests = 2
        nights = calculate_nights(dates)
        
        # Get rooms from Amadeus API or static data
        if amadeus.is_configured():
            rooms = amadeus.search_hotels(dates, guests)
        else:
            rooms = static_rooms  # From hotel_data.json
        
        # Show rooms to user
        return jsonify({'message': formatted_room_list})
```

**Step 4: User selects room → Contact form → Booking confirmed**

---

### 2️⃣ **Voice Calling Flow**

#### Architecture:
```
User clicks "Call Support"
       ↓
Browser requests microphone permission
       ↓
Calling screen opens (full-screen overlay)
       ↓
AI speaks greeting (Web Speech Synthesis API)
       ↓
Recognition starts (Web Speech Recognition API)
       ↓
User speaks → Browser converts to text
       ↓
Text sent to Flask backend /api/chat
       ↓
Backend processes (same as text chat)
       ↓
Response sent back
       ↓
Browser speaks response (Text-to-Speech)
       ↓
Cycle repeats (natural conversation)
```

#### Detailed Voice Flow:

**Step 1: Opening Call Screen**
```javascript
// templates/index.html line ~1750
async function openCallScreen() {
    // Request microphone permission
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    
    // Create full-screen overlay
    overlay.innerHTML = `
        <div class="calling-screen">
            <div class="calling-avatar">🤖</div>
            <div class="calling-name">AI Assistant (Sarah)</div>
            <button onclick="manualPushToTalk()">🎤 Click & Speak</button>
        </div>
    `;
    
    // AI speaks first
    aiSpeakFirst();
}
```

**Step 2: AI Speaks Using Browser Text-to-Speech**
```javascript
// line ~1796
function aiSpeakFirst() {
    const greeting = "Hello! I'm Sarah...";
    
    // Browser's Speech Synthesis API
    const utterance = new SpeechSynthesisUtterance(greeting);
    utterance.rate = 1.1;  // Speed
    utterance.pitch = 1.1;  // Tone
    utterance.voice = femaleVoice;  // Voice selection
    
    utterance.onend = () => {
        // When AI finishes, start listening
        listenForUser();
    };
    
    synthesis.speak(utterance);  // Browser speaks!
}
```

**Step 3: User Speaks (Manual Button)**
```javascript
// line ~2295
function manualPushToTalk() {
    // Create speech recognition instance
    const SpeechRecognition = window.webkitSpeechRecognition;
    recognition = new SpeechRecognition();
    recognition.continuous = false;  // Single utterance
    recognition.interimResults = true;  // Show partial results
    recognition.lang = 'en-US';
    
    // Event: Recognition starts
    recognition.onstart = () => {
        console.log('✅ MIC ACTIVE!');
        // Button turns RED
    };
    
    // Event: Sound detected
    recognition.onsoundstart = () => {
        console.log('🔊 SOUND DETECTED!');
    };
    
    // Event: Speech detected
    recognition.onspeechstart = () => {
        console.log('🗣️ SPEECH DETECTED!');
    };
    
    // Event: Got transcript
    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        
        if (event.results[0].isFinal) {
            console.log('📝 FINAL:', transcript);
            // User said: "I need a room for 2 guests"
        } else {
            console.log('🔄 Interim:', transcript);
            // Shows: "I", "I need", "I need a", etc.
        }
    };
    
    // Event: Recognition ends
    recognition.onend = async () => {
        // Send transcript to backend
        await getAIResponse(transcript);
    };
    
    // Start listening
    recognition.start();
}
```

**Step 4: Send to Backend**
```javascript
// line ~1941
async function getAIResponse(userMessage) {
    // Call Flask API
    const response = await fetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ 
            message: userMessage,  // "I need a room for 2 guests"
            session_id: sessionId  // Track conversation
        })
    });
    
    const data = await response.json();
    const aiResponse = data.message;
    
    // AI speaks the response
    const utterance = new SpeechSynthesisUtterance(aiResponse);
    synthesis.speak(utterance);
    
    // After speaking, listen again
    utterance.onend = () => {
        listenForUser();  // Continue conversation
    };
}
```

---

### 3️⃣ **Amadeus API Integration (Real Hotel Data)**

#### How It Works:
```
User searches for rooms
       ↓
Frontend sends: dates, guests, location
       ↓
Backend checks: Is Amadeus configured?
       ↓
YES → Call Amadeus API
       ↓
Amadeus returns real hotels near Charlotte Airport
       ↓
Backend formats data to match our structure
       ↓
Shows real hotels with live pricing
       ↓
NO → Use static demo data from hotel_data.json
```

#### Code Flow:
```python
# app.py line ~116
# When user provides guests and dates

# Try Amadeus API
amadeus = get_amadeus_api()

if amadeus.is_configured():
    try:
        # Call Amadeus API
        rooms = amadeus.search_charlotte_airport_hotels(
            check_in='2025-10-15',
            check_out='2025-10-17', 
            guests=2
        )
        # Returns: real hotels from Amadeus database
    except Exception:
        # API failed, use static data
        rooms = agent.data['rooms']
else:
    # Not configured, use static data
    rooms = agent.data['rooms']
```

**Amadeus API Request:**
```python
# amadeus_integration.py line ~132
def search_charlotte_airport_hotels(check_in, check_out, guests):
    # Step 1: Get access token (OAuth)
    token = self._get_access_token()
    
    # Step 2: Search hotels by city
    hotels = self.search_hotels_by_city("CLT", radius=5)
    # CLT = Charlotte airport code
    
    # Step 3: Get pricing for those hotels
    offers = self.get_hotel_offers(
        hotel_ids=['HOTEL123', 'HOTEL456'],
        check_in=check_in,
        check_out=check_out,
        adults=guests
    )
    
    # Step 4: Format to our structure
    formatted_rooms = []
    for offer in offers:
        formatted_rooms.append({
            'type': offer['room']['type'],
            'price_per_night': offer['price']['total'],
            'hotel_name': offer['hotel']['name'],
            'source': 'amadeus'  # Mark as real data
        })
    
    return formatted_rooms
```

---

### 4️⃣ **Session Management (Conversation Memory)**

The backend remembers where you are in the conversation:

```python
# app.py line ~59
conversation_sessions = {
    'session_abc123': {
        'step': 'awaiting_room_selection',  # Current state
        'booking_data': {
            'guests': 2,
            'nights': 3,
            'check_in': '2025-10-15',
            'check_out': '2025-10-18',
            'available_rooms': [...],  # Cached room list
            'room': {...}  # Selected room
        }
    }
}
```

#### State Machine:
```
1. None → User says "Book room"
2. awaiting_guests_dates → User enters "2 guests, Oct 15 to Oct 17"
3. awaiting_room_selection → Shows rooms, user picks "Queen"
4. awaiting_contact_details → Shows form, user fills it
5. Booking confirmed → Session cleared, back to None
```

---

## 🛠️ Key Technologies Explained

### 1. **Web Speech API** (Browser Built-in)

#### Speech Recognition (Speech-to-Text):
```javascript
const SpeechRecognition = window.webkitSpeechRecognition;
const recognition = new SpeechRecognition();

recognition.continuous = false;  // Stop after one utterance
recognition.interimResults = true;  // Show partial results
recognition.lang = 'en-US';  // Language

// Events:
recognition.onstart = () => { /* Mic active */ };
recognition.onsoundstart = () => { /* Sound detected */ };
recognition.onspeechstart = () => { /* Speech detected */ };
recognition.onresult = (event) => { 
    // Got transcript!
    const transcript = event.results[0][0].transcript;
    console.log('You said:', transcript);
};

recognition.start();  // Start listening
```

**How it works:**
1. Activates your microphone
2. Captures audio
3. Sends to browser's speech recognition service
4. Returns text transcript
5. Includes confidence score (how sure it is)

#### Speech Synthesis (Text-to-Speech):
```javascript
const synthesis = window.speechSynthesis;
const utterance = new SpeechSynthesisUtterance("Hello!");

utterance.rate = 1.1;  // Speed (0.1 to 10)
utterance.pitch = 1.0;  // Tone (0 to 2)
utterance.voice = femaleVoice;  // Voice selection

utterance.onend = () => { /* Finished speaking */ };

synthesis.speak(utterance);  // Browser speaks!
```

**How it works:**
1. Takes text string
2. Converts to audio using browser's TTS engine
3. Plays through speakers
4. Can select voice (male/female, accents)

### 2. **VAPI** (Professional Voice AI)

VAPI is an alternative to browser speech APIs:

**What it provides:**
- Professional voice quality (ElevenLabs voices)
- More reliable speech recognition
- Phone system integration
- Advanced AI (GPT-4)
- Function calling (AI can trigger actions)

**Why we use it:**
- Browser Speech API has limitations (Safari, permissions)
- VAPI works across all devices
- Better for production use
- Can handle real phone calls

**How it would work (if SDK loaded):**
```javascript
const vapi = new Vapi('your-api-key');

// Start call
await vapi.start({
    model: 'gpt-4',
    voice: 'rachel',  // Professional voice
    firstMessage: 'Hello! How can I help?',
    functions: [
        // AI can call these functions
        'check_availability',
        'create_booking',
        'transfer_to_agent'
    ]
});

// Listen for events
vapi.on('message', (msg) => {
    if (msg.type === 'transcript') {
        console.log('User said:', msg.transcript);
    }
    if (msg.type === 'function-call') {
        // AI wants to transfer to human
        transferToHuman();
    }
});
```

### 3. **Amadeus API** (Real Hotel Data)

**What it is:**
- Global hotel database
- Used by travel agencies worldwide
- Free tier: 2,000 API calls/month

**How it works:**
```python
# Step 1: Authenticate
response = requests.post('https://test.api.amadeus.com/v1/security/oauth2/token', {
    'client_id': AMADEUS_API_KEY,
    'client_secret': AMADEUS_API_SECRET
})
access_token = response.json()['access_token']

# Step 2: Search hotels
response = requests.get(
    'https://test.api.amadeus.com/v1/reference-data/locations/hotels/by-city',
    headers={'Authorization': f'Bearer {access_token}'},
    params={'cityCode': 'CLT', 'radius': 5}
)
hotels = response.json()['data']
# Returns: list of hotels near Charlotte Airport

# Step 3: Get pricing
response = requests.get(
    'https://test.api.amadeus.com/v1/shopping/hotel-offers',
    params={
        'hotelIds': 'HOTEL123,HOTEL456',
        'checkInDate': '2025-10-15',
        'checkOutDate': '2025-10-17',
        'adults': 2
    }
)
offers = response.json()['data']
# Returns: rooms with current pricing
```

---

## 🎨 Frontend Features Explained

### 1. **Interactive Booking Widget**

**Visual calendar date pickers:**
```html
<input type="date" id="checkInDate" min="2025-10-14">
```

Browser provides native calendar UI!

**Auto-calculate nights:**
```javascript
function calculateNights() {
    const checkIn = new Date(checkInDate.value);
    const checkOut = new Date(checkOutDate.value);
    const diffTime = checkOut - checkIn;
    const nights = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    // Returns: number of nights
}
```

### 2. **Room Selection Cards**

**Parsing room listings:**
```javascript
function extractRoomButtons(content) {
    // Content has format: "**Room Name** (Room #123)"
    const regex = /\*\*(.+?)\*\*\s*(?:\(Room #(\d+)\))?/;
    
    // Extract: room name, price, capacity, amenities
    rooms = [];
    for (each room in content) {
        rooms.push({
            name: "Queen Guest Room",
            price: "139",
            capacity: "2",
            amenities: ["WiFi", "TV", "Fridge"]
        });
    }
    
    // Create clickable cards
    rooms.forEach(room => {
        createCard(room);
    });
}
```

**Dynamic card creation:**
```javascript
// Creates beautiful cards with hover effects
const card = document.createElement('div');
card.style.border = '2px solid #e2e8f0';
card.onmouseover = () => {
    card.style.borderColor = '#0891b2';  // Blue on hover
    card.style.transform = 'translateY(-2px)';  // Lift up
};
```

### 3. **Payment Form**

**Auto-formatting card number:**
```javascript
function formatCardNumber(input) {
    let value = input.value.replace(/\s/g, '');  // Remove spaces
    // "1234567890123456"
    
    let formatted = value.match(/.{1,4}/g).join(' ');
    // "1234 5678 9012 3456"
    
    input.value = formatted;
}
```

**Security (masking):**
```javascript
const cardNumber = "1234 5678 9012 3456";
const digits = cardNumber.replace(/\s/g, '');  // "1234567890123456"
const masked = '****' + digits.slice(-4);  // "****3456"

// Only send masked version to server!
sendToBackend(masked);  // Never send full card number
```

---

## 🤖 How AI Works

### Option A: Rule-Based (Default)

**Intent detection with regex:**
```python
# hotel_agent.py line ~91
def _detect_intent_rule_based(message):
    message_lower = message.lower()
    
    # Check availability
    if 'available' in message_lower or 'check' in message_lower:
        return 'check_availability', {}
    
    # Book room
    if 'book' in message_lower or 'reserve' in message_lower:
        return 'book_room', {}
    
    # Extract entities with regex
    guest_match = re.search(r'(\d+)\s*guest', message_lower)
    if guest_match:
        entities['guests'] = int(guest_match.group(1))
    
    return intent, entities
```

### Option B: LLM-Based (Advanced)

**Using OpenAI GPT:**
```python
# hotel_agent.py line ~209
def _detect_intent_llm(message, api_key):
    client = OpenAI(api_key=api_key)
    
    prompt = f"""
    Analyze this message: "{message}"
    Extract intent and entities.
    Return JSON: {{"intent": "...", "entities": {{...}}}}
    """
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    result = json.loads(response.choices[0].message.content)
    # AI understands: intent=book_room, entities={guests:2, dates:[...]}
    
    return result['intent'], result['entities']
```

---

## 🔄 Transfer to Human Logic

### Detection:
```python
# app.py VAPI configuration line ~900
system_prompt = """
WHEN TO TRANSFER:
1. User asks for human/person
2. Complex requests (group bookings)
3. User frustrated
4. Payment issues
5. Can't understand after 2-3 attempts
"""
```

**Frontend detection:**
```javascript
// If user says these phrases
const shouldTransfer = 
    userMessage.includes('speak to a person') ||
    userMessage.includes('human agent') ||
    userMessage.includes('talk to someone');

if (shouldTransfer) {
    transferToHumanAgent();
}
```

**Transfer simulation:**
```javascript
function transferToHumanAgent() {
    // Show transfer message
    updateStatus('📞 Transferring...');
    
    // Wait 2 seconds (simulates hold music)
    setTimeout(() => {
        // Change avatar and name
        avatar.textContent = '👤';
        name.textContent = 'Human Agent (Michael)';
        
        // Human speaks
        speak("Hello! I'm a human customer support agent...");
    }, 2000);
}
```

---

## 📊 Data Flow Diagrams

### Booking Flow:
```
┌─────────────┐
│ User clicks │
│ "Book Room" │
└──────┬──────┘
       ↓
┌──────────────────┐
│ Booking Widget   │
│ Dates + Guests   │
└──────┬───────────┘
       ↓
┌──────────────────┐
│ POST /api/chat   │
│ "2 guests, Oct15"│
└──────┬───────────┘
       ↓
┌──────────────────────┐
│ Backend detects:     │
│ - Extract: 2 guests  │
│ - Extract: dates     │
│ - Calculate: nights  │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Get rooms:           │
│ - Try Amadeus API    │
│ - Fallback: static   │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Show room cards      │
│ with Select buttons  │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ User clicks room     │
│ → Show contact form  │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ User fills form:     │
│ Name, Phone, Email   │
│ Card details         │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Backend creates      │
│ booking in JSON file │
└──────┬───────────────┘
       ↓
┌──────────────────────┐
│ Show confirmation    │
│ with booking ID      │
└───────────────────────┘
```

### Voice Call Flow:
```
┌─────────────────┐
│ User clicks     │
│ "Call Support"  │
└────────┬────────┘
         ↓
┌─────────────────┐
│ Request mic     │
│ permission      │
└────────┬────────┘
         ↓
┌─────────────────────┐
│ Open calling screen │
│ (full-screen UI)    │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ AI speaks greeting  │
│ (Text-to-Speech)    │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ Start listening     │
│ (Speech-to-Text)    │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ User speaks         │
│ → Transcript shown  │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ Send to /api/chat   │
│ (same as text chat) │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ AI responds         │
│ → Speaks response   │
└────────┬────────────┘
         ↓
┌─────────────────────┐
│ Listen again        │
│ (conversation loop) │
└─────────────────────┘
```

---

## 🔐 Security Features

### 1. **Payment Card Masking**
```javascript
const cardNumber = "1234567890123456";
const last4 = cardNumber.slice(-4);  // "3456"
const masked = "****" + last4;  // "****3456"

// NEVER send full number to server
sendToServer({ payment: masked });
```

### 2. **Session Isolation**
```python
# Each user gets unique session ID
session_id = 'session_' + timestamp + '_' + random_string
conversation_sessions[session_id] = {...}
# Prevents mixing up different users' data
```

### 3. **Input Validation**
```javascript
// Email validation
if (!email.includes('@')) {
    alert('Invalid email');
    return;
}

// Card validation
if (cardDigits.length < 13 || cardDigits.length > 19) {
    alert('Invalid card number');
    return;
}
```

---

## 📁 File Structure & Responsibilities

```
hotel agent/
├── app.py                    # 🖥️ Flask server, API endpoints
├── hotel_agent.py            # 🧠 Business logic, intent detection
├── hotel_data.json           # 💾 Database (rooms, bookings)
├── amadeus_integration.py    # 🌐 Real hotel API integration
├── vapi_integration.py       # 📞 Voice AI integration
├── templates/
│   └── index.html            # 🎨 Frontend UI, JavaScript
└── static/                   # 📦 Static assets (if any)
```

**app.py** (1,452 lines):
- Flask web server
- API endpoints (/api/chat, /api/rooms, etc.)
- Session management
- VAPI webhooks
- Amadeus integration calls

**hotel_agent.py** (455 lines):
- Intent detection (what user wants)
- Response generation
- Booking logic
- Data access

**index.html** (2,474 lines):
- User interface
- Voice calling screen
- Booking widgets
- Room cards
- Payment forms
- All JavaScript logic

**amadeus_integration.py** (227 lines):
- Amadeus API client
- Hotel search
- Pricing lookups
- Data formatting

**vapi_integration.py** (370 lines):
- VAPI API client
- Assistant configuration
- Call management
- Function definitions

---

## 🎯 Complete User Journey Example

### Scenario: Voice Booking

**1. User clicks "Call Support"**
```
Frontend: openCallScreen()
Browser: Request microphone → User allows
Frontend: Creates calling UI overlay
Frontend: aiSpeakFirst()
Browser TTS: "Hello! I'm Sarah..."
```

**2. AI finishes speaking**
```
Browser TTS: onend event fires
Frontend: listenForUser()
Browser STT: recognition.start()
Screen: "🎤 CLICK ME TO SPEAK" (button appears)
```

**3. User clicks button and speaks**
```
User: *clicks button*
Frontend: manualPushToTalk()
Frontend: Creates fresh SpeechRecognition
Browser STT: recognition.start()
Browser STT: onstart → "✅ MIC ACTIVE!"
User: "I need a room for 2 guests"
Browser STT: onsoundstart → "🔊 SOUND DETECTED!"
Browser STT: onspeechstart → "🗣️ SPEECH DETECTED!"
Browser STT: onresult (interim) → "🔄 I"
Browser STT: onresult (interim) → "🔄 I need"
Browser STT: onresult (interim) → "🔄 I need a"
Browser STT: onresult (interim) → "🔄 I need a room"
Browser STT: onresult (final) → "📝 I need a room for 2 guests"
```

**4. Send to backend**
```
Frontend: getAIResponse("I need a room for 2 guests")
Frontend: fetch('/api/chat', {message: "I need a room for 2 guests"})
Backend: Receives message
Backend: Session step = 'awaiting_guests_dates'
Backend: Parses: guests=2
Backend: Gets rooms from Amadeus or static data
Backend: Formats response with room list
Backend: Returns: "Perfect! For 2 guests, here are options..."
```

**5. AI speaks response**
```
Frontend: Receives response
Frontend: Clean markdown: "Perfect! For 2 guests..."
Frontend: utterance = new SpeechSynthesisUtterance(response)
Browser TTS: Speaks the response
Frontend: Shows in transcript
Browser TTS: onend → listenForUser() again
```

**6. Conversation continues**
```
AI: "Which room would you like?"
User: *clicks button* "Queen room"
Backend: Recognizes "queen", finds room
Backend: Shows contact form
User: Fills form
Backend: Creates booking
AI: "Booking confirmed! Your confirmation number is BK0007"
```

---

## 🚀 Why Your Browser Uses Manual Button

### Browser Limitations:

**Chrome:** ✅ Auto-start works  
**Safari (macOS):** ❌ Requires user gesture (click)  
**Firefox:** ⚠️ Limited support  

**Your browser (likely Safari):**
- `recognition.start()` is called ✅
- But `onstart` event never fires ❌
- This is a browser security feature
- Prevents websites from auto-activating microphone
- **Solution:** User must click a button (user gesture)

**Why manual button works:**
```javascript
// When user clicks button:
onclick="manualPushToTalk()"
       ↓
recognition.start()  // Called from user gesture
       ↓
Browser allows it! ✅
       ↓
onstart event fires
       ↓
Microphone activates
```

---

## 🎓 Summary

**What you built:**
1. **Smart chatbot** with conversation memory
2. **Interactive booking** with calendars and forms
3. **Voice AI** that speaks and listens
4. **Human transfer** system (simulated)
5. **Real hotel data** integration (Amadeus)
6. **Payment processing** with security

**Technologies used:**
- **Flask** (Python web framework)
- **Web Speech API** (browser voice)
- **VAPI** (professional voice AI)
- **Amadeus API** (hotel database)
- **JSON** (data storage)
- **JavaScript** (frontend logic)
- **CSS3** (animations, styling)

**How it works:**
- Text chat → User types → Backend processes → Shows response
- Voice call → User speaks → Browser converts to text → Backend processes → AI speaks response
- Booking → Widget → Form → Backend creates record → Confirmation

**The magic:** All integrated seamlessly into one beautiful interface! 🎉

Would you like me to explain any specific part in more detail?



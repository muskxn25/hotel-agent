# Hotel Agent - AI-Powered Voice Booking System

An intelligent hotel booking system that uses VAPI (Voice AI) to handle phone calls and provide seamless room booking experiences. The system integrates with Amadeus API for real-time hotel data and provides a complete voice-based booking solution.

## 🏨 Features

- **Voice AI Integration**: Powered by VAPI for natural phone conversations
- **Real-time Hotel Data**: Integration with Amadeus API for live availability
- **Intelligent Booking Flow**: Guided conversation with date options and room selection
- **Multiple Interfaces**: Voice calls, web chat, and CLI interface
- **Static Data Fallback**: Uses local hotel data when APIs are unavailable
- **Performance Optimized**: Fast responses with GPT-4o-mini and optimized prompts

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- VAPI API key
- Amadeus API credentials (optional)
- ngrok for webhook tunneling

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd hotel-agent
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.template .env
   # Edit .env with your API keys
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

## 📋 Configuration

### Required Environment Variables

Create a `.env` file with the following variables:

```env
# VAPI Configuration
VAPI_API_KEY=your_vapi_api_key_here

# Amadeus API (Optional)
AMADEUS_API_KEY=your_amadeus_api_key
AMADEUS_API_SECRET=your_amadeus_api_secret

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=True
```

### VAPI Setup

1. Create a VAPI account at [vapi.ai](https://vapi.ai)
2. Get your API key from the dashboard
3. Create a phone number in VAPI
4. Set the webhook URL to: `https://your-ngrok-url.ngrok-free.dev/api/vapi/webhook`

### Amadeus Setup (Optional)

1. Sign up at [Amadeus for Developers](https://developers.amadeus.com)
2. Create a new project and get API credentials
3. Add credentials to your `.env` file

## 🎯 Usage

### Voice Calls

1. **Start ngrok** (in a separate terminal):
   ```bash
   ngrok http 5000
   ```

2. **Update VAPI webhook** with your ngrok URL

3. **Call your VAPI number** and experience the AI booking agent!

### Web Interface

1. **Start the Flask app**:
   ```bash
   python app.py
   ```

2. **Open browser** to `http://localhost:5000`

3. **Chat with the AI** for hotel bookings

### CLI Interface

```bash
python hotel_agent.py
```

## 🏗️ Architecture

```
hotel-agent/
├── app.py                 # Main Flask application
├── hotel_agent.py         # Core AI agent logic
├── vapi_integration.py    # VAPI API integration
├── amadeus_integration.py # Amadeus API integration
├── hotel_data.json       # Static hotel data fallback
├── templates/
│   └── index.html        # Web interface
├── static/               # Static assets
└── requirements.txt     # Python dependencies
```

## 🔧 API Endpoints

### Web Interface
- `GET /` - Main chat interface
- `POST /api/chat` - Chat with AI agent

### VAPI Integration
- `POST /api/vapi/webhook` - VAPI webhook handler
- `GET /api/vapi/sessions` - Get call sessions

### Amadeus Integration
- `POST /api/amadeus/search` - Search hotels
- `GET /api/amadeus/status` - Check API status

## 🎙️ Voice AI Features

- **Natural Conversations**: Powered by GPT-4o-mini for fast, natural responses
- **Guided Booking Flow**: Offers date options and room selections
- **Function Calling**: Automatically calls booking functions when needed
- **Performance Optimized**: Low latency with optimized prompts and settings
- **Error Handling**: Graceful fallbacks and error recovery

## 📊 Hotel Data

The system uses **Hyatt House Charlotte Airport** as the primary hotel with:

- **Address**: 4920 South Tryon Street, Charlotte, NC
- **Amenities**: Free WiFi, fitness center, indoor pool, free parking, airport shuttle, breakfast
- **Room Types**: Studio King, One-Bedroom Suite, Two-Queen, Executive King
- **Policies**: Check-in 3:00 PM, Check-out 12:00 PM

## 🔄 Booking Flow

1. **Greeting**: AI introduces itself as Sarah from front desk
2. **Name Collection**: Gets caller's name
3. **Service Inquiry**: Asks how it can help
4. **Date Options**: Offers specific date ranges for booking
5. **Guest Count**: Asks for number of guests
6. **Room Search**: Calls `check_room_availability` function
7. **Room Selection**: Presents available rooms with prices
8. **Booking Confirmation**: Creates reservation if requested

## 🛠️ Development

### Running Tests

```bash
python -m pytest tests/
```

### Code Style

```bash
black .
flake8 .
```

### Adding New Features

1. **New Functions**: Add to `_get_functions()` in `vapi_integration.py`
2. **New Handlers**: Add to `handle_vapi_function_call()` in `app.py`
3. **New Prompts**: Update `_get_system_prompt()` in `vapi_integration.py`

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

For support and questions:
- Create an issue in this repository
- Check the documentation in the `/docs` folder
- Review the setup guides in the root directory

## 🎉 Acknowledgments

- [VAPI](https://vapi.ai) for voice AI capabilities
- [Amadeus](https://developers.amadeus.com) for hotel data API
- [OpenAI](https://openai.com) for GPT models
- [Flask](https://flask.palletsprojects.com) for web framework

---

**Made with ❤️ for seamless hotel booking experiences**
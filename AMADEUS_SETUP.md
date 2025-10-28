# Amadeus Hotel API Setup Guide

Get **REAL hotel data** from 150,000+ properties worldwide with Amadeus API!

## 🎁 **Why Amadeus?**

- ✅ **FREE** developer account (2,000 API calls/month)
- ✅ **Self-service** - Get keys in 5 minutes
- ✅ **Real data** - Actual hotels, prices, availability
- ✅ **150,000+ hotels** worldwide
- ✅ **No partnership** required
- ✅ **Easy integration** - Just 2 API keys needed

---

## 📋 **Quick Setup (5 Minutes)**

### **Step 1: Create Amadeus Account**

1. Go to **https://developers.amadeus.com**
2. Click **"Register"** or **"Get Started"**
3. Fill in your details:
   - Email
   - Company/Project name (can be "Personal Project")
   - Create password
4. **Verify your email**

### **Step 2: Get API Keys**

1. **Log in** to https://developers.amadeus.com
2. Go to **"My Self-Service Workspace"**
3. Create a new app:
   - Click **"Create New App"**
   - Name it: "Hotel Front Desk Agent"
   - Click **"Create"**
4. You'll see your credentials:
   - **API Key** (Client ID)
   - **API Secret** (Client Secret)
5. **Copy both values!**

### **Step 3: Configure Your Project**

Update your `.env` file:

```bash
# Copy the template if you haven't
cp env.template .env

# Edit .env and add your Amadeus credentials:
AMADEUS_API_KEY=your_api_key_here
AMADEUS_API_SECRET=your_api_secret_here
```

### **Step 4: Install Dependencies**

```bash
cd "/Users/muskxn25/hotel agent"
source venv/bin/activate
pip install -r requirements.txt
```

### **Step 5: Test the Integration**

```bash
# Restart the server
# The server should reload automatically if running

# Test Amadeus connection
curl http://localhost:5000/api/amadeus/status
```

You should see:
```json
{
  "configured": true,
  "authenticated": true,
  "message": "Amadeus API ready to use!"
}
```

---

## 🚀 **Using Real Hotel Data**

### **Option 1: Automatic (In Booking Flow)**

When users book, the system can optionally fetch real data:

```bash
# The booking flow will automatically use Amadeus if configured
# Just use the web interface normally!
```

### **Option 2: Manual Search**

Search for real hotels via API:

```bash
curl -X POST http://localhost:5000/api/amadeus/search \
  -H "Content-Type: application/json" \
  -d '{
    "city_code": "CLT",
    "check_in": "2025-10-15",
    "check_out": "2025-10-17",
    "guests": 2
  }'
```

**City Codes:**
- CLT = Charlotte, NC
- NYC = New York City
- LAX = Los Angeles
- MIA = Miami
- CHI = Chicago
- LAS = Las Vegas

### **Option 3: Hybrid Mode**

The system intelligently uses:
- **Amadeus data** when configured (real prices)
- **Static data** as fallback (always works)

---

## 📊 **What You Get from Amadeus:**

### **Real Data:**
- ✅ Actual hotel names
- ✅ Real-time availability
- ✅ Current pricing (in USD, EUR, etc.)
- ✅ Room descriptions
- ✅ Amenities
- ✅ Hotel addresses
- ✅ Distance from landmarks

### **Example Response:**
```json
{
  "hotel_name": "Hilton Charlotte Airport",
  "type": "Superior King Room",
  "price_per_night": 159.00,
  "currency": "USD",
  "amenities": ["Free WiFi", "Flat-screen TV", "King bed"],
  "available": true
}
```

---

## 🔄 **Updating the Booking Flow**

Once Amadeus is configured, you can update `app.py` to:

### **1. Use Real Data in Booking**

Modify the `awaiting_guests_dates` step to fetch from Amadeus:

```python
# Instead of using static rooms
available_rooms = [r for r in agent.data['rooms'] if r['available']]

# Use Amadeus
amadeus = get_amadeus_api()
if amadeus.is_configured():
    available_rooms = amadeus.search_charlotte_airport_hotels(
        check_in=session['booking_data']['check_in'],
        check_out=session['booking_data']['check_out'],
        guests=num_guests
    )
else:
    # Fallback to static
    available_rooms = [r for r in agent.data['rooms'] if r['available']]
```

---

## 💰 **Pricing & Limits**

### **Free Tier (Self-Service)**
- **Cost:** $0/month
- **API Calls:** 2,000/month
- **Rate Limit:** 10 calls/second
- **Perfect for:** Demos, testing, MVPs

### **Production Tier**
- **Cost:** Pay as you go
- **API Calls:** Unlimited
- **Rate Limit:** Higher
- **For:** Live applications

---

## 🧪 **Testing Amadeus Integration**

### **Test 1: Check Status**
```bash
curl http://localhost:5000/api/amadeus/status
```

Expected: `"authenticated": true`

### **Test 2: Search Hotels**
```bash
curl -X POST http://localhost:5000/api/amadeus/search \
  -H "Content-Type: application/json" \
  -d '{
    "city_code": "CLT",
    "guests": 2
  }'
```

Expected: List of real hotels with prices

### **Test 3: Use in Web Interface**

1. Open http://localhost:5000
2. Click "1. Check Rooms"
3. If Amadeus is configured, you'll see real hotel data!

---

## 🎯 **Current vs With Amadeus**

| Feature | Static Data | With Amadeus API |
|---------|-------------|------------------|
| **Availability** | Fake | ✅ Real-time |
| **Pricing** | Estimated | ✅ Actual prices |
| **Hotels** | 1 hotel | ✅ 100+ hotels |
| **Data Freshness** | Manual update | ✅ Live data |
| **API Calls** | 0 | 2,000/month free |
| **Reliability** | 100% | 99%+ (with fallback) |

---

## 🔧 **Troubleshooting**

### **Issue: "Amadeus API not configured"**

**Solution:**
1. Make sure `.env` file exists
2. Add `AMADEUS_API_KEY` and `AMADEUS_API_SECRET`
3. Restart server

### **Issue: "Authentication failed"**

**Solutions:**
1. Check API keys are correct (no extra spaces)
2. Verify you're using **Self-Service** keys (not production)
3. Check your Amadeus account is active

### **Issue: "No hotels found"**

**Solutions:**
1. Try a different city code
2. Adjust search radius
3. Check date format (YYYY-MM-DD)

### **Issue: API quota exceeded**

**Solutions:**
1. You've used 2,000 calls this month
2. Wait until next month
3. System automatically falls back to static data
4. Upgrade to paid tier if needed

---

## 📚 **Amadeus API Documentation**

- **Main Docs:** https://developers.amadeus.com/self-service
- **Hotel APIs:** https://developers.amadeus.com/self-service/category/hotels
- **Guides:** https://developers.amadeus.com/get-started/get-started-with-self-service-apis-335
- **Support:** https://developers.amadeus.com/support

---

## 🎨 **Integration Options**

### **Option A: Hybrid (Recommended)**
- Use Amadeus when available
- Fallback to static data
- Best of both worlds!

### **Option B: Amadeus Only**
- Always use real data
- Requires API keys
- More realistic

### **Option C: Static Only (Current)**
- No API needed
- Always works
- Easy to customize

---

## ✅ **Next Steps**

1. ✅ Sign up at https://developers.amadeus.com
2. ✅ Get your API keys
3. ✅ Add to `.env` file
4. ✅ Restart server
5. ✅ Test with: `curl http://localhost:5000/api/amadeus/status`
6. ✅ See real hotel data in your app!

---

## 🎉 **Benefits of Using Amadeus**

- **More Realistic Demo** - Show actual hotel prices
- **Multiple Hotels** - Not just one hotel
- **Real Inventory** - Live availability
- **Professional** - Enterprise-grade data
- **Free** - Perfect for demos and testing

---

**Ready to get real hotel data? Follow the steps above!** 🚀

**Or keep using static data - both work great!**


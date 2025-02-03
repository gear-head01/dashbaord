import streamlit as st
import pandas as pd
import plotly.express as px
import random
import groq
import requests
from streamlit_option_menu import option_menu
import geocoder
from PIL import Image

# Load the API key from Streamlit secrets
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
THINGSPEAK_WRITE_API_KEY = 'BKM8V6DFW6E87UYQ'
THINGSPEAK_CHANNEL_ID = '2686081'

# Initialize Groq Client
client = groq.Client(api_key=GROQ_API_KEY)

# Function to get AI-based recommendations
def get_recommendation(location, soil_type, crop_type):
    prompt = f"""
    Based on the given conditions:
    - Location: {location}
    - Soil Type: {soil_type}
    - Crop Type: {crop_type}

    Suggest the best irrigation practices, fertilizers, and water management.
    """
    response = client.chat.completions.create(
        model="mixtral-8x7b-32768",  # Groq AI Model
        messages=[
            {"role": "system", "content": "You are an expert in precision agriculture."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content

# Function to generate fake sensor data
def generate_data():
    return {
        "Timestamp": pd.date_range(start="2025-02-03", periods=20, freq="S"),
        "Soil Moisture": [random.randint(20, 80) for _ in range(20)],
        "Temperature": [random.randint(15, 40) for _ in range(20)],
        "Humidity": [random.randint(30, 90) for _ in range(20)],
        "Water Flow": [random.randint(10, 50) for _ in range(20)],
        "pH Level": [round(random.uniform(5.5, 8.5), 2) for _ in range(20)],
    }

# Function to fetch weather data from Open-Meteo API
def get_weather_data(latitude, longitude):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&hourly=temperature_2m"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['hourly']['temperature_2m'][0]  # Latest temperature value
    else:
        st.error("Failed to fetch weather data.")
        return None

# Function to fetch user location using geo-location API
def get_user_location():
    g = geocoder.ip('me')
    return g.latlng

# Function to send data to ThingSpeak
def send_to_thingspeak(moisture_status):
    url = f"https://api.thingspeak.com/update?api_key={THINGSPEAK_WRITE_API_KEY}&field2={moisture_status}"
    response = requests.get(url)
    if response.status_code == 200:
        return "Data sent successfully to ThingSpeak."
    else:
        return "Failed to send data to ThingSpeak."

# Authentication System
def login():
    st.sidebar.subheader("Login")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login"):
        # Simple check for demo purposes
        if username == "admin" and password == "password":
            st.session_state["authenticated"] = True
            st.success("Login successful!")
            st.experimental_rerun()  # Refresh the app to display authenticated content
        else:
            st.sidebar.error("Invalid credentials! Please try again.")

# Language Selection (English/Tamil)
def change_language():
    language = st.sidebar.selectbox("Select Language", ["English", "தமிழ்"])
    return language

# Function to handle chatbot interaction
def chatbot():
    st.subheader("🤖 Chat with Agriculture Bot")
    user_message = st.text_input("You:", "")
    
    if st.button("Send"):
        if user_message:
            # Get response from Groq chatbot
            response = client.chat.completions.create(
                model="mixtral-8x7b-32768",  # Groq AI Model
                messages=[
                    {"role": "system", "content": "You are an expert in precision agriculture."},
                    {"role": "user", "content": user_message}
                ]
            )
            st.text_area("Bot:", response.choices[0].message.content, height=200)
        else:
            st.error("Please enter a message.")

# Resizing images using PIL
login_image = Image.open("logo.jpg")  # Ensure you have an image file in your project folder
dashboard_image = Image.open("logo.jpg")  # Ensure you have an image file for the dashboard

# Resize images using PIL
login_image = login_image.resize((600, 400))
dashboard_image = dashboard_image.resize((600, 400))

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    login()
else:
    # Display the login image at the login page with custom width and height
    st.image(login_image)

    # Sidebar Menu
    with st.sidebar:
        selected = option_menu("Smart Irrigation Dashboard", 
                               ["AI Recommendation", "Dashboard", "Reports", "Chatbot", "Settings", "Logout"],
                               icons=["lightbulb", "bar-chart", "file-earmark-text", "chat", "gear", "box-arrow-right"],
                               menu_icon="menu-hamburger", default_index=0)
    
    if selected == "Logout":
        st.session_state["authenticated"] = False
        st.experimental_rerun()

    # Get User's Location
    user_location = get_user_location()

    # AI-Based Recommendation System
    if selected == "AI Recommendation":
        language = change_language()
        if language == "English":
            st.title("🤖 AI-Based Smart Irrigation Suggestions")
        else:
            st.title("🤖 ஸ்மார்ட் ஆர்ிகேஷன் பரிந்துரைகள்")

        location = st.selectbox("📍 Select Your Location", ["Region A", "Region B", "Region C"])
        soil_type = st.selectbox("🌱 Select Soil Type", ["Clay", "Sandy", "Loamy"])
        crop_type = st.selectbox("🌾 Select Crop Type", ["Wheat", "Rice", "Corn"])

        if st.button("🔍 Get Recommendation"):
            with st.spinner("AI is analyzing your inputs..."):
                suggestion = get_recommendation(location, soil_type, crop_type)
            st.write("### 🌟 AI Recommendation: ")
            st.success(suggestion)

    # Dashboard
    elif selected == "Dashboard":
        st.image(dashboard_image)
        st.title("🌾 Smart Irrigation System Dashboard")

        # Fetch weather data from Open-Meteo API (Example coordinates for location)
        latitude, longitude = user_location
        weather_temp = get_weather_data(latitude, longitude)

        # Generate fake data
        data = pd.DataFrame(generate_data())

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("🌡️ Temperature (°C)", f"{weather_temp} (Real-time)")
            st.progress(int(weather_temp))

        with col2:
            st.metric("💧 Soil Moisture (%)", f"{data['Soil Moisture'].iloc[-1]}")
            st.progress(int(data['Soil Moisture'].iloc[-1]))

        with col3:
            st.metric("🌫️ Humidity (%)", f"{data['Humidity'].iloc[-1]}")
            st.progress(int(data['Humidity'].iloc[-1]))

        # Line Chart for Real-time Data
        fig = px.line(data, x="Timestamp", y=["Soil Moisture", "Temperature", "Humidity"], markers=True)
        st.plotly_chart(fig, use_container_width=True)

        # More Widgets
        st.slider("Adjust Water Flow Rate", min_value=10, max_value=50, value=20)
        st.checkbox("Enable Automatic Irrigation")
        st.date_input("📅 Schedule Next Irrigation")

    # Reports
    elif selected == "Reports":
        st.title("📊 Sensor Data Reports")
        st.dataframe(data)
        st.download_button(label="📥 Download Data as CSV", data=data.to_csv(), file_name="sensor_data.csv", mime="text/csv")

    # Chatbot
    elif selected == "Chatbot":
        chatbot()

    # Settings
    elif selected == "Settings":
        st.title("⚙️ Settings")
        auto_irrigation = st.checkbox("Enable Auto Irrigation")
        moisture_threshold = st.slider("Set Soil Moisture Threshold", min_value=10, max_value=80, value=40)
        st.write(f"Auto Irrigation is {'Enabled' if auto_irrigation else 'Disabled'}. Moisture threshold is set to {moisture_threshold}%.")
        send_to_thingspeak(50)  # Example of sending data to ThingSpeak

        # Language button
        language = change_language()
        if language == "English":
            st.write("You are viewing the English version.")
        else:
            st.write("நீங்கள் தமிழ் பதிப்பை பார்க்கிறீர்கள்.")

    # Chatbot button at the right corner
    chatbot_button = st.button("🗨️ Chat", key="chatbot_button")
    if chatbot_button:
        chatbot()

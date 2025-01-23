from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import inflect

app = Flask(__name__)

# Hugging Face API Configuration
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
HEADERS = {"Authorization": f"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"}

# Load car data from cars.json
with open('data/cars.json') as f:
    car_data = json.load(f)

# Appointment data structure
appointments = []
appointment_in_progress = False  # Flag to track appointment scheduling

def query_huggingface(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# Route for Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Function to convert numbers to words, specifically handling Indian numbers
def convert_to_indian_words(number):
    p = inflect.engine()

    # Handling special case for 'lakh' and 'crore'
    if number >= 100000:
        lakhs = number // 100000
        if lakhs == 1:
            return f"{lakhs} lakh"
        else:
            return f"{lakhs} lakhs"
    else:
        return p.number_to_words(number).replace(",", "")

def clean_price(price):
    """Fixes encoding issues and formats the price correctly."""
    # Remove any unwanted characters (like â‚¹) and ensure proper rupee symbol
    return price.replace("â‚¹", "₹").replace(",", "")

@app.route('/chat', methods=['POST'])
def chat():
    global appointment_in_progress
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message received"}), 400

    # Check if the user is trying to book an appointment
    if "book appointment" in user_message.lower():
        appointment_in_progress = True
        return jsonify({
            "reply": "Sure! Please select the date and time for your appointment using the form below."
        })

    # Check if the user is asking about a specific car
    for car in car_data:
        if car['name'].lower() in user_message.lower():
            competitors = ''
            for comp in car['competitors']:
                # Clean competitor price and convert to words
                competitor_price = clean_price(comp['price'])
                competitor_numeric_price = int(competitor_price.replace("₹", ""))  # Remove ₹ for numeric value
                competitor_price_in_words = convert_to_indian_words(competitor_numeric_price)
                
                competitors += f"{comp['name']} is priced at {competitor_price_in_words}, features: {comp['features']}. "

            # Fix price and convert number to words for the main car
            price = clean_price(car['price'])
            numeric_price = int(price.replace("₹", "").replace(",", ""))  # Remove ₹ and commas for numeric value
            price_in_words = convert_to_indian_words(numeric_price)

            return jsonify({
                "reply": f"The {car['name']} is priced at {price_in_words}. Details: {car['details']}. Competitors: {competitors}"
            })

    # Default Chatbot behavior (fallback to Hugging Face)
    try:
        payload = {"inputs": user_message}
        response = query_huggingface(payload)
        bot_reply = response.get('generated_text', "I'm sorry, I couldn't process that.")
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route for confirming appointment
@app.route('/confirm_appointment', methods=['POST'])
def confirm_appointment():
    try:
        data = request.json
        date = data.get('date')
        time = data.get('time')
        appointment_time = f"{date} {time}:00"

        # Convert to datetime object
        appointment_datetime = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M:%S")
        appointments.append({
            "appointment_time": appointment_datetime,
        })
        global appointment_in_progress
        appointment_in_progress = False  # Reset the flag
        return jsonify({"reply": "Thank you and we are excited to see you in your dream car"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

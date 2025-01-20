from flask import Flask, render_template, request, jsonify
import requests
import json
from datetime import datetime
import os
API_KEY = os.getenv("HUGGING_FACE_API_KEY")

app = Flask(__name__)

# Hugging Face API Configuration
API_URL = ""
HEADERS = {}
API_URL = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
HEADERS = {"Authorization": f"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"}

# Load car data from cars.json
with open('data/cars.json') as f:
    car_data = json.load(f)

# Appointment data structure
appointments = []

def query_huggingface(payload):
    response = requests.post(API_URL, headers=HEADERS, json=payload)
    return response.json()

# Route for Homepage
@app.route('/')
def index():
    return render_template('index.html')

# Route for Chatbot Interaction
@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message received"}), 400

    # Check if the user is trying to book an appointment
    if "book appointment" in user_message.lower():
        return jsonify({
            "reply": "Sure! When would you like to schedule the appointment? Please provide the date and time."
        })

    # Collecting appointment details if requested
    if "date" in user_message.lower() or "time" in user_message.lower():
        try:
            # Extract date and time from message
            parts = user_message.split(' ')
            date = parts[2]
            time = parts[3]
            appointment_time = f"{date} {time}"

            # Convert to datetime object
            appointment_datetime = datetime.strptime(appointment_time, "%Y-%m-%d %H:%M")
            appointments.append({
                "customer_message": user_message,
                "appointment_time": appointment_datetime,
            })
            return jsonify({"reply": "Thank you"})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # Check if the user is asking about a specific car
    for car in car_data:
        if car['name'].lower() in user_message.lower():
            competitors = ', '.join([comp['name'] for comp in car['competitors']])
            return jsonify({
                "reply": f"The {car['name']} is priced at {car['price']}. Details: {car['details']}. Competitors: {competitors}."
            })

    # Default Chatbot behavior (fallback to Hugging Face)
    try:
        payload = {"inputs": user_message}
        response = query_huggingface(payload)
        bot_reply = response.get('generated_text', "I'm sorry, I couldn't process that.")
        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)

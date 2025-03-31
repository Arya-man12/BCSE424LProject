import numpy as np
import cv2
import requests
import serial
import time
import tflite_runtime.interpreter as tflite
import os
from picamera2 import Picamera2

# Load the TensorFlow Lite model
MODEL_PATH = "sign_language_model.tflite"
interpreter = tflite.Interpreter(model_path=MODEL_PATH)
interpreter.allocate_tensors()

# Get input and output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

def preprocess_frame(frame):
    """ Preprocess the frame for model inference """
    frame = cv2.resize(frame, (128, 128))  # Resize to match model input
    frame = frame.astype("float32") / 255.0  # Normalize
    frame = np.expand_dims(frame, axis=0)  # Add batch dimension
    return frame

def predict_sign_language(frame):
    """ Predict sign language using the TFLite model """
    processed_frame = preprocess_frame(frame)
    interpreter.set_tensor(input_details[0]['index'], processed_frame)
    interpreter.invoke()
    prediction = interpreter.get_tensor(output_details[0]['index'])
    return chr(np.argmax(prediction) + 65)  # Assuming output is A-Z

# Capture Video Frames for Prediction Window
def capture_gesture_sequence(pause_threshold=1.5, inactivity_threshold=15, headless_mode=False):
    """ Capture gestures until user decides to stop and return the detected string """
    picam2 = Picamera2()
    picam2.configure(picam2.create_preview_configuration())
    picam2.start()
    
    detected_text = ""
    last_time = time.time()
    inactivity_start = time.time()
    
    while True:
        frame = picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        
        if not headless_mode:
            cv2.imshow("Sign Language Detection", frame)
        
        letter = predict_sign_language(frame)  # Predict single letter
        
        if letter:  # If a valid letter is detected, add to text
            detected_text += letter
            last_time = time.time()  # Reset last detection time
            inactivity_start = time.time()  # Reset inactivity timer
        elif time.time() - last_time > pause_threshold:
            detected_text += " "  # Insert space if there is a long pause
            last_time = time.time()
        
        if time.time() - inactivity_start >= inactivity_threshold:
            user_choice = input("Continue capturing gestures? (yes/no): ").strip().lower()
            if user_choice == "no":
                break  # Stop capturing if user says no
            else:
                inactivity_start = time.time()  # Reset inactivity timer
        
        if not headless_mode and cv2.waitKey(1) & 0xFF == ord('q'):
            break  # Allow quitting with 'q'
        
        time.sleep(0.5)  # Adjust timing as needed
    
    picam2.stop()
    if not headless_mode:
        cv2.destroyAllWindows()
    return detected_text

def convert_to_sentence(text):
    """ Simple heuristic to convert detected letters into words/sentences """
    words = text.split()  # Split based on detected spaces
    return " ".join(words).capitalize() + "."

# Check if running in a headless environment
headless_mode = os.getenv("DISPLAY") is None

# Capture gestures
print("Capturing gestures...")
detected_text = capture_gesture_sequence(headless_mode=headless_mode)
if not detected_text:
    print("No gestures detected. Exiting.")
    exit()

sentence = convert_to_sentence(detected_text)
print(f"Predicted Sentence: {sentence}")

# Ask user how to respond
response_option = input("Do you want to send the text to Gemini API or type your own response? (gemini/manual): ").strip().lower()
if response_option == "gemini":
    GEMINI_API_KEY = "your-gemini-api-key"
    
    def send_to_gemini(text):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateText?key={GEMINI_API_KEY}"
        headers = {"Content-Type": "application/json"}
        payload = {"contents": [{"parts": [{"text": text}]}]}

        response = requests.post(url, json=payload, headers=headers)
        return response.json().get("candidates", [{}])[0].get("content", "No response")
    
    response = send_to_gemini(sentence)
    print(f"Gemini Response: {response}")
else:
    response = input("Type your response: ")

# Send Response via Bluetooth to Arduino HC-05
def send_bluetooth_message(message):
    try:
        with serial.Serial("/dev/rfcomm0", 9600, timeout=1) as bt:
            bt.write(message.encode())  # Convert text to bytes and send
            print(f"Sent via Bluetooth: {message}")
    except Exception as e:
        print(f"Bluetooth Error: {e}")

if response:
    send_bluetooth_message(response)

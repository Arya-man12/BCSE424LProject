import numpy as np
import tflite_runtime.interpreter as tflite
from picamera2 import Picamera2
import time
import cv2
import os
import google.generativeai as genai
import paho.mqtt.client as mqtt

# Clear console for better readability
def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

# Load the TensorFlow Lite model
def load_model(model_path):
    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()
    print("Model loaded successfully.")
    return interpreter

# Preprocess camera frame for model input
def preprocess_frame(frame, input_shape):
    if frame is None or frame.size == 0:
        print("Empty frame captured, skipping...")
        return None
    print(f"Original frame shape: {frame.shape}")
    if frame.shape[2] != 1:
        print("Converting to grayscale...")
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame = cv2.resize(frame, (input_shape[2], input_shape[1]))
    frame = np.expand_dims(frame, axis=-1)
    frame = frame.astype(np.float32) / 255.0
    frame = (frame * 127).astype(np.int8)
    frame = np.expand_dims(frame, axis=0)
    print(f"Processed frame shape: {frame.shape}")
    return frame

# Predict letter from frame
def predict(interpreter, frame):
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    interpreter.set_tensor(input_details[0]['index'], frame)
    interpreter.invoke()
    output_data = interpreter.get_tensor(output_details[0]['index'])
    print(f"Raw model output: {output_data}")
    predicted_index = np.argmax(output_data)
    print(f"Predicted index: {predicted_index}")
    return chr(predicted_index + 65)

# Send text to Gemini API
def send_to_gemini(text):
    try:
        genai.configure(api_key="YOUR_GEMINI_API_KEY")  # Replace with your key
        model = genai.GenerativeModel('gemini-1.0-pro')
        response = model.generate_content(f"Respond to this: {text}")
        return response.text
    except Exception as e:
        return f"Error contacting Gemini: {str(e)}"

# Send text via MQTT to ESP32
def send_via_mqtt(text):
    try:
        broker_address = "192.168.113.250"  # Your phone's IP
        broker_port = 1883
        topic = "test/topic"  # Topic ESP32 is subscribed to
        
        client = mqtt.Client(protocol=mqtt.MQTTv311)
        client.connect(broker_address, broker_port)
        
        # Publish the user input to "test/topic"
        client.publish(topic, text, qos=1)  # QoS 1 ensures delivery
        print(f"Sending '{text}' to '{topic}'...")
        
        # Keep the connection alive briefly to ensure delivery
        client.loop_start()
        time.sleep(2)  # Wait 2 seconds for message to propagate
        client.loop_stop()
        
        client.disconnect()
        return f"Sent '{text}' to MQTT broker at {broker_address}:{broker_port} on topic '{topic}'"
    except Exception as e:
        return f"Error sending via MQTT: {str(e)}"

# Display menu and handle user choice
def display_menu(output_text):
    clear_console()
    print("=====================================")
    print("      Sign Language Recognition      ")
    print("=====================================")
    print(f"Recognized Text: {output_text}")
    print("-------------------------------------")
    print("Options:")
    print("  1. Send to Gemini for a response")
    print("  2. Send custom input via MQTT to ESP32")
    print("  q. Quit")
    print("-------------------------------------")
    choice = input("Enter your choice (1, 2, or q): ").strip().lower()
    return choice

# Main program
model_path = "sign_language_model.tflite"
interpreter = load_model(model_path)
input_details = interpreter.get_input_details()
input_shape = input_details[0]['shape']
print(f"Model expects input shape: {input_shape}")

picam2 = Picamera2()
picam2.configure(picam2.create_preview_configuration(main={'size': (input_shape[2], input_shape[1])}))
picam2.start()
print("Camera started.")

output_text = ""
last_prediction_time = time.time()
last_letter = None
pause_for_space = 3
inactivity_limit = 15
debounce_count = 0
required_debounce = 3
prev_predicted_letter = None

clear_console()
print("=====================================")
print("  Starting Sign Language Detection  ")
print("=====================================")
print("Show your signs to the camera...")
print("Press 'q' to stop detection at any time.")

try:
    while True:
        frame = picam2.capture_array()
        print(f"Captured frame: {frame.shape if frame is not None else 'None'}")
        
        if frame is None or frame.size == 0:
            print("Skipping empty frame...")
            continue
        
        processed_frame = preprocess_frame(frame, input_shape)
        if processed_frame is None:
            continue
        
        predicted_letter = predict(interpreter, processed_frame)
        current_time = time.time()
        
        if predicted_letter == prev_predicted_letter:
            debounce_count += 1
        else:
            debounce_count = 0
            prev_predicted_letter = predicted_letter
        
        if debounce_count >= required_debounce:
            if last_letter is None or predicted_letter != last_letter or output_text[-1] == " ":
                output_text += predicted_letter
                last_prediction_time = current_time
                last_letter = predicted_letter
                debounce_count = 0
                print(f"Added letter: {predicted_letter}")
        
        elif current_time - last_prediction_time >= pause_for_space and last_letter is not None:
            output_text += " "
            last_prediction_time = current_time
            print("Added space due to 3-second pause.")
        
        if current_time - last_prediction_time >= inactivity_limit:
            print("No activity for 15 seconds. Moving to menu...")
            break
        
        print(f"Recognized Text: {output_text}")
        
        cv2.imshow("Camera Feed", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            print("Detection stopped by 'q' key.")
            break
        
        time.sleep(0.5)

except KeyboardInterrupt:
    print("\nDetection stopped by user (Ctrl+C).")

finally:
    picam2.stop()
    cv2.destroyAllWindows()
    print("Camera stopped.")

# Menu loop
while True:
    choice = display_menu(output_text)
    
    if choice == '1':
        clear_console()
        print("=====================================")
        print("      Sending to Gemini API         ")
        print("=====================================")
        print(f"Sending: {output_text}")
        response = send_to_gemini(output_text)
        print("-------------------------------------")
        print(f"Gemini Response: {response}")
        print("-------------------------------------")
        input("Press Enter to return to menu...")
    
    elif choice == '2':
        clear_console()
        print("=====================================")
        print("      MQTT Input Mode               ")
        print("=====================================")
        user_input = input("Enter text to send via MQTT to ESP32: ").strip()
        print("-------------------------------------")
        result = send_via_mqtt(user_input)
        print(result)
        print("-------------------------------------")
        input("Press Enter to return to menu...")
    
    elif choice == 'q':
        print("Exiting program. Goodbye!")
        break
    
    else:
        print("Invalid choice. Please select 1, 2, or q.")
        input("Press Enter to try again...")

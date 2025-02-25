from machine import Pin, ADC
import network
import time
import dht
import ujson
from umqtt.robust import MQTTClient
import utime

# Wi-Fi Configuration
SSID = "smkn7smg"  # Replace with your Wi-Fi SSID
PASSWORD = ""  # Replace with your Wi-Fi password

# Ubidots MQTT Broker Configuration
ubidotsToken = "BBUS-texNJUy7hZEzqgMHrcKGHAkbGE0fxI"
clientID = "MUDRIK2910290"
client = MQTTClient(clientID, "industrial.api.ubidots.com", 1883, user=ubidotsToken, password=ubidotsToken)

# Sensor and Output Pins
sensor1 = dht.DHT11(Pin(25))  # DHT22 Temperature and Humidity Sensor connected to GPIO25
buzzer = Pin(14, Pin.OUT)  # Buzzer connected to GPIO14
led = Pin(12, Pin.OUT)  # LED connected to GPIO12
led3 = Pin(13, Pin.OUT)  # Another LED connected to GPIO13

AO_PIN = ADC(Pin(35))  # LDR sensor pin (light intensity) connected to GPIO35
AO_PIN.width(ADC.WIDTH_12BIT)  # Set ADC width to 12 bits (0-4095)
AO_PIN.atten(ADC.ATTN_11DB)  # Set attenuation to 11 dB (input range ~3.3V)

# Define MQTT_TOPIC
MQTT_TOPIC = "/v1.6/devices/esp32-sensor"

# Connect to Wi-Fi
def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(SSID, PASSWORD)

    print("Connecting to Wi-Fi", SSID)
    while not wlan.isconnected():
        print("Waiting for connection...")
        time.sleep(1)

    print("Connected to Wi-Fi, IP:", wlan.ifconfig()[0])


# Main loop
def main():
    connect_wifi()  # Connect to Wi-Fi
    mqtt_client = client.connect()  # Connect to MQTT broker

    if mqtt_client is None:
        return  # Exit if unable to connect to MQTT

    prev_data = ""

    while True:
        light_value = AO_PIN.read()  # Read light sensor (LDR) value (0-4095)

        # Control LED and Buzzer based on light intensity
        if light_value < 800:
            description = "Dark"
            led.on()
            buzzer.on()
        elif light_value < 1500:
            description = "Dim"
            led.on()
            buzzer.on()
        elif light_value < 3048:
            description = "Light"
            led.off()
            buzzer.off()
        elif light_value < 4000:
            description = "Bright"
            led.off()
            buzzer.off()
        else:
            description = "Very Bright"
            led.off()
            buzzer.off()

        print("Measuring weather and light conditions...")

        sensor1.measure()  # Read DHT22 sensor data

        # Create JSON message with temperature, humidity, and light intensity
        message = ujson.dumps({
            "temperature": sensor1.temperature(),
            "humidity": sensor1.humidity(),
            "light": light_value,
        })

        if message != prev_data:
            print("New data!")
            print(f"Publishing data to MQTT topic {MQTT_TOPIC}: {message}")
            try:
                client.publish(MQTT_TOPIC, message)  # Send data to MQTT broker
            except OSError as e:
                print(f"Error publishing data: {e}")
                time.sleep(5)  # Retry after 5 seconds
            prev_data = message
        else:
            print("Data is the same, no change.")

        time.sleep(1)  # Sleep for 1 second
        utime.sleep(1)  # Use utime.sleep(1) for ESP32


# Start the program
main()


from flask import Flask, render_template
import RPi.GPIO as GPIO
import time
import Adafruit_DHT

app = Flask(__name__)

# Set the GPIO pin number for the DHT22 sensor
DHT22 = Adafruit_DHT.DHT22
dht_pin = 4

# Set the GPIO pin numbers for the relays
heat_relay_pin = 17
humidifier_relay_pin = 27
egg_turner_relay_pin = 22

# Set the temperature and humidity thresholds
temp_threshold = 50
humidity_threshold = 20

# Initialize the GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(heat_relay_pin, GPIO.OUT)
GPIO.setup(humidifier_relay_pin, GPIO.OUT)
GPIO.setup(egg_turner_relay_pin, GPIO.OUT)

# Set the egg turner interval time
egg_turner_interval = 4*60*60  # 4 hours in seconds

# Get the current time
start_time = time.time()

try:
    while True:
        # Read the temperature and humidity from the DHT22 sensor
        humidity, temperature = Adafruit_DHT.read_retry(DHT22, dht_pin)

        # Check if the temperature is below the threshold
        if temperature < temp_threshold:
            # Turn on the heat source
            heat_status = "On"
            GPIO.output(heat_relay_pin, GPIO.HIGH)
        else:
            # Turn off the heat source
            heat_status = "Off"
            GPIO.output(heat_relay_pin, GPIO.LOW)

        # Check if the humidity is above the threshold
        if humidity > humidity_threshold:
            # Turn off the humidifier
            humidifier_status = "Off"
            GPIO.output(humidifier_relay_pin, GPIO.LOW)
        else:
            # Turn on the humidifier
            humidifier_status = "On"
            GPIO.output(humidifier_relay_pin, GPIO.HIGH)

        # Check if it's time to turn the eggs
        if (time.time() - start_time) > egg_turner_interval:
            # Turn on the egg turner for 5 seconds
            egg_turner_status = "On"
            GPIO.output(egg_turner_relay_pin, GPIO.HIGH)
            time.sleep(5)
            GPIO.output(egg_turner_relay_pin, GPIO.LOW)
            egg_turner_status = "Off"
            last_turn_time = time.time()
            # Reset the start time
            start_time = time.time()

        # Wait for a few seconds before reading the sensor again
        time.sleep(5)

except KeyboardInterrupt:
    print("Quit")
    # Reset GPIO settings
    GPIO.cleanup()

@app.route("/")
def index():
    return render_template("index.html", temperature=temperature, humidity=humidity, heat_status=heat_status, humidifier_status=humidifier_status, egg_turner_status=egg_turner_status, last_turn_time=last_turn_time)

if name == "main":
    app.run(host='0.0.0.0', port=80)

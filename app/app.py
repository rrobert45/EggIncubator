from flask import Flask, render_template, request
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import csv
import pandas as pd
import datetime

app = Flask(__name__)

class IncubatorApp:
    def __init__(self):
        # Set the sensor type and the pin number where the sensor is connected. 
        self.sensor = Adafruit_DHT.DHT22
        self.pin = 4

        # Set the pin numbers for the power relays
        self.heater_relay_pin = 17
        self.cooler_relay_pin = 18
        self.humidifier_relay_pin = 27
        self.dehumidifier_relay_pin = 22

        # Set the temperature and humidity thresholds
        self.temp_threshold = 99.5
        self.humidity_threshold = 50

        # Set the waiting time between measurements
        self.waiting_time = 10
        
        # Set the incubation start day
        self.start_date = None
        self.current_day = None

        # Set up the GPIO library
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.heater_relay_pin, GPIO.OUT)
        GPIO.setup(self.cooler_relay_pin, GPIO.OUT)
        GPIO.setup(self.humidifier_relay_pin, GPIO.OUT)
        GPIO.setup(self.dehumidifier_relay_pin, GPIO.OUT)

        # Turn off all the power relays
        GPIO.output(self.heater_relay_pin, GPIO.LOW)
        GPIO.output(self.cooler_relay_pin, GPIO.LOW)
        GPIO.output(self.humidifier_relay_pin, GPIO.LOW)
        GPIO.output(self.dehumidifier_relay_pin, GPIO.LOW)
    
        # function to log data in csv file
    def log_data(self, temperature, humidity):
        data = {"temperature": temperature, "humidity": humidity, "timestamp": time.time()}
        with open("data.csv", "a") as f:
            writer = csv.DictWriter(f, fieldnames=["temperature", "humidity", "timestamp"])
            writer.writerow(data)
            
    def start_incubation(self):
        self.start_date = datetime.datetime.now()
        with open("startdate.csv", "w") as f:
            writer = csv.DictWriter(f, fieldnames=["start_date"])
            writer.writerow({"start_date": self.start_date})

    def update_current_day(self):
        if self.start_date:
            current_date = datetime.datetime.now()
            self.current_day = (current_date - self.start_date).days

    def update_values(self):
        # Read the temperature and humidity from the sensor
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        temperature_f = temperature * (9/5) + 32
        temperature_f = round(temperature_f, 2)
        humidity = round(humidity, 2)
        self.log_data(temperature_f, humidity)
        self.update_current_day()
        # Check if the temperature is above the threshold
        if temperature > self.temp_threshold:
            # Turn on the cooler
            GPIO.output(self.cooler_relay_pin, GPIO.HIGH)
            cooler_status = "ON"
            # Turn off the heater
            GPIO.output(self.heater_relay_pin, GPIO.LOW)
            heater_status = "OFF"
        else:
            # Turn off the cooler
            GPIO.output(self.cooler_relay_pin, GPIO.LOW)
            cooler_status = "OFF"
            # Turn on the heater
            GPIO.output(self.heater_relay_pin, GPIO.HIGH)
            heater_status = "ON"

    # Check if the humidity is above the threshold
        if humidity > self.humidity_threshold:
            # Turn on the dehumidifier
            GPIO.output(self.dehumidifier_relay_pin, GPIO.HIGH)
            dehumidifier_status = "ON"
            # Turn off the humidifier
            GPIO.output(self.humidifier_relay_pin, GPIO.LOW)
            humidifier_status = "OFF"
        else:
            # Turn off the dehumidifier
            GPIO.output(self.dehumidifier_relay_pin, GPIO.LOW)
            dehumidifier_status = "OFF"
            # Turn on the humidifier
            GPIO.output(self.humidifier_relay_pin, GPIO.HIGH)
            humidifier_status = "ON"

        # Check if the incubation start date has been set
        if self.start_date:
            # Calculate the current day of incubation
            self.current_day = (datetime.datetime.now() - self.start_date).days + 1
        else:
            self.current_day = None
            # Return the current temperature, humidity, and status of the power relays
        return temperature_f, humidity, heater_status, cooler_status, humidifier_status, dehumidifier_status

    def start_incubation(self):
        # Set the incubation start date to the current date and time
        self.start_date = datetime.datetime.now()
        
        # Save the incubation start date to a csv file
        with open("startdate.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerow([self.start_date])
            
    def load_start_date(self):
        try:
            # Try to read the incubation start date from a csv file
            # Try to read the incubation start date from a csv file
            with open("statedate.csv", "r") as f:
                reader = csv.reader(f)
                start_date = next(reader)[0]
                self.start_date = datetime.datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S.%f")
                self.current_day = (datetime.datetime.now() - self.start_date).days
        except:
            # If the file doesn't exist or there's an error reading it, set the start date to None
            self.start_date = None
            self.current_day = None
        
@app.route("/")
def index():
    incubator_app = IncubatorApp()
    temperature, humidity, heater_status, cooler_status, humidifier_status, dehumidifier_status = incubator_app.update_values()
    current_day = incubator_app.calculate_current_day()
    start_date = incubator_app.load_start_date()
    return render_template("index.html", temperature=temperature, humidity=humidity, heater_status=heater_status, 
                           cooler_status=cooler_status, humidifier_status=humidifier_status, 
                           dehumidifier_status=dehumidifier_status, current_day=current_day, start_date=start_date)

@app.route("/start_incubation", methods=["POST"])
def start_incubation():
    incubator_app = IncubatorApp()
    incubator_app.save_start_date()
    return "Incubation started!"

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
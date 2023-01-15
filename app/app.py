from flask import Flask, render_template
import Adafruit_DHT
import RPi.GPIO as GPIO
import time
import csv
import pandas as pd
import datetime

start_date = None

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
            
    def update_values(self):
        # Read the temperature and humidity from the sensor
        humidity, temperature = Adafruit_DHT.read_retry(self.sensor, self.pin)
        temperature_f = temperature * (9/5) + 32
        temperature_f = round(temperature_f, 2)
        humidity = round(humidity, 2)
        self.log_data(temperature_f, humidity)

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
        
        if self.start_date is not None:
            self.current_day = (datetime.now() - self.start_date).days + 1
        else:
            self.current_day = None
        # Check if the incubation start day is set
        if self.start_day:
            self.current_day = (time.time() - self.start_day) // (24*3600) + 1
            if self.current_day <= 17:
                self.humidity_threshold = 50
                self.temp_threshold = 99.5
            elif 18 <= self.current_day <= 21:
                self.humidity_threshold = 70
                self.temp_threshold = 100.5
                self.stop_egg_turning()
        
        # Return the values to be displayed on the web page
        return temperature_f, humidity, heater_status, cooler_status, humidifier_status, dehumidifier_status
    
    def stop_egg_turning(self):
        # Stop the egg turning mechanism
        pass
    
    def set_start_day(self):
        self.start_day = time.time()
        with open("data.csv", "a") as f:
            writer = csv.writer(f)
            writer.writerow(["Start Day", self.start_day])

    def retrieve_start_date():
        with open('startdate.csv', 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row[0] == 'start_date':
                    start_date = row[1]
                    return start_date
        return None

    
            
@app.route('/')
def index():
    temperature, humidity, heater_status, cooler_status, humidifier_status, dehumidifier_status = incubator_app.update_values()
    return render_template('index.html', temperature=temperature, humidity=humidity, heater_status=heater_status, cooler_status=cooler_status, humidifier_status=humidifier_status, dehumidifier_status=dehumidifier_status)
@app.route('/start')
def start():
    incubator_app.set_start_day()
    return "Incubation started!"

@app.route('/data')
def data():
    data = pd.read_csv("data.csv")
    return render_template("data.html", data=data)

@app.route('/start', methods=['GET'])
def start_incubation():
    incubator_app.start_date = datetime.now()
    with open('startdate.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['start_date', incubator_app.start_date])
    return redirect('/')
    
if __name__ == '__main__':
    incubator_app = IncubatorApp()
    app.run(debug=True, host='0.0.0.0')
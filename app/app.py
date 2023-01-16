import Adafruit_DHT
import datetime
import csv
import time
import RPi.GPIO as GPIO
import json

# Reading config file
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

DHT_SENSOR = Adafruit_DHT.DHT22
DHT_PIN = config['dht_pin']
RELAY_HUMIDITY = config['relay_humidity']
RELAY_TEMPERATURE = config['relay_temperature']
RELAY_EGG_TURNER = config['relay_egg_turner']
DESIRED_HUMIDITY = config['desired_humidity']
DESIRED_TEMPERATURE = config['desired_temperature']
START_DATE = datetime.datetime.strptime(config['start_date'], '%Y-%m-%d %H:%M:%S')

# Setting up GPIO pins
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_HUMIDITY, GPIO.OUT)
GPIO.setup(RELAY_TEMPERATURE, GPIO.OUT)
GPIO.setup(RELAY_EGG_TURNER, GPIO.OUT)
GPIO.setwarnings(False)

def read_sensor():
    humidity, temperature = Adafruit_DHT.read_retry(DHT_SENSOR, DHT_PIN)
    return humidity, temperature

def control_humidity():
    humidity, _ = read_sensor()
    if humidity < DESIRED_HUMIDITY:
        GPIO.output(RELAY_HUMIDITY, GPIO.HIGH)
    else:
        GPIO.output(RELAY_HUMIDITY, GPIO.LOW)

def control_temperature():
    _, temperature = read_sensor()
    if temperature < DESIRED_TEMPERATURE:
        GPIO.output(RELAY_TEMPERATURE, GPIO.HIGH)
    else:
        GPIO.output(RELAY_TEMPERATURE, GPIO.LOW)

def control_egg_turner():
    current_time = datetime.datetime.now()
    egg_turner_status = GPIO.input(RELAY_EGG_TURNER)
    if (current_time - last_egg_turn_time).seconds > 4*60*60 and egg_turner_status == 0:
        GPIO.output(RELAY_EGG_TURNER, GPIO.HIGH)
        time.sleep(10)
        GPIO.output(RELAY_EGG_TURNER, GPIO.LOW)
        last_egg_turn_time = current_time

def increase_humidity():
    current_day = (datetime.datetime.now() - START_DATE).days
    if current_day == 19:
        DESIRED_HUMIDITY = 70

def save_data():
    humidity, temperature = read_sensor()
    current_time = datetime.datetime.now()
    egg_turner_status = GPIO.input(RELAY_EGG_TURNER)
    with open('data.csv', mode='a') as data_file:
        data_writer = csv.writer(data_file)
        data_writer.writerow([current_time, temperature, humidity, egg_turner_status])

def display_data():
    # code to display data on web page
    pass

last_egg_turn_time = datetime.datetime.now()

# Main loop that runs every 10 minutes
while True:
    control_humidity()
    control_temperature()
    control_egg_turner()
    increase_humidity()
    save_data()
    time.sleep(10*60)

# Cleanup
GPIO.cleanup()
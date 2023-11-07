import machine
import network
import time
import json
from servo import Servo
from umqtt.simple import MQTTClient
from machine import RTC
from machine import Timer

# WIFI parameters
ACCESS_POINT = "XXXX"
PASSWORD = "XXXX"

# Wait for connection
def check_wifi(wlan):
    # Track the connection retries
    connect_count = 0
    while not wlan.isconnected():
        if connect_count == 5:
            machine.reset()
            
        print("connecting")
        wlan.connect( ACCESS_POINT, PASSWORD )
        connect_count = connect_count + 1
        
        for i in range(0, 6, 1):
            led.toggle()
            time.sleep(1)            
        
    print("connected")
    led.on()

# Callback for timer, could use the check_wifi instead
def check_wifi_callback(timer):
    global wlan
    check_wifi(wlan)

# Sweep for smoother position movements
def sweep_servo(angle):
    global last_position
    increment_by = 1
    if last_position > angle:
        increment_by = -1
    for i in range(last_position, angle, increment_by):
        s.write(i)
        time.sleep(0.2)
    s.off() # Turn off the PWM, the solar panel should stay in place
    last_position = angle

# Callback function for received messages
def mqtt_callback(topic, msg):
    #print("received data:")
    #print("topic: %s message: %s" %(topic, msg))
    if topic==b'solar/controlunit/1/reset':
        machine.reset()
    elif topic==b'solar/controlunit/1/led':
        if msg==b'on':
            led.on()
        elif msg==b'off':
            led.off()
    elif topic==b'solar/controlunit/1/position':
        try:                
            angle = int(msg)
            if angle < 0 or angle > 180:
                print("angle must be between 0 and 180")
            else:
                print(angle)
                sweep_servo(angle)      
                mqtt.publish(b"solar/controlunit/1/status/position", str(angle))
        except ValueError:
            print("invalid angle")
            
# Read internal temperature sensor of RPi Pico W
def read_internal_temp_sensor():
    sensor_temp = machine.ADC(4)
    conversion_factor = 3.3 / (65535)
    reading = sensor_temp.read_u16() * conversion_factor
    temperature = 27 - (reading - 0.706)/0.001721
    return temperature

# Pin setup
led = machine.Pin("LED", machine.Pin.OUT)
s=Servo(pin_id=22)
battery_voltage_pin = machine.ADC(1)
solar_voltage_pin = machine.ADC(2)

# Last servo position
last_position = 90

# Conversion for ADC voltages
conversion_factor = 3.3 / (65535)

# Give some startup time
time.sleep(2)

# Setup WiFi connection.
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
check_wifi(wlan)

# Setup MQTT
mqtt = MQTTClient("umqtt_client", "10.0.0.21")
mqtt.set_callback(mqtt_callback)
mqtt.connect()
mqtt.subscribe(b"solar/controlunit/1/reset")
mqtt.subscribe(b"solar/controlunit/1/position")
mqtt.subscribe(b"solar/controlunit/1/led")

# Set Default panel position
s.write(95)
time.sleep(1)
s.off()

# Set a timer to check the wifi every 1 minute
Timer(mode=Timer.PERIODIC, period=60000, callback=check_wifi_callback)

# Main Loop
while True:
    # Solar Voltage Measurement
    solar_voltage =  round(solar_voltage_pin.read_u16() * conversion_factor * 2 + 0.033, 2)
    
    # Battery Voltage Measurement
    battery_voltage =  round(battery_voltage_pin.read_u16() * conversion_factor * 2 + 0.033, 2)
    
    # Internal Temp
    internal_temp =  round(read_internal_temp_sensor())
    
    # Publish status
    status = {"supply-voltage": solar_voltage,"battery-voltage":  battery_voltage,"internal_temp": internal_temp,"position":  last_position}
    mqtt.publish(b"solar/controlunit/1/status", json.dumps(status))
    
    # Check for new subscribed messages
    mqtt.check_msg()
    
    time.sleep(10)

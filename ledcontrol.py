#! /usr/bin/env python3
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt
import json
import os
import pprint
import signal

#define some default values
DEFAULT_MQTT_ACTIVE=True
DEFAULT_MQTT_BROKER_ADDRESS="192.168.1.2"
DEFAULT_MQTT_USERNAME=None
DEFAULT_MQTT_PASSWORD=""
DEFAULT_CLIENT_NAME="raspled"
DEFAULT_SPI_PORT=0
DEFAULT_SPI_DEVICE=0
DEFAULT_SPI_CLK_GPIO=""
DEFAULT_SPI_DATA_GPIO=""
DEFAULT_LED_GPIO_PIN=-1
DEFAULT_LED_RGB_MODE="GRB"
DEFAULT_MAX_LEDS=160
DEFAULT_NUM_LEDS=160
DEFAULT_NUM_PONG_LEDS=10
DEFAULT_BTN_ONE_GPIO=17
DEFAULT_BTN_TWO_GPIO=27
DEFAULT_BTN_DEBOUNCE_DELAY=300
DEFAULT_PONG_BTN_DELAY=2.0
DEFAULT_PONG_MAX_WINS=2
DEFAULT_PONG_TOLERANCE=2
DEFAULT_PONG_INIT_LED_DELAY=0.5
DEFAULT_PONG_DEC_PER_RUN=0.05
DEFAULT_PONG_MIN_LED_DELAY=0.02
DEFAULT_PONG_RESULT_DELAY_DURING=2.0
DEFAULT_PONG_RESULT_DELAY_AFTER=5.0
DEFAULT_PONG_COLOR_R=0
DEFAULT_PONG_COLOR_B=255
DEFAULT_PONG_COLOR_G=0
DEFAULT_PONG_RESULT_COLOR_R=0
DEFAULT_PONG_RESULT_COLOR_G=255
DEFAULT_PONG_RESULT_COLOR_B=0
DEFAULT_COLOR_R=255
DEFAULT_COLOR_G=255
DEFAULT_COLOR_B=255
DEFAULT_PUBLISH_STATUS_AFTER_EVERY_CONFIG_CHANGE=False
DEFAULT_PUBLISH_STATUS_IF_TOGGLED=True

#set the gpio mode to use the gpio numbering and not the pin numbering
GPIO.setmode(GPIO.BCM)

#function that decides if a system variable or the default value should be used
#the type of the return value will be the same as of the default value
#if the default value is boolean a value of "1" of the system variable will lead to a true value, all others to false
def sys_var_to_var(sys_var, default_value):
    if type(default_value) is int:
        return int(os.getenv(sys_var, default_value))
    elif type(default_value) is float:
        return float(os.getenv(sys_var, default_value))
    elif type(default_value) is bool:
        if default_value:
            cur_value = 1
        else:
            cur_value = 0
        if os.getenv(sys_var, cur_value) == 1:
            return True
        else:
            return False
    else:
        return os.getenv(sys_var, default_value)

def clear_pixels(pixels):
    global led_gpio_mode, led_rgb_mode
    if led_gpio_mode:
        if led_rgb_mode in (neopixel.RGB, neopixel.GRB):
            pixels.fill((0, 0, 0))
        else:
            pixels.fill((0, 0, 0, 0))
        
    else:
        pixels.clear()

def set_pixel_color(pixels, i, color_r, color_g, color_b):
    global led_gpio_mode, led_rgb_mode
    if led_gpio_mode:
        if led_rgb_mode in (neopixel.RGB, neopixel.GRB):
            pixels[i] = (color_r,color_g,color_b)
        else:
            pixels[i] = (color_r,color_g,color_b,0)
    else:
        pixels.set_pixel_rgb(i, color_r, color_g, color_b)

def get_board_pin(gpio_nr):
    if gpio_nr is 21:
        return board.D21
    elif gpio_nr is 10:
        return board.D10
    elif gpio_nr is 12:
        return board.D12
    elif gpio_nr is 18:
        return board.D18
    else:
        return None

#init the variables either with the default value or values that are set in environment variables
btn_one_gpio = sys_var_to_var("LED_BTN_ONE_GPIO", DEFAULT_BTN_ONE_GPIO)
btn_two_gpio = sys_var_to_var("LED_BTN_TWO_GPIO", DEFAULT_BTN_TWO_GPIO)
btn_debounce = sys_var_to_var("LED_BTN_DEBOUNCE_DELAY", DEFAULT_BTN_DEBOUNCE_DELAY)

reverse_mode = False
cur_pixel = 0
btn_one_state = False
btn_one_time = 0
btn_two_state = False
btn_two_time = 0

num_leds = sys_var_to_var("LED_NUM_LEDS", DEFAULT_NUM_LEDS)
max_leds = sys_var_to_var("LED_MAX_LEDS", DEFAULT_MAX_LEDS)
stripe_mode = 0
stripe_on = False
color_r = sys_var_to_var("LED_COLOR_R",DEFAULT_COLOR_R)
color_g = sys_var_to_var("LED_COLOR_G",DEFAULT_COLOR_G)
color_b = sys_var_to_var("LED_COLOR_B",DEFAULT_COLOR_B)


pong_init_delay = sys_var_to_var("LED_PONG_INIT_DELAY", DEFAULT_PONG_INIT_LED_DELAY)
cur_pong_delay = pong_init_delay
num_pong_leds = sys_var_to_var("LED_PONG_NUM_LEDS", DEFAULT_NUM_PONG_LEDS)
pong_max_wins = sys_var_to_var("LED_PONG_MAX_WINS", DEFAULT_PONG_MAX_WINS)
pong_wins_delay_during = sys_var_to_var("LED_PONG_RESULT_DELAY_DURING", DEFAULT_PONG_RESULT_DELAY_DURING)
pong_wins_delay_after = sys_var_to_var("LED_PONG_RESULT_DELAY_AFTER", DEFAULT_PONG_RESULT_DELAY_AFTER)
pong_min_delay = sys_var_to_var("LED_PONG_MIN_DELAY", DEFAULT_PONG_MIN_LED_DELAY)
pong_dec_per_run = sys_var_to_var("LED_PONG_DEC_PER_RUN", DEFAULT_PONG_DEC_PER_RUN)
pong_btn_delay = sys_var_to_var("LED_PONG_BTN_DELAY", DEFAULT_PONG_BTN_DELAY)
pong_tolerance = sys_var_to_var("LED_PONG_TOLERANCE", DEFAULT_PONG_TOLERANCE)
pong_color_r = sys_var_to_var("LED_PONG_COLOR_R", DEFAULT_PONG_COLOR_R)
pong_color_g = sys_var_to_var("LED_PONG_COLOR_G", DEFAULT_PONG_COLOR_G)
pong_color_b = sys_var_to_var("LED_PONG_COLOR_B", DEFAULT_PONG_COLOR_B)
pong_result_color_r = sys_var_to_var("LED_PONG_RESULT_COLOR_R", DEFAULT_PONG_RESULT_COLOR_R)
pong_result_color_g = sys_var_to_var("LED_PONG_RESULT_COLOR_G", DEFAULT_PONG_RESULT_COLOR_G)
pong_result_color_b = sys_var_to_var("LED_PONG_RESULT_COLOR_B", DEFAULT_PONG_RESULT_COLOR_B)
player_one_wins = 0
player_one_successfull_press = False
player_two_wins = 0
player_two_successfull_press = False

led_gpio_pin = sys_var_to_var("LED_GPIO_PIN", DEFAULT_LED_GPIO_PIN)
led_rgb_mode = sys_var_to_var("LED_RGB_MODE", DEFAULT_LED_RGB_MODE)
spi_port   = sys_var_to_var("SPI_PORT", DEFAULT_SPI_PORT)
spi_device = sys_var_to_var("SPI_DEVICE", DEFAULT_SPI_DEVICE)
spi_clk_gpio = sys_var_to_var("SPI_CLK_GPIO", DEFAULT_SPI_CLK_GPIO)
spi_data_gpio = sys_var_to_var("SPI_DATA_GPIO", DEFAULT_SPI_DATA_GPIO)

publish_status_after_every_config_change = sys_var_to_var("LED_PUBLISH_STATUS_AFTER_EVERY_CONFIG_CHANGE", DEFAULT_PUBLISH_STATUS_AFTER_EVERY_CONFIG_CHANGE)
publish_status_if_toggled = sys_var_to_var("LED_PUBLISH_STATUS_IF_TOGGLED", DEFAULT_PUBLISH_STATUS_IF_TOGGLED)

led_gpio_mode = False
if led_gpio_pin > 0:
    import neopixel, board
    print ("Will WS281X library in %s color mode and the strip is connected to gpio %d" %(led_rgb_mode, led_gpio_pin))

    if led_rgb_mode is "RGB":
        led_rgb_mode = neopixel.RGB
    elif led_rgb_mode is "RGBW":
        led_rgb_mode = neopixel.RGBW
    elif led_rgb_mode is "GRB":
        led_rgb_mode = neopixel.GRB
    elif led_rgb_mode is "GRBW":
        led_rgb_mode = neopixel.GRBW
    else:
        led_rgb_mode = neopixel.GRB

    pixels = neopixel.NeoPixel(get_board_pin(led_gpio_pin), max_leds, brightness=1.0, auto_write=False, pixel_order=led_rgb_mode)
    led_gpio_mode = True

else:#allways prefer the hardware connection
    import Adafruit_WS2801
    import Adafruit_GPIO.SPI as SPI
    if not spi_port is "":
        print ("Will WS2801 library and the strip is connected to hardware spi port %d as device %d" %(spi_port, spi_device))
        pixels = Adafruit_WS2801.WS2801Pixels(max_leds, spi=SPI.SpiDev(spi_port, spi_device))
    else:
        print ("Will WS2801 library and the strip is connected to software spi. Clock pin is GPIO%d and the data pin GPIO%d" %(spi_clk_gpio, spi_data_gpio))
        pixels = Adafruit_WS2801.WS2801Pixels(max_leds, clk=spi_clk_gpio, do=spi_data_gpio)

clear_pixels(pixels)
pixels.show()

client_name = sys_var_to_var("MQTT_CLIENT_NAME", DEFAULT_CLIENT_NAME)
mqtt_broker_address = sys_var_to_var("MQTT_BROKER_ADDRESS", DEFAULT_MQTT_BROKER_ADDRESS)
mqtt_topic_prefix = sys_var_to_var("MQTT_TOPIC_PREFIX", client_name+"/")
mqtt_active = sys_var_to_var("MQTT_ACTIVE", DEFAULT_MQTT_ACTIVE)
mqtt_username = sys_var_to_var("MQTT_USERNAME", DEFAULT_MQTT_USERNAME)
mqtt_password = sys_var_to_var("MQTT_PASSWORD", DEFAULT_MQTT_PASSWORD)

client = None

stop_now = False

#this function connects the mqtt client to the server
#if a username is specified the credentials will be used
def connect_mqtt_client():
    global client, mqtt_username, mqtt_password
    client = mqtt.Client(client_name)
    client.connected_flag=False
    client.on_message=callback_on_message
    client.on_disconnect = on_disconnect
    client.on_connect = on_connect
    client.loop_start()
    
    print("Connecting to MQTT broker: %s" % mqtt_broker_address)
    try:
        if not ((mqtt_username is None) or (mqtt_username is "")):
            client.username_pw_set(mqtt_username, mqtt_password)
        client.connect(mqtt_broker_address)
    except:
        print("Connection attempt failed!")

    time.sleep(5)

#this funtion will be called everytime the MQTT connection will be (re-)established
#after the connection is established the client registers to all necessary topics
def on_connect(client, userdata, flags, rc):
    if rc==0:
        client.connected_flag=True #set flag
        print("Connected to MQTT broker. Subscribing for our topics")
        client.subscribe(mqtt_topic_prefix+"get_status")
        client.subscribe(mqtt_topic_prefix+"config")
        client.subscribe(mqtt_topic_prefix+"output")
        client.subscribe(mqtt_topic_prefix+"pong/btn_delay")
        client.subscribe(mqtt_topic_prefix+"pong/init_delay")
        client.subscribe(mqtt_topic_prefix+"pong/min_delay")
        client.subscribe(mqtt_topic_prefix+"pong/dec_per_run")
        client.subscribe(mqtt_topic_prefix+"pong/num_leds")
        client.subscribe(mqtt_topic_prefix+"pong/max_wins")
        client.subscribe(mqtt_topic_prefix+"pong/result/delay/during")
        client.subscribe(mqtt_topic_prefix+"pong/result/delay/after")
        client.subscribe(mqtt_topic_prefix+"pong/result/color/r")
        client.subscribe(mqtt_topic_prefix+"pong/result/color/g")
        client.subscribe(mqtt_topic_prefix+"pong/result/color/b")
        client.subscribe(mqtt_topic_prefix+"pong/tolerance")
        client.subscribe(mqtt_topic_prefix+"pong/color/r")
        client.subscribe(mqtt_topic_prefix+"pong/color/g")
        client.subscribe(mqtt_topic_prefix+"pong/color/b")
        client.subscribe(mqtt_topic_prefix+"color/r")
        client.subscribe(mqtt_topic_prefix+"color/g")
        client.subscribe(mqtt_topic_prefix+"color/b")
    else:
        print("Bad connection Returned code= ",rc)

#this function is called everytime the MQTT client is disconnected from the server
def on_disconnect(client, userdata, rc):
    print("on_disconnect")
    client.connected_flag = False

#this function is called everytime the MQTT client receives a message
def callback_on_message(client, userdata, message):
    global mqtt_topic_prefix
    global pong_btn_delay, pong_init_delay, pong_min_delay, pong_dec_per_run
    global num_pong_leds, pong_tolerance
    global pong_max_wins, pong_wins_delay_after, pong_wins_delay_during
    global pong_color_r, pong_color_g, pong_color_b, pong_result_color_r, pong_result_color_g, pong_result_color_b
    global color_r, color_g, color_b
    global stripe_on, stripe_mode
    message_str = str(message.payload.decode("utf-8"))
    print ("Received message %s for topic %s" %(message_str, message.topic))

    #check to which topic the message was send
    #apply the value in the same data type as the original and check if the new value is plausible (min, max)
    #if the values are greater than the max or smaller than the min set the value to the max or min value
    if message.topic == mqtt_topic_prefix+"output":
        if message_str == "on":
            toggle_leds(True)
        elif message_str == "off":
            toggle_leds(False)
        else:
            toggle_leds()
    elif message.topic == mqtt_topic_prefix+"config":
        try:
            new_config = json.loads(message_str)
            apply_config(new_config)
        except:
            print("Received wrong config: %s" % message_str)
    elif message.topic == mqtt_topic_prefix+"pong/btn_delay":
        pong_btn_delay = float(message_str)
        if pong_btn_delay < 0:
            pong_btn_delay = 0
    elif message.topic == mqtt_topic_prefix+"pong/init_delay":
        pong_init_delay = float(message_str)
        if pong_init_delay < pong_min_delay:
            pong_init_delay = pong_min_delay
    elif message.topic == mqtt_topic_prefix+"pong/min_delay":
        pong_min_delay = float(message_str)
        if pong_min_delay < 0:
            pong_min_delay = 0
    elif message.topic == mqtt_topic_prefix+"pong/dec_per_run":
        pong_dec_per_run = float(message_str)
        if pong_dec_per_run < 0:
            pong_dec_per_run = 0
    elif message.topic == mqtt_topic_prefix+"pong/num_leds":
        num_pong_leds = int(message_str)
        if num_pong_leds > max_leds:
            num_pong_leds = max_leds
    elif message.topic == mqtt_topic_prefix+"pong/max_wins":
        pong_max_wins = int(message_str)
        if pong_max_wins > num_pong_leds:
            pong_max_wins = num_pong_leds
    elif message.topic == mqtt_topic_prefix+"pong/result/delay/during":
        pong_wins_delay_during = float(message_str)
        if pong_wins_delay_during < 0:
            pong_wins_delay_during = 0
    elif message.topic == mqtt_topic_prefix+"pong/result/delay/after":
        pong_wins_delay_after = float(message_str)
        if pong_wins_delay_after < 0:
            pong_wins_delay_after = 0
    elif message.topic == mqtt_topic_prefix+"pong/result/color/r":
        pong_result_color_r = int(message_str)
        if pong_result_color_r > 255:
            pong_result_color_r = 255
        elif pong_result_color_r < 0:
            pong_result_color_r = 0
    elif message.topic == mqtt_topic_prefix+"pong/result/color/g":
        pong_result_color_g = int(message_str)
        if pong_result_color_g > 255:
            pong_result_color_g = 255
        elif pong_result_color_g < 0:
            pong_result_color_g = 0
    elif message.topic == mqtt_topic_prefix+"pong/result/color/b":
        pong_result_color_b = int(message_str)
        if pong_result_color_b > 255:
            pong_result_color_b = 255
        elif pong_result_color_b < 0:
            pong_result_color_b = 0
    elif message.topic == mqtt_topic_prefix+"pong/tolerance":
        pong_tolerance = int(message_str)
        if pong_tolerance < 0:
            pong_tolerance = 0
        if pong_tolerance > (num_pong_leds - 1):
            pong_tolerance = num_pong_leds - 1
    elif message.topic == mqtt_topic_prefix+"pong/color/r":
        pong_color_r = int(message_str)
        if pong_color_r > 255:
            pong_color_r = 255
        elif pong_color_r < 0:
            pong_color_r = 0
    elif message.topic == mqtt_topic_prefix+"pong/color/g":
        pong_color_g = int(message_str)
        if pong_color_g > 255:
            pong_color_g = 255
        elif pong_color_g < 0:
            pong_color_g = 0
    elif message.topic == mqtt_topic_prefix+"pong/color/b":
        pong_color_b = int(message_str)
        if pong_color_b > 255:
            pong_color_b = 255
        elif pong_color_b < 0:
            pong_color_b = 0
    elif message.topic == mqtt_topic_prefix+"color/r":
        color_r = int(message_str)
        if color_r > 255:
            color_r = 255
        elif color_r < 0:
            color_r = 0
        if stripe_mode == 0:
            toggle_leds(stripe_on)
    elif message.topic == mqtt_topic_prefix+"color/g":
        color_g = int(message_str)
        if color_g > 255:
            color_g = 255
        elif color_g < 0:
            color_g = 0
        if stripe_mode == 0:
            toggle_leds(stripe_on)
    elif message.topic == mqtt_topic_prefix+"color/b":
        color_b = int(message_str)
        if color_b > 255:
            color_b = 255
        elif color_b < 0:
            color_b = 0
        if stripe_mode == 0:
            toggle_leds(stripe_on)
    elif message.topic == mqtt_topic_prefix+"get_status":
        publish_current_status()

#if the function is called the script publishes the current configuration and status to the PREFIX/status topic
def publish_current_status():
    global client
    global mqtt_topic_prefix
    global pong_btn_delay, pong_init_delay, pong_min_delay, pong_dec_per_run
    global num_pong_leds, pong_tolerance
    global pong_max_wins, pong_wins_delay_after, pong_wins_delay_during
    global pong_color_r, pong_color_g, pong_color_b, pong_result_color_r, pong_result_color_g, pong_result_color_b
    global color_r, color_g, color_b
    global stripe_on, stripe_mode, publish_status_if_toggled

    if client != None and client.connected_flag:
        print("Will publish the current status!")
        res_obj = {
            "pong" : {
                "btn_delay" : pong_btn_delay,
                "init_delay" : pong_init_delay,
                "min_delay" : pong_min_delay,
                "dec_per_run" : pong_dec_per_run,
                "num_leds" : num_pong_leds,
                "max_wins" : pong_max_wins,
                "tolerance" : pong_tolerance,
                "result_delay_during" : pong_wins_delay_during,
                "result_delay_after" : pong_wins_delay_after,
                "color_r" : pong_color_r,
                "color_g" : pong_color_g,
                "color_b" : pong_color_b,
                "result_color_r" : pong_result_color_r,
                "result_color_g" : pong_result_color_g,
                "result_color_b" : pong_result_color_b
            },
            "output" : stripe_on,
            "mode" : stripe_mode,
            "color_r" : color_r,
            "color_g" : color_g,
            "color_b" : color_b
        }

        client.publish(mqtt_topic_prefix+"status",json.dumps(res_obj))

#this function is called if button one is pressed
def callback_one(channel):
    global btn_one_time
    global btn_one_state
    btn_one_time  = time.time()
    btn_one_state = True
    

#this function is called if the second button is pressed
def callback_two(channel):
    global btn_two_time 
    global btn_two_state
    btn_two_time = time.time()
    btn_two_state = True

#this function toggles the led stripe either to a specific state (on or off)
#or to the opposite of the current one
def toggle_leds(to_state = None):
    global stripe_on
    global pixels

    state_changed = False

    if to_state != None:
        if(to_state == False):
            if stripe_on != True:
                stripe_on = True
                state_changed = True
        else:
            if stripe_on != False:
                stripe_on = False
                state_changed = True
    else:
        state_changed = True
    
    if stripe_on == False:
        for i in range(0,num_leds):
            set_pixel_color(pixels, i, color_r, color_g, color_b)
        stripe_on = True
    else:
        clear_pixels(pixels)
        stripe_on = False

    pixels.show()

    if state_changed and publish_status_if_toggled:
        publish_current_status()

#this function will init the pong mode
def switch_to_pong_mode():
    global btn_one_state
    global btn_two_state
    global stripe_mode
    global player_one_wins
    global player_two_wins
    global cur_pixel
    global num_pong_leds
    global pong_init_delay
    global cur_pong_delay
    global pixels
    global pong_color_r, pong_color_g, pong_color_b

    btn_one_state = False
    btn_two_state = False
    stripe_mode = 1
    player_one_wins = 0
    player_two_wins = 0
    cur_pixel = 0
    cur_pong_delay = pong_init_delay

    clear_pixels(pixels)
    pixels.show()
    time.sleep(1)

    for i in range(0, num_pong_leds):
        set_pixel_color(pixels, i, pong_color_r, pong_color_g, pong_color_b)
    pixels.show()
    time.sleep(1)

    clear_pixels(pixels)
    pixels.show()
    time.sleep(1)

#this function displays the current pong results
#and waits a given delay
def display_result(cur_delay):
    global pixels
    global player_one_wins, player_two_wins
    global pong_result_color_r, pong_result_color_g, pong_result_color_b
    global num_pong_leds
    time.sleep(0.5)
    clear_pixels(pixels)
    for i in range(0, player_one_wins):
        set_pixel_color(pixels, i, pong_result_color_r, pong_result_color_g, pong_result_color_b)

    for i in range((num_pong_leds-player_two_wins), num_pong_leds):
        set_pixel_color(pixels, i, pong_result_color_r, pong_result_color_g, pong_result_color_b)

    pixels.show()
    time.sleep(cur_delay)

#this function overrides the current values with the ones in the new config
#if the new config is only a partial one the values of the not existing parts will be kept
def apply_config(new_config={}):
    global pong_btn_delay, pong_init_delay, pong_min_delay, pong_dec_per_run
    global num_pong_leds, pong_tolerance
    global pong_max_wins, pong_wins_delay_after, pong_wins_delay_during
    global pong_color_r, pong_color_g, pong_color_b, pong_result_color_r, pong_result_color_g, pong_result_color_b
    global color_r, color_g, color_b
    global stripe_mode, stripe_on, publish_status_after_every_config_change

    pong_options = new_config.get("pong", {})

    pong_btn_delay = float(pong_options.get("btn_delay",pong_btn_delay))
    if pong_btn_delay < 0:
        pong_btn_delay = 0
    pong_min_delay = float(pong_options.get("min_delay",pong_min_delay))
    if pong_min_delay < 0:
        pong_min_delay = 0
    pong_init_delay = float(pong_options.get("init_delay",pong_init_delay))
    if pong_init_delay < pong_min_delay:
        pong_init_delay = pong_min_delay
    pong_dec_per_run = float(pong_options.get("dec_per_run",pong_dec_per_run))
    if pong_dec_per_run < 0:
        pong_dec_per_run = 0
    num_pong_leds = int(pong_options.get("num_leds",num_pong_leds))
    if num_pong_leds > max_leds:
        num_pong_leds = max_leds
    pong_max_wins = int(pong_options.get("max_wins",pong_max_wins))
    if pong_max_wins > num_pong_leds:
        pong_max_wins = num_pong_leds
    pong_tolerance = int(pong_options.get("tolerance",pong_tolerance))
    if pong_tolerance < 0:
        pong_tolerance = 0
    if pong_tolerance > (num_pong_leds - 1):
        pong_tolerance = num_pong_leds - 1
    pong_wins_delay_after = float(pong_options.get("result_delay_after",pong_wins_delay_after))
    if pong_wins_delay_after < 0:
        pong_wins_delay_after = 0
    pong_wins_delay_during = float(pong_options.get("result_delay_during",pong_wins_delay_during))
    if pong_wins_delay_during < 0:
        pong_wins_delay_during = 0
    pong_color_r = int(pong_options.get("color_r",pong_color_r))
    if pong_color_r > 255:
        pong_color_r = 255
    if pong_color_r < 0:
        pong_color_r = 0
    pong_color_g = int(pong_options.get("color_g",pong_color_g))
    if pong_color_g > 255:
        pong_color_g = 255
    if pong_color_g < 0:
        pong_color_g = 0
    pong_color_b = int(pong_options.get("color_b",pong_color_b))
    if pong_color_b > 255:
        pong_color_b = 255
    if pong_color_b < 0:
        pong_color_b = 0
    pong_result_color_r = int(pong_options.get("result_color_r",pong_result_color_r))
    if pong_result_color_r > 255:
        pong_result_color_r = 255
    if pong_result_color_r < 0:
        pong_result_color_r = 0
    pong_result_color_g = int(pong_options.get("result_color_g",pong_result_color_g))
    if pong_result_color_g > 255:
        pong_result_color_g = 255
    if pong_result_color_g < 0:
        pong_result_color_g = 0
    pong_result_color_b = int(pong_options.get("result_color_b",pong_result_color_b))
    if pong_result_color_b > 255:
        pong_result_color_b = 255
    if pong_result_color_b < 0:
        pong_result_color_b = 0

    color_r = int(new_config.get("color_r", color_r))
    if color_r > 255:
        color_r = 255
    if color_r < 0:
        color_r = 0
    color_g = int(new_config.get("color_g", color_g))
    if color_g > 255:
        color_g = 255
    if color_g < 0:
        color_g = 0
    color_b = int(new_config.get("color_b", color_b))
    if color_b > 255:
        color_b = 255
    if color_b < 0:
        color_b = 0

    if stripe_mode == 0:
        toggle_leds(to_state = stripe_on)

    if publish_status_after_every_config_change:
        publish_current_status()

#this function will be called if the script gets killed (sigterm, sigint)
def do_cleanup(signum, frame):
    global client, stop_now
    GPIO.cleanup()

    if client != None:
        try:
            client.loop_stop()
            client.disconnect()
        except:
            pass
    print ("Bye")
    stop_now = True


#register to the signals to do a graceful shutdown
signal.signal(signal.SIGINT, do_cleanup)
signal.signal(signal.SIGTERM, do_cleanup)

#init the gpio ports of the buttons and register the callbacks
GPIO.setup(btn_one_gpio, GPIO.IN)
GPIO.setup(btn_two_gpio, GPIO.IN)

GPIO.add_event_detect(btn_one_gpio, GPIO.RISING, callback=callback_one, bouncetime = btn_debounce)
GPIO.add_event_detect(btn_two_gpio, GPIO.RISING, callback=callback_two, bouncetime = btn_debounce)

#only if mqtt should be used we activate the clients
if mqtt_active:
    connect_mqtt_client()

try:
    while not stop_now:
        #normal mode
        if stripe_mode == 0:
            if btn_two_state == True:
                btn_two_state = False
                if((btn_two_time - btn_one_time) < pong_btn_delay):
                    switch_to_pong_mode()
                else:
                    toggle_leds()
            if btn_one_state == True:
                btn_one_state = False
                toggle_leds()
        #pong mode
        elif stripe_mode == 1:
            #black out all pixels and change only the pixel of the current one to the pong color value
            clear_pixels(pixels)
            set_pixel_color(pixels, cur_pixel, pong_color_r, pong_color_g, pong_color_b)
            pixels.show()
            time.sleep(cur_pong_delay)

            #if the buttons get pressed to early or late we will abort the run
            abort_run = False

            player_one_miss = False
            if player_one_successfull_press == False:
                if btn_one_state == True:
                    btn_one_state = False
                    if (reverse_mode == False) or (cur_pixel - pong_tolerance) >= 0:
                        player_one_miss = True
                    else:
                        player_one_successfull_press = True
                elif ((reverse_mode == True) and (cur_pixel == 0)):
                    player_one_miss = True
            else:
                btn_one_state = False

            if player_one_miss == True:
                abort_run = True
                player_two_wins += 1
                if (player_two_wins >= pong_max_wins):
                    stripe_mode = 0
                    display_result(pong_wins_delay_after)
                    toggle_leds(False)
                else:
                    display_result(pong_wins_delay_during)
                    cur_pixel = 0
                    reverse_mode = False
                    cur_pong_delay = pong_init_delay

            player_two_miss = False
            if player_two_successfull_press == False:
                if btn_two_state == True:
                    btn_two_state = False
                    if (reverse_mode == True) or ((cur_pixel + pong_tolerance) <= (num_pong_leds - 1)):
                        player_two_miss = True
                    else:
                        player_two_successfull_press = True
                elif ((reverse_mode == False) and (cur_pixel == (num_pong_leds - 1))):
                    player_two_miss = True
            else:
                btn_two_state = False

            if player_two_miss == True:
                abort_run = True
                player_one_wins += 1
                if player_one_wins >= pong_max_wins:
                    stripe_mode = 0
                    display_result(pong_wins_delay_after)
                    toggle_leds(False)
                    btn_two_state = False
                    btn_one_state = False
                    player_one_successfull_press = False
                    player_two_successfull_press = False
                else:
                    display_result(pong_wins_delay_during)
                    cur_pixel = 0
                    reverse_mode = False
                    btn_two_state = False
                    btn_one_state = False
                    player_one_successfull_press = False
                    player_two_successfull_press = False
                    cur_pong_delay = pong_init_delay

            if abort_run == False:
                if reverse_mode == True:
                    cur_pixel -= 1
                    if cur_pixel < 0:
                        reverse_mode = False
                        player_one_successfull_press = False
                        cur_pixel = 1
                        cur_pong_delay = cur_pong_delay - pong_dec_per_run
                        if cur_pong_delay < pong_min_delay:
                            cur_pong_delay = pong_min_delay
                else:
                    cur_pixel += 1
                    if cur_pixel > (num_pong_leds - 1):
                        player_two_successfull_press = False
                        cur_pixel = num_pong_leds - 2
                        reverse_mode = True
                        cur_pong_delay = cur_pong_delay - pong_dec_per_run
                        if cur_pong_delay < pong_min_delay:
                            cur_pong_delay = pong_min_delay

#do some cleanup if the script gets killed
except KeyboardInterrupt:
    do_cleanup()


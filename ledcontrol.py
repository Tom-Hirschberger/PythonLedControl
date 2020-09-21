#! /usr/bin/env python3
import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import time
import paho.mqtt.client as mqtt
import json
import os

DEFAULT_MQTT_BROKER_ADDRESS="192.168.1.2"
DEFAULT_CLIENT_NAME="raspled"
DEFAULT_SPI_PORT=0
DEFAULT_SPI_DEVICE=0
DEFAULT_MAX_LEDS=160
DEFAULT_NUM_LEDS=160
DEFAULT_NUM_PONG_LEDS=10
DEFAULT_BTN_ONE_GPIO=17
DEFAULT_BTN_TWO_GPIO=27
DEFAULT_BTN_DEBOUNCE_DELAY=300
DEFAULT_PONG_BTN_DELAY=2
DEFAULT_PONG_MAX_WINS=2
DEFAULT_PONG_TOLERANCE=2
DEFAULT_PONG_INIT_LED_DELAY=0.5
DEFAULT_PONG_DEC_PER_RUN=0.05
DEFAULT_PONG_MIN_LED_DELAY=0.02
DEFAULT_PONG_RESULT_DELAY_DURING=2
DEFAULT_PONG_RESULT_DELAY_AFTER=5
DEFAULT_PONG_COLOR_R=0
DEFAULT_PONG_COLOR_B=255
DEFAULT_PONG_COLOR_G=0
DEFAULT_PONG_RESULT_COLOR_R=0
DEFAULT_PONG_RESULT_COLOR_G=255
DEFAULT_PONG_RESULT_COLOR_B=0
DEFAULT_COLOR_R=255
DEFAULT_COLOR_G=255
DEFAULT_COLOR_B=255

reverse_mode = False
cur_pixel = 0
btn_one_state = False
btn_one_time = 0
btn_two_state = False
btn_two_time = 0

num_leds = DEFAULT_NUM_LEDS
max_leds = DEFAULT_MAX_LEDS
stripe_mode = 0
stripe_on = False
color_r = DEFAULT_COLOR_R
color_g = DEFAULT_COLOR_G
color_b = DEFAULT_COLOR_B


pong_init_delay = DEFAULT_PONG_INIT_LED_DELAY
cur_pong_delay = pong_init_delay
num_pong_leds = DEFAULT_NUM_PONG_LEDS
pong_max_wins = DEFAULT_PONG_MAX_WINS
pong_wins_delay_during = DEFAULT_PONG_RESULT_DELAY_DURING
pong_wins_delay_after = DEFAULT_PONG_RESULT_DELAY_AFTER
pong_min_delay = DEFAULT_PONG_MIN_LED_DELAY
pong_dec_per_run = DEFAULT_PONG_DEC_PER_RUN
pong_btn_delay = DEFAULT_PONG_BTN_DELAY
pong_tolerance = DEFAULT_PONG_TOLERANCE
pong_color_r = DEFAULT_PONG_COLOR_R
pong_color_g = DEFAULT_PONG_COLOR_G
pong_color_b = DEFAULT_PONG_COLOR_B
pong_result_color_r = DEFAULT_PONG_RESULT_COLOR_R
pong_result_color_g = DEFAULT_PONG_RESULT_COLOR_G
pong_result_color_b = DEFAULT_PONG_RESULT_COLOR_B
player_one_wins = 0
player_one_successfull_press = False
player_two_wins = 0
player_two_successfull_press = False

# Alternatively specify a hardware SPI connection on /dev/spidev0.0:
spi_port   = os.getenv("SPI_PORT", DEFAULT_SPI_PORT)
spi_device = os.getenv("SPI_DEVICE", DEFAULT_SPI_DEVICE)
pixels = Adafruit_WS2801.WS2801Pixels(max_leds, spi=SPI.SpiDev(spi_port, spi_device))
pixels.clear()
pixels.show()

client_name = os.getenv("MQTT_CLIENT_NAME", DEFAULT_CLIENT_NAME)
mqtt_broker_address = os.getenv("MQTT_BROKER_ADDRESS", DEFAULT_MQTT_BROKER_ADDRESS)
mqtt_topic_prefix = os.getenv("MQTT_TOPIC_PREFIX", client_name+"/")

def callback_on_message(client, userdata, message):
    global mqtt_topic_prefix
    global pong_btn_delay, pong_init_delay, pong_min_delay, pong_dec_per_run
    global num_pong_leds, pong_tolerance
    global pong_max_wins, pong_wins_delay_after, pong_wins_delay_during
    global pong_color_r, pong_color_g, pong_color_b, pong_result_color_r, pong_result_color_g, pong_result_color_b
    global color_r, color_g, color_b
    message_str = str(message.payload.decode("utf-8"))
    print ("Received message %s for topic %s" %(message_str, message.topic))

    if message.topic == mqtt_topic_prefix+"output":
        if message_str == "on":
            toggle_leds(True)
        else:
            toggle_leds(False)
    elif message.topic == mqtt_topic_prefix+"pong/btn_delay":
        pong_btn_delay = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/init_delay":
        pong_init_delay = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/min_delay":
        pong_min_delay = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/dec_per_run":
        pong_dec_per_run = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/num_leds":
        num_pong_leds = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/max_wins":
        pong_max_wins = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/result/delay/during":
        pong_wins_delay_during = int(message_str)
    elif message.topic == mqtt_topic_prefix+"pong/result/delay/after":
        pong_wins_delay_after = int(message_str)
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
    elif message.topic == mqtt_topic_prefix+"color/g":
        color_g = int(message_str)
        if color_g > 255:
            color_g = 255
        elif color_g < 0:
            color_g = 0
    elif message.topic == mqtt_topic_prefix+"color/b":
        color_b = int(message_str)
        if color_b > 255:
            color_b = 255
        elif color_b < 0:
            color_b = 0
    elif message.topic == mqtt_topic_prefix+"get_status":
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

def callback_one(channel):
    global btn_one_time
    global btn_one_state
    btn_one_time  = time.time()
    btn_one_state = True
    

def callback_two(channel):
    global btn_two_time 
    global btn_two_state
    btn_two_time = time.time()
    btn_two_state = True

def toggle_leds(to_state = None):
    global stripe_on
    global pixels

    if to_state != None:
        if(to_state == False):
            stripe_on = True
        else:
            stripe_on = False
    
    if stripe_on == False:
        for i in range(0,num_leds):
            pixels.set_pixel_rgb(i, color_r, color_g, color_b)
        stripe_on = True
    else:
        pixels.clear()
        stripe_on = False

    pixels.show()

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

    pixels.clear()
    pixels.show()
    time.sleep(1)

    for i in range(0, num_pong_leds):
        pixels.set_pixel_rgb(i, pong_color_r, pong_color_g, pong_color_b)
    pixels.show()
    time.sleep(1)

    pixels.clear()
    pixels.show()
    time.sleep(1)

def display_result(cur_delay):
    global pixels
    global player_one_wins, player_two_wins
    global pong_result_color_r, pong_result_color_g, pong_result_color_b
    global num_pong_leds
    time.sleep(0.5)
    pixels.clear()
    for i in range(0, player_one_wins):
        pixels.set_pixel_rgb(i, pong_result_color_r , pong_result_color_g, pong_result_color_b)

    for i in range((num_pong_leds-player_two_wins), num_pong_leds):
        pixels.set_pixel_rgb(i, pong_result_color_r, pong_result_color_g, pong_result_color_b)

    pixels.show()
    time.sleep(cur_delay)

GPIO.setmode(GPIO.BCM)

GPIO.setup(17, GPIO.IN)
GPIO.setup(27, GPIO.IN)

channel_one = 17  # GPIO-Pin
channel_two = 27  # GPIO-Pin

GPIO.add_event_detect(channel_one, GPIO.RISING, callback=callback_one, bouncetime = DEFAULT_BTN_DEBOUNCE_DELAY)
GPIO.add_event_detect(channel_two, GPIO.RISING, callback=callback_two, bouncetime = DEFAULT_BTN_DEBOUNCE_DELAY)

client = mqtt.Client(client_name)
client.on_message=callback_on_message
client.connect(mqtt_broker_address)
client.subscribe(mqtt_topic_prefix+"get_status")
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
client.loop_start()

try:
  while True:
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
    elif stripe_mode == 1:
        pixels.clear()
        pixels.set_pixel_rgb(cur_pixel, pong_color_r, pong_color_g, pong_color_b)
        pixels.show()
        time.sleep(cur_pong_delay)

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
            else:
                display_result(pong_wins_delay_during)
                cur_pixel = 0
                reverse_mode = False
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


except KeyboardInterrupt:
  GPIO.cleanup()
  print ("Bye")


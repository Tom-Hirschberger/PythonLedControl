#!/usr/bin/env python3
import RPi.GPIO as GPIO
import Adafruit_WS2801
import Adafruit_GPIO.SPI as SPI
import time

DEFAULT_MAX_LEDS=160
DEFAULT_NUM_LEDS=160
DEFAULT_NUM_PONG_LEDS=10
DEFAULT_BTN_ONE_GPIO=17
DEFAULT_BTN_TWO_GPIO=27
DEFAULT_BTN_DEBOUNCE_DELAY=300
DEFAULT_DATA_PIN=0#FIXME
DEFAULT_CLOCK_PIN=0#FIXME
DEFAULT_PONG_BTN_DELAY=2
DEFAULT_PONG_MAX_WINS=2
DEFAULT_PONG_TOLERANCE=2
DEFAULT_PONG_INIT_LED_DELAY=0.5
DEFAULT_PONG_DEC_PER_RUN=0.05
DEFAULT_PONG_MIN_LED_DELAY=0.02
DEFAULT_PONG_RESULT_DELAY_DURING=2
DEFAULT_PONG_RESULT_DELAY_AFTER=5
DEFAULT_COLOR_R=255
DEFAULT_COLOR_G=255
DEFAULT_COLOR_B=255

reverse_mode = False
cur_pixel = 0
btn_one_state = False
btn_one_time = 0
btn_two_state = False
btn_two_time = 0

stripe_mode = 0
stripe_on = False
color_r = DEFAULT_COLOR_R
color_g = DEFAULT_COLOR_G
color_b = DEFAULT_COLOR_B


pong_init_delay = DEFAULT_PONG_INIT_LED_DELAY
cur_pong_delay = pong_init_delay
num_pong_leds = DEFAULT_NUM_PONG_LEDS
pong_max_wins = DEFAULT_PONG_MAX_WINS
pong_min_delay = DEFAULT_PONG_MIN_LED_DELAY
pong_dec_per_run = DEFAULT_PONG_DEC_PER_RUN
pong_btn_delay = DEFAULT_PONG_BTN_DELAY
pong_tolerance = DEFAULT_PONG_TOLERANCE
player_one_wins = 0
player_one_successfull_press = False
player_two_wins = 0
player_two_successfull_press = False

# Alternatively specify a hardware SPI connection on /dev/spidev0.0:
SPI_PORT   = 0
SPI_DEVICE = 0
pixels = Adafruit_WS2801.WS2801Pixels(DEFAULT_MAX_LEDS, spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE))
pixels.clear()
pixels.show()

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
        for i in range(0,DEFAULT_NUM_LEDS):
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
        pixels.set_pixel_rgb(i, 0, 0, 255)
    pixels.show()
    time.sleep(1)

    pixels.clear()
    pixels.show()
    time.sleep(1)

def display_result(cur_delay):
    global pixels
    global player_one_wins
    global player_two_wins
    global num_pong_leds
    time.sleep(0.5)
    pixels.clear()
    for i in range(0, player_one_wins):
        pixels.set_pixel_rgb(i, 0, 255, 0)

    for i in range((num_pong_leds-player_two_wins), num_pong_leds):
        pixels.set_pixel_rgb(i, 0, 255, 0)

    pixels.show()
    time.sleep(cur_delay)

GPIO.setmode(GPIO.BCM)

GPIO.setup(17, GPIO.IN)
GPIO.setup(27, GPIO.IN)

channel_one = 17  # GPIO-Pin
channel_two = 27  # GPIO-Pin

GPIO.add_event_detect(channel_one, GPIO.RISING, callback=callback_one, bouncetime = DEFAULT_BTN_DEBOUNCE_DELAY)
GPIO.add_event_detect(channel_two, GPIO.RISING, callback=callback_two, bouncetime = DEFAULT_BTN_DEBOUNCE_DELAY)

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
        pixels.set_pixel_rgb(cur_pixel, 0, 0, color_b)
        pixels.show()
        time.sleep(cur_pong_delay)

        abort_run = False
        player_one_miss = False

        if player_one_successfull_press == False:
            if btn_one_state == True:
                btn_one_state = False
                if (cur_pixel - pong_tolerance) >= 0:
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
                display_result(DEFAULT_PONG_RESULT_DELAY_AFTER)
                toggle_leds(False)
            else:
                display_result(DEFAULT_PONG_RESULT_DELAY_DURING)
                cur_pixel = 0
                reverse_mode = False
                cur_pong_delay = pong_init_delay

        player_two_miss = False
        if player_two_successfull_press == False:
            if btn_two_state == True:
                btn_two_state = False
                if ((cur_pixel + pong_tolerance) <= (num_pong_leds - 1)):
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
                display_result(DEFAULT_PONG_RESULT_DELAY_AFTER)
                toggle_leds(False)
            else:
                display_result(DEFAULT_PONG_RESULT_DELAY_DURING)
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


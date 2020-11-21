# PythonLedControl #
The aim of this project is to provide a script that controls an WS2801 or WS281X led strip connected to an Raspberry Pi board. Additionally to the strip two buttons are connected to the board to switch the led strip on or off. If the second button is pressed after the first button within a configurable time range the script will change to pong mode. A moving light will be started and the users need to press the buttons right before the light reaches the end of the strip. If the buttons are pressed in the right moment the moving light will turn the direction and the other user needs to press. Each time the moving light turns the direction the light gets faster.

The strip can be controlled either via hardware or software spi. The preferred mode is hardware spi because the timing is very sensitive.

**If you want to use an WS281X strip like i.e. WS2812B you can not use the build in sound output of the Raspberry Pi because both machnism use PWM. The installation guide will show you how to disable the kernel module of the on-board sound card!**

## Wiring ##
The strip uses 5V spi lanes but the Raspberry uses 3.3V. We need to use an level converter to get rid of this problem. Connecting the strip directly to the Pi may cause harm to it!

There are different possibilities to wire the buttons. I will show three examples.

### Wiring WS2801 ###
This example uses the hardware spi pins to connect the led strip.

![alt text](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-WS2801.png "Wiring WS2801")


### Wiring WS2813 ###
This example uses the GPIO21. 10, 12 and 18 are supported, also.

![Wiring WS2813](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-WS2813.png "Wiring WS2813")

### Wiring WS281X (except WS2813) ###
This example uses the GPIO21. 10, 12 and 18 are supported, also.

![Wiring WS281X](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-WS281X.png "Wiring WS281X")

### Wiring the Buttons with pull-down resistors ###
GPIO pins do not have an inital default state. To get one we connect an resistor to the ground and to the pin. The GPIO then is low and will be set to high if the switch is pressed and the connection to the VCC pin is closed.

![Two buttons pull-down](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-buttons-pulldown.png "Wiring the buttons with pull-down resistors")

You need to set "LED_BTN_TRIGGER_ON_HIGH=1" in the environment file to get this setup work (default)!

### Wiring the Buttons with pull-up resistors ###
GPIO pins do not have an inital default state. To get one we connect an resistor to the VCC and to the pin. The GPIO then is high and will be set to low if the switch is pressed and the connection to the ground pin is closed.

This setup is more robust against influnces of other electronical devices like frigerators or microwaves.

![Two buttons pull-up](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-buttons-pullup.png "Wiring the buttons with pull-up resistors")

You need to set "LED_BTN_TRIGGER_ON_HIGH=0" in the environment file to get this setup work!

### Wiring the Buttons with pull-up resistors and capacitors ###
GPIO pins do not have an inital default state. To get one we connect an resistor to the VCC and to the pin. The GPIO then is high and will be set to low if the switch is pressed and the connection to the ground pin is closed.

This setup is more robust against influnces of other electronical devices like frigerators or microwaves than the one which only uses pull-up resistors.

![Two buttons pull-up with capacitors](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/ledcontrol-buttons-pullup-withCapacitors.png "Wiring the buttons with pull-up resistors")

You need to set "LED_BTN_TRIGGER_ON_HIGH=0" in the environment file to get this setup work!

## Installation ##
### General###
```
    sudo apt-get install -y python3-pip git
    sudo pip3 install paho-mqtt

    git clone https://github.com/Tom-Hirschberger/PythonLedControl.git /home/pi/ledcontrol

    cd /home/pi/ledcontrol
    cp ledcontrol.env.example ledcontrol.env
    sudo cp /home/pi/ledcontrol/ledcontrol-root.service /etc/systemd/system/ledcontrol.service
    sudo systemctl enable ledcontrol
```

### WS2801 Strip ###
```
    sudo pip3 install adafruit-ws2801
```

Make sure the pi user is in the gpio and spi group:
```
    sudo usermod -a -G gpio,spi pi
```

Check that the spi bus is enabled:
```
    sudo raspi-config
```
![raspi-config main menu](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/screenshots/raspi-config-00-main.png "Main Menu")
![raspi-config main menu](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/screenshots/raspi-config-01-interfaceOptions.png "Interface Options")
![raspi-config main menu](https://github.com/Tom-Hirschberger/PythonLedControl/raw/master/screenshots/raspi-config-02-activateSPI.png "Activate SPI")

### WS281X Strip ###
```
    sudo pip3 install rpi_ws281x adafruit-circuitpython-neopixel
```

Make sure the root user is in the gpio group:
```
    sudo usermod -a -G gpio root
```

Make sure to disable the on-board sound card because both the strip and the sound card need to use PWM:
```
    sudo sed -i "s/^dtparam=audio=on/#dtparam=audio=on/g" /boot/config.txt
    sudo sed -i "s/^snd_bcm2835\s*$/#snd_bcm2835/g" /etc/modules
    echo 'blacklist snd_bcm2835' | sudo tee /etc/modprobe.d/blacklist-snd_bcm2835.conf
    sudo chmod u=rw,g=r,o=r /etc/modprobe.d/blacklist-snd_bcm2835.conf
```

## Configuration ##
Open the file /home/pi/ledcontrol/ledcontrol.env in your favorit editor. In example:

```
    nano /home/pi/ledcontrol/ledcontrol.env
```

### Options ###
```
    #The script supports both, a WS2801 strip that is connected using SPI or a WS281X strip connected to a "normal" gpio
    #If an LED_GPIO_PIN greater 0 is specified the WS281X routine is used if not the SPI routine
    #Attention: Only GPIO10, GPIO12, GPIO18 and GPIO21 are supported!!!
    LED_GPIO_PIN=-1
    #If WS281X option is used you can change RGB mapping from GRB to RGB if you like
    LED_RGB_MODE="GRB"

    #The connection to the WS2801 LED stripe can be established either by hardware or software spi
    #The default is hardware
    #Change the value of SPI_PORT to "" and specify the spi GPIO pins to activate the software spi
    SPI_PORT=0
    SPI_DEVICE=0

    #The clock and data pin to use for the software spi connection
    SPI_CLK_GPIO=""
    SPI_DATA_GPIO=""

    #Which name should the script use to register at the MQTT server?
    MQTT_CLIENT_NAME="raspled"
    #What is the hostname or ip of the MQTT server?
    MQTT_BROKER_ADDRESS="192.168.1.2"
    #Optional: Is there a login required to register to the MQTT server?
    MQTT_USERNAME=""
    MQTT_PASSWORD=""
    #Which prefix should be used for the MQTT topics?
    MQTT_TOPIC_PREFIX="raspled/"
    
    #To which GPIO pins are the buttons connected?
    LED_BTN_ONE_GPIO=17
    LED_BTN_TWO_GPIO=27
    #How many milliseconds should be waited before another press of the same button is accepted?
    LED_BTN_DEBOUNCE_DELAY=300
    #Should the button be triggerd on a high (default) or low value of the gpio
    LED_BTN_TRIGGER_ON_HIGH=1

    #How many leds does the connected led stripe have?
    LED_MAX_LEDS=160
    #How many of the leds should be used during "normal" operation?
    LED_NUM_LEDS=160
    
    #How many of the leds should be used in pong mode?
    LED_PONG_NUM_LEDS=10
    #How many wins are needed to win the whole game?
    LED_PONG_MAX_WINS=2
    #How many leds before the turn-around are presses of the buttons acceptable?
    LED_PONG_TOLERANCE=2
    
    #Which color is the default for the "normal" mode?
    LED_COLOR_R=255
    LED_COLOR_G=255
    LED_COLOR_B=255

    #If the led strip is shut off the state needs the be refreshed periodically at some led strips. The interval is set in seconds. Use a number smaller than 1 to deactivate this feature.
    LED_BLACK_COLOR_REFRESH_INTERVAL=30
    
    #Which color should be used for the pong running light?
    LED_PONG_COLOR_R=0
    LED_PONG_COLOR_G=0
    LED_PONG_COLOR_B=255
    
    #Which color shuld be used to display the result on the led strip?
    LED_PONG_RESULT_COLOR_R=0
    LED_PONG_RESULT_COLOR_G=255
    LED_PONG_RESULT_COLOR_B=0
    
    #How fast should the running light be at the beginning of each game (fraction support!)?
    LED_PONG_INIT_DELAY=0.5
    #Each time the light turns it gets faster. This value controls how many seconds it gets faster (fraction support!).
    LED_PONG_DEC_PER_RUN=0.05
    #What is the fastest speed that should be used in seconds (fraction support!)?
    LED_PONG_MIN_DELAY=0.02
    
    #If the second button is pressed after the first one within a delay that is less then this value the mode changes to pong
    LED_PONG_BTN_DELAY=2
    #How many seconds should the result be displayed between the single games (fraction support!)?
    LED_PONG_RESULT_DELAY_DURING=2
    #How many seconds should the final result be displayed (fraction support!)?
    LED_PONG_RESULT_DELAY_AFTER=5

    #Should the status be published after every config change? This is only needed if you use two different sources to change the configuration of the strip and want the second source to be updated if the first source changes a value.
    LED_PUBLISH_STATUS_AFTER_EVERY_CONFIG_CHANGE=0
    #Should the status be published if the output state changed? This feature is enabled because if one of the buttons gets pressed and you have an control source active the source gets informed that the output state changed.
    LED_PUBLISH_STATUS_IF_TOGGLED=1
    #Should the status be published at the script start?
    LED_PUBLISH_STATUS_AT_START=1
```

### MQTT Messages ###
The script can be configured during runtime by sending MQTT messages to your MQTT Broker. Be sure to send the messages with the configured prefix. The default is "raspled/" and will be used in the following examples.

#### /raspled/output ####
Switch the led strip on or off

"on" -> Switch all leds on

"off" -> Switch all leds off

anything else -> Toggle the status

#### /raspled/get_status ####
Trigger the script to send the current configuration als MQTT message to the topic "raspled/status". The message content will be in json format.
```json5
{
    "output": false,
    "mode": 0,
    "color_r": 255,
    "color_g": 255,
    "color_b": 255,
    "pong": {
        "btn_delay": 2.0,
        "init_delay": 0.5,
        "min_delay": 0.02,
        "dec_per_run": 0.05,
        "num_leds": 10,
        "max_wins": 2,
        "tolerance": 2,
        "result_delay_during": 2.0,
        "result_delay_after": 5.0,
        "color_r": 0,
        "color_g": 0,
        "color_b": 255,
        "result_color_r": 0,
        "result_color_g": 255,
        "result_color_b": 0
    },
}
```

#### /raspled/config ####
Send a configuration to this topic to change the values in the script during runtime. The configuration needs to be in the same json format as the raspled/status topic provides it. It is not neccessary to send a complete configuration. Missing values stay untouched.

#### /raspled/color/r ####
Send a integer value between 0 and 255 to this topic to change the red part of the normal color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/color/g ####
Send a integer value between 0 and 255 to this topic to change the green part of the normal color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/color/b ####
Send a integer value between 0 and 255 to this topic to change the blue part of the normal color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/num_leds ####
Send a value greater 0 and smaller than the maximum numbers of leds to this topic to change the number of leds that are used for the running light in pong mode. If the value is smaller than 0 it will be set to 0. If it is greater than the maximum numbers of leds it will be set to the maximum number of leds.

#### /raspled/pong/max_wins ####
Send a value between 1 and the number of pong leds minus one to this topic to change the number of wins that are needed to win the total game. If the value is smaller than 1 or greater than the number of pong leds minus one it will set to these values.

#### /raspled/pong/btn_delay ####
Configure the allowd delay in seconds between the press of the first button and the second one to switch to pong mode. Fractional values are allowed. Set the value to 0 to disable the pong mode.

#### /raspled/pong/init_delay ####
Configure how fast the running light will be after each game start. The delay is configured in seconds and fractional values are allowed. The amount of time will be waited between each led movement. If the initial delay is smaller than the minimum delay it will be set to the minimum delay.

#### /raspled/pong/dec_per_run ####
Configure the speedup after each turn around of the running light during pong mode.

#### /raspled/pong/min_delay ####
Configure the minimum delay between each led movement in pong mode.

#### /raspled/pong/tolerance ####
This topic configures how many leds before the turn around a button press is accaptable. If it is greater as the numbers of leds to use it will be set to this value.

#### /raspled/pong/color_r ####
Send a integer value between 0 and 255 to this topic to change the red part of the pong running light color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/color_g ####
Send a integer value between 0 and 255 to this topic to change the green part of the pong running light color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/color_b ####
Send a integer value between 0 and 255 to this topic to change the blue part of the pong running light color. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/result/color_r ####
Send a integer value between 0 and 255 to this topic to change the red part of color which is used to display the pong results. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/result/color_g ####
Send a integer value between 0 and 255 to this topic to change the green part of color which is used to display the pong results. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/result/color_b ####
Send a integer value between 0 and 255 to this topic to change the blue part of color which is used to display the pong results. If the value is smaller than 0 it will be set to 0. If it is greater than 255 it will be set to 255.

#### /raspled/pong/result/delay/during ####
Configures how many seconds the result should be displayed during the games.

#### /raspled/pong/result/delay/after ####
Configures how many seconds the final result should be displayed after the games.

## Startup ##
Because of the service file the script will be started automatically during system boot.

### Manuel stop ###
sudo systemctl stop ledcontrol

### Manuel restart ###
sudo systemctl restart ledcontrol

### Manuel start ###
sudo systemctl start ledcontrol

### Check the status ###
sudo systemctl status ledcontrol

### View the log messages ###
journalctl -u ledcontrol

### View the log messages in continous mode ###
journalctl -f -u ledcontrol
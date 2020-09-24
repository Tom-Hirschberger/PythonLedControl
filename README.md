# LedControl

## Wiring

## Installation
```
    sudo apt-get install -y python3-pip git
    sudo pip3 install adafruit-ws2801
    sudo pip3 install paho-mqtt

    git clone https://github.com/Tom-Hirschberger/PythonLedControl.git /home/pi/ledcontrol

    cd /home/pi/ledcontrol
    cp ledcontrol.env.example ledcontrol.env

    sudo ln -s /home/pi/ledcontrol/ledcontrol.service /etc/systemd/system/ledcontrol.service
    sudo systemctl enable ledcontrol
```

## Configuration
    Open the file /home/pi/ledcontrol/ledcontrol.env in your favorit editor. In example:

```
    nano /home/pi/ledcontrol/ledcontrol.env
```

### Options ###
| Option | Description | Type | Default |
| ------ | ----------- | ---- | ------- |
| MQTT_ACTIVE | If the script should be run without MQTT support this option can be used (0=disabled, 1=enabled). | Integer | 1 |
| MQTT_CLIENT_NAME | The name the client will be use while connecting to the MQTT Broker | String | "raspled" |
| MQTT_BROKER_ADDRESS | The hostname or ip address of your MQTT Broker | String | "192.168.1.2" |
| MQTT_TOPIC_PREFIX | The ledcontrol service not only reacts on button presses but also on MQTT messages. All these messages will be prefixed with this string | String | "raspled/" |
| LED_BTN_ONE_GPIO | The GPIO number the first button is connected to (GPIO not PIN number!). | Integer | 17 |
| LED_BTN_TWO_GPIO | The GPIO number the second button is connected to (GPIO not PIN number!) | Integer | 27 |


## MQTT Messages ##
The script can be configured during runtime by sending MQTT messages to your MQTT Broker. Be sure to send the messages with the configured prefix. The default is "raspled/" and will be used in the following examples.

### /raspled/output ###
Switch the led strip on or off

"on" -> Switch all leds on
"off" -> Switch all leds off

### /raspled/get_status ###
Fetch the current configuration als MQTT message with the data in json format. The message will be send to the topic "raspled/status"

### /raspled/config ###
### /raspled/color/r ###
### /raspled/color/g ###
### /raspled/color/b ###
### /raspled/pong/num_leds ###
### /raspled/pong/max_wins ###
### /raspled/pong/btn_delay ###
### /raspled/pong/init_delay ###
### /raspled/pong/dec_per_run ###
### /raspled/pong/min_delay ###
### /raspled/pong/tolerance ###
### /raspled/pong/color_r ###
### /raspled/pong/color_g ###
### /raspled/pong/color_b ###
### /raspled/pong/result/color_r ###
### /raspled/pong/result/color_g ###
### /raspled/pong/result/color_b ###
### /raspled/pong/result/delay/during ###
### /raspled/pong/result/delay/after ###

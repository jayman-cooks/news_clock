import time
import RPi.GPIO as GPIO
from datetime import datetime, timedelta
from luma.core.interface.serial import spi
from luma.lcd.device import st7735
from PIL import Image, ImageDraw, ImageFont
# GPIO Button Pins
BTN_UP = 5
BTN_DOWN = 6
BTN_LEFT = 13
BTN_RIGHT = 19
BTN_OK = 26

buttons = [BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT, BTN_OK]

GPIO.setmode(GPIO.BCM)
for btn in buttons:
    GPIO.setup(btn, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# screen setup
serial = spi(port=0, device=0, gpio_DC=24, gpio_RST=25, gpio_CS=8)
device = st7735(serial, width=160, height=128, rotate=0)
font = ImageFont.load_default()

# time handler
current_screen = "clock"
alarm_time = None
alarm_set = False
selected_index = 0  # for navigating hour/minute
set_time = [7, 0]   # Default alarm: 07:00

# Sound setup
BUZZER_PIN = 18
GPIO.setup(BUZZER_PIN, GPIO.OUT)
buzzer = GPIO.PWM(BUZZER_PIN, 440)  # Default 440 Hz

# Define a simple melody (notes in Hz and durations in sec)
melody = [
    (440, 0.3),  # A4
    (494, 0.3),  # B4
    (523, 0.3),  # C5
    (587, 0.3),  # D5
    (659, 0.3),  # E5
    (698, 0.3),  # F5
    (784, 0.6),  # G5
]


def draw_screen():
    image = Image.new("RGB", device.size, "black")
    draw = ImageDraw.Draw(image)

    now = datetime.now()
    draw.text((10, 10), f"Time: {now.strftime('%H:%M:%S')}", fill="white", font=font)

    if current_screen == "set_alarm":
        draw.text((10, 30), f"Set Alarm: {set_time[0]:02}:{set_time[1]:02}", fill="cyan", font=font)
        draw.rectangle((10 + selected_index * 40, 45, 50 + selected_index * 40, 60), outline="cyan")
    else:
        draw.text((10, 30), f"Alarm: {alarm_time.strftime('%H:%M') if alarm_time else '--:--'}",
                  fill="green" if alarm_set else "gray", font=font)

    device.display(image)

def read_buttons():
    return {
        "up": not GPIO.input(BTN_UP),
        "down": not GPIO.input(BTN_DOWN),
        "left": not GPIO.input(BTN_LEFT),
        "right": not GPIO.input(BTN_RIGHT),
        "ok": not GPIO.input(BTN_OK),
    }
def play_alarm_tune():
    buzzer.start(50)  # 50% duty cycle
    for freq, duration in melody:
        buzzer.ChangeFrequency(freq)
        time.sleep(duration)
    buzzer.stop()


try:
    while True:
        buttons = read_buttons()

        if buttons["ok"]:
            if current_screen == "clock":
                current_screen = "set_alarm"
            else:
                current_screen = "clock"
                alarm_time = datetime.now().replace(hour=set_time[0], minute=set_time[1], second=0, microsecond=0)
                alarm_set = True
            time.sleep(0.3)  # debounce

        if current_screen == "set_alarm":
            if buttons["left"]:
                selected_index = max(0, selected_index - 1)
                time.sleep(0.2)
            if buttons["right"]:
                selected_index = min(1, selected_index + 1)
                time.sleep(0.2)
            if buttons["up"]:
                set_time[selected_index] = (set_time[selected_index] + 1) % (24 if selected_index == 0 else 60)
                time.sleep(0.2)
            if buttons["down"]:
                set_time[selected_index] = (set_time[selected_index] - 1) % (24 if selected_index == 0 else 60)
                time.sleep(0.2)

        # Check for alarm
        now = datetime.now()
        if alarm_set and now.hour == alarm_time.hour and now.minute == alarm_time.minute and now.second == 0:
            print("⏰ ALARM RINGING!")
            play_alarm_tune()
            alarm_set = False

        draw_screen()
        time.sleep(0.1)

except KeyboardInterrupt:
    GPIO.cleanup()
    device.clear()

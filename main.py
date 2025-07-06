import machine
import st7789
import time
import utime
import random
import sys
import os
import urequests
import ubinascii
import ujson
from machine import Pin, SPI, PWM
import uos
import network
from news import get_headlines

# =============================================================================
# ESP32 HARDWARE IMPLEMENTATION WITH BLUETOOTH AUDIO
# =============================================================================
class AlarmClockESP32:
    def __init__(self):
        # Initialize display
        self.width = 170
        self.height = 320
        self.init_display()

        # Initialize buttons
        self.init_buttons()

        # Initialize Wi-Fi
        self.wifi_connected = False
        self.connect_wifi()

        # Alarm state
        self.alarm_time = (7, 30)  # (hour, minute)
        self.alarm_enabled = True
        self.alarm_ringing = False
        self.setting_mode = False
        self.setting_index = 0  # 0=hour, 1=minute
        self.last_alarm_trigger = 0

        # Bluetooth state
        self.bt_speaker_connected = False
        self.init_bluetooth()

    def init_display(self):
        """Initialize ST7789 display"""
        spi = SPI(
            2,
            baudrate=40000000,
            sck=Pin(18),
            mosi=Pin(23),
            miso=Pin(19)
        )
        self.disp = st7789.ST7789(
            spi,
            self.width,
            self.height,
            reset=Pin(4, Pin.OUT),
            dc=Pin(2, Pin.OUT),
            cs=Pin(5, Pin.OUT),
            backlight=Pin(12, Pin.OUT),
            rotation=1,
        )
        self.disp.init()
        self.disp.fill(st7789.BLACK)

    def init_buttons(self):
        """Initialize buttons with debounce"""
        self.buttons = {
            "MODE": Pin(32, Pin.IN, Pin.PULL_UP),
            "UP": Pin(33, Pin.IN, Pin.PULL_UP),
            "DOWN": Pin(25, Pin.IN, Pin.PULL_UP),
            "SET": Pin(26, Pin.IN, Pin.PULL_UP),
            "ALARM": Pin(27, Pin.IN, Pin.PULL_UP),
        }
        self.last_button_state = {name: 1 for name in self.buttons}
        self.last_debounce_time = {name: 0 for name in self.buttons}
        self.debounce_delay = 50  # ms

    def connect_wifi(self):
        """Connect to Wi-Fi for TTS service"""
        ssid = "YOUR_WIFI_SSID"
        password = "YOUR_WIFI_PASSWORD"

        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        if not wlan.isconnected():
            print("Connecting to Wi-Fi...")
            wlan.connect(ssid, password)

            # Wait for connection
            for _ in range(20):
                if wlan.isconnected():
                    break
                time.sleep(1)

        self.wifi_connected = wlan.isconnected()
        if self.wifi_connected:
            print("Wi-Fi connected:", wlan.ifconfig())
        else:
            print("Wi-Fi connection failed")

    def init_bluetooth(self):
        """Initialize Bluetooth A2DP sink"""
        try:
            import a2dp
            # Initialize A2DP sink
            self.a2dp = a2dp.A2dpSink()
            self.a2dp.start()
            print("Bluetooth A2DP sink started. Device name:", self.a2dp.get_device_name())
            print("Pair with your speaker and connect to ESP32")
            self.bt_available = True
        except ImportError:
            print("a2dp library not available")
            self.bt_available = False
        except Exception as e:
            print("Bluetooth init failed:", str(e))
            self.bt_available = False

    def is_bluetooth_connected(self):
        """Check if Bluetooth speaker is connected"""
        if not self.bt_available:
            return False
        return self.a2dp.is_connected()

    def get_message_text(self):
        """Generate message text for TTS"""
        quotes = [
            "Good morning! Time to start your day.",
            "Rise and shine! A new day awaits.",
            "Wake up! Your adventures begin now.",
            "Hello world! Time to be productive."
        ]
        return get_headlines()

    def text_to_speech(self, text):
        """Convert text to speech using Google TTS"""
        if not self.wifi_connected:
            print("Wi-Fi not connected. Cannot use TTS")
            return None

        try:
            # Google TTS API endpoint
            url = "http://translate.google.com/translate_tts"

            # Request parameters
            params = {
                'ie': 'UTF-8',
                'q': text,
                'tl': 'en',
                'client': 'tw-ob'
            }

            # Headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
            }

            # Send request
            response = urequests.get(url, params=params, headers=headers)

            if response.status_code == 200:
                return response.content
            else:
                print("TTS request failed:", response.status_code)
                return None

        except Exception as e:
            print("TTS error:", str(e))
            return None

    def play_audio(self, audio_data):
        """Play audio through Bluetooth speaker"""
        if not self.bt_available or not self.is_bluetooth_connected():
            print("Bluetooth not available or speaker not connected")
            return False

        try:
            print("Playing audio...")
            self.a2dp.play(audio_data)
            return True
        except Exception as e:
            print("Playback failed:", str(e))
            return False

    def trigger_alarm(self):
        """Trigger alarm with TTS over Bluetooth"""
        self.alarm_ringing = True
        message = self.get_message_text()
        print("ALARM! Message:", message)

        # Get TTS audio
        audio = self.text_to_speech(message)

        if audio:
            # Play through Bluetooth
            if not self.play_audio(audio):
                print("Failed to play through Bluetooth")
        else:
            print("TTS generation failed")

    def update_display(self):
        """Update the physical display"""
        # Get current time
        current_time = utime.localtime()
        time_str = "{:02d}:{:02d}:{:02d}".format(
            current_time[3], current_time[4], current_time[5]
        )

        # Clear display
        self.disp.fill(st7789.BLACK)

        # Draw time
        self.disp.text(
            "Arial_16",
            time_str,
            60,
            40,
            st7789.WHITE,
            st7789.BLACK
        )

        # Draw alarm status
        alarm_status = "Alarm: {:02d}:{:02d}".format(
            self.alarm_time[0], self.alarm_time[1]
        )
        self.disp.text(
            "Arial_16",
            alarm_status,
            60,
            80,
            st7789.GREEN if self.alarm_enabled else st7789.RED,
            st7789.BLACK
        )

        # Draw setting indicator
        if self.setting_mode:
            mode_text = ["SET HOUR", "SET MINUTE"][self.setting_index]
            self.disp.text(
                "Arial_16",
                mode_text,
                60,
                120,
                st7789.YELLOW,
                st7789.BLACK
            )

        # Draw connection status
        bt_status = "BT: " + ("Connected" if self.is_bluetooth_connected() else "Disconnected")
        self.disp.text(
            "Arial_16",
            bt_status,
            60,
            150,
            st7789.CYAN if self.is_bluetooth_connected() else st7789.RED,
            st7789.BLACK
        )

        # Draw alarm ringing indicator
        if self.alarm_ringing:
            self.disp.text(
                "Arial_16",
                "ALARM!",
                200,
                40,
                st7789.RED,
                st7789.BLACK
            )

    def check_buttons(self):
        """Check button states with debounce"""
        current_time = utime.ticks_ms()
        for name, button in self.buttons.items():
            current_state = button.value()

            # Reset button state if debounce time has passed
            if current_state != self.last_button_state[name]:
                self.last_debounce_time[name] = current_time

            if (current_time - self.last_debounce_time[name]) > self.debounce_delay:
                if current_state == 0 and self.last_button_state[name] == 1:
                    self.handle_button(name)

            self.last_button_state[name] = current_state

    def handle_button(self, name):
        """Handle button press"""
        if name == "MODE":  # MODE button
            self.setting_mode = not self.setting_mode
            self.setting_index = 0

        elif name == "UP":  # UP button
            if self.setting_mode:
                if self.setting_index == 0:
                    self.alarm_time = ((self.alarm_time[0] + 1) % 24, self.alarm_time[1])
                else:
                    self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] + 1) % 60)

        elif name == "DOWN":  # DOWN button
            if self.setting_mode:
                if self.setting_index == 0:
                    self.alarm_time = ((self.alarm_time[0] - 1) % 24, self.alarm_time[1])
                else:
                    self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] - 1) % 60)

        elif name == "SET":  # SET button
            if self.setting_mode:
                self.setting_index = (self.setting_index + 1) % 2
            elif self.alarm_ringing:
                self.alarm_ringing = False

        elif name == "ALARM":  # ALARM ON/OFF button
            self.alarm_enabled = not self.alarm_enabled

    def check_alarm(self):
        """Check if alarm should trigger"""
        current_time = utime.localtime()
        current_hour = current_time[3]
        current_minute = current_time[4]
        current_second = current_time[5]

        # Only trigger once per minute
        if (self.alarm_enabled and
                current_hour == self.alarm_time[0] and
                current_minute == self.alarm_time[1] and
                current_second < 5 and  # Trigger during first 5 seconds of the minute
                not self.alarm_ringing and
                time.time() - self.last_alarm_trigger > 55):  # Prevent retriggering

            self.last_alarm_trigger = time.time()
            threading.Thread(target=self.trigger_alarm).start()

    def run(self):
        """Main hardware loop"""
        try:
            while True:
                self.check_buttons()
                self.check_alarm()
                self.update_display()
                time.sleep(0.1)
        except KeyboardInterrupt:
            if hasattr(self, 'a2dp') and self.bt_available:
                self.a2dp.stop()
            self.disp.fill(st7789.BLACK)


# =============================================================================
# SIMULATION MODULE (For Computer Testing)
# =============================================================================
class AlarmClockSimulator:
    def __init__(self):
        # Initialize pygame for simulation
        import pygame
        pygame.init()
        self.screen = pygame.display.set_mode((320, 170))
        pygame.display.set_caption("Alarm Clock Simulator")
        self.font = pygame.font.SysFont('Arial', 24)
        self.small_font = pygame.font.SysFont('Arial', 18)
        self.clock = pygame.time.Clock()

        # Button positions (x, y, width, height)
        self.buttons = [
            {"rect": pygame.Rect(10, 130, 50, 30), "label": "MODE"},
            {"rect": pygame.Rect(70, 130, 50, 30), "label": "+"},
            {"rect": pygame.Rect(130, 130, 50, 30), "label": "-"},
            {"rect": pygame.Rect(190, 130, 50, 30), "label": "SET"},
            {"rect": pygame.Rect(250, 130, 50, 30), "label": "ALARM"}
        ]

        # Alarm state
        self.current_time = time.localtime()
        self.alarm_time = (7, 30)  # (hour, minute)
        self.alarm_enabled = True
        self.alarm_ringing = False
        self.setting_mode = False  # True when setting alarm time
        self.setting_index = 0  # 0=hour, 1=minute
        self.bt_connected = False

    def get_message_text(self):
        """Generate message text for TTS"""
        quotes = [
            "Good morning! Time to start your day.",
            "Rise and shine! A new day awaits.",
            "Wake up! Your adventures begin now.",
            "Hello world! Time to be productive."
        ]
        return get_headlines()

    def update_display(self):
        """Update the simulation display"""
        self.screen.fill((0, 0, 0))  # Clear screen

        # Draw current time
        time_str = time.strftime("%H:%M:%S", self.current_time)
        time_surface = self.font.render(time_str, True, (255, 255, 255))
        self.screen.blit(time_surface, (100, 30))

        # Draw alarm status
        alarm_status = f"Alarm: {self.alarm_time[0]:02d}:{self.alarm_time[1]:02d}"
        alarm_surface = self.small_font.render(alarm_status, True,
                                               (0, 255, 0) if self.alarm_enabled else (255, 0, 0))
        self.screen.blit(alarm_surface, (100, 70))

        # Draw setting indicator
        if self.setting_mode:
            mode_text = ["SET HOUR", "SET MINUTE"][self.setting_index]
            mode_surface = self.small_font.render(mode_text, True, (255, 255, 0))
            self.screen.blit(mode_surface, (100, 100))

        # Draw Bluetooth status
        bt_status = "BT: " + ("Connected" if self.bt_connected else "Disconnected")
        bt_surface = self.small_font.render(bt_status, True,
                                            (0, 255, 255) if self.bt_connected else (255, 0, 0))
        self.screen.blit(bt_surface, (100, 140))

        # Draw alarm ringing indicator
        if self.alarm_ringing:
            ring_surface = self.font.render("ALARM!", True, (255, 0, 0))
            self.screen.blit(ring_surface, (220, 30))

        # Draw buttons
        for button in self.buttons:
            pygame.draw.rect(self.screen, (50, 50, 50), button["rect"])
            pygame.draw.rect(self.screen, (200, 200, 200), button["rect"], 2)
            label_surface = self.small_font.render(button["label"], True, (255, 255, 255))
            self.screen.blit(label_surface,
                             (button["rect"].centerx - label_surface.get_width() // 2,
                              button["rect"].centery - label_surface.get_height() // 2))

        pygame.display.flip()

    def handle_button(self, index):
        """Handle button press in simulation"""
        if index == 0:  # MODE
            self.setting_mode = not self.setting_mode
            self.setting_index = 0

        elif index == 1:  # +
            if self.setting_mode:
                if self.setting_index == 0:
                    self.alarm_time = ((self.alarm_time[0] + 1) % 24, self.alarm_time[1])
                else:
                    self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] + 1) % 60)

        elif index == 2:  # -
            if self.setting_mode:
                if self.setting_index == 0:
                    self.alarm_time = ((self.alarm_time[0] - 1) % 24, self.alarm_time[1])
                else:
                    self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] - 1) % 60)

        elif index == 3:  # SET
            if self.setting_mode:
                self.setting_index = (self.setting_index + 1) % 2
            elif self.alarm_ringing:
                self.alarm_ringing = False

        elif index == 4:  # ALARM ON/OFF
            self.alarm_enabled = not self.alarm_enabled
            # Simulate Bluetooth connection
            if self.alarm_enabled:
                self.bt_connected = True
            else:
                self.bt_connected = False

    def check_alarm(self):
        """Check if alarm should trigger"""
        self.current_time = time.localtime()
        if (self.alarm_enabled and not self.alarm_ringing and
                self.current_time.tm_hour == self.alarm_time[0] and
                self.current_time.tm_min == self.alarm_time[1] and
                self.current_time.tm_sec == 0):
            self.alarm_ringing = True
            message = self.get_message_text()
            print(f"ALARM! Message: {message} (would play through Bluetooth)")

    def run_simulation(self):
        """Main simulation loop"""
        import pygame
        running = True
        while running:
            # Update time
            self.current_time = time.localtime()

            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    for i, button in enumerate(self.buttons):
                        if button["rect"].collidepoint(pos):
                            self.handle_button(i)

            # Check alarm
            self.check_alarm()

            # Update display
            self.update_display()
            self.clock.tick(30)  # 30 FPS

        pygame.quit()


# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    # Check if we're running on ESP32 or in simulation
    if sys.platform == 'esp32':
        print("Running on ESP32 hardware...")
        clock = AlarmClockESP32()
        clock.run()
    else:
        print("Running in simulation mode...")
        simulator = AlarmClockSimulator()
        simulator.run_simulation()
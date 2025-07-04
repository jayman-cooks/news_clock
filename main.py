import time
import datetime
import threading
import pygame
import os
import random
import sys
from news import get_headlines
from PIL import Image, ImageDraw, ImageFont


# =============================================================================
# SIMULATION MODULE (For Computer Testing)
# =============================================================================
class AlarmClockSimulator:
    def __init__(self):
        # Initialize pygame for simulation
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
        self.current_time = datetime.datetime.now()
        self.alarm_time = (7, 30)  # (hour, minute)
        self.alarm_enabled = True
        self.alarm_ringing = False
        self.setting_mode = False  # True when setting alarm time
        self.setting_index = 0  # 0=hour, 1=minute

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
        time_str = self.current_time.strftime("%H:%M:%S")
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

    def check_alarm(self):
        """Check if alarm should trigger"""
        if (self.alarm_enabled and not self.alarm_ringing and
                self.current_time.hour == self.alarm_time[0] and
                self.current_time.minute == self.alarm_time[1] and
                self.current_time.second == 0):
            self.alarm_ringing = True
            message = self.get_message_text()
            print(f"ALARM! Message: {message}")
            # In real implementation, this would trigger TTS

    def run_simulation(self):
        """Main simulation loop"""
        running = True
        while running:
            # Update time
            self.current_time = datetime.datetime.now()

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
# HARDWARE IMPLEMENTATION (For Raspberry Pi)
# =============================================================================
class AlarmClockHardware:
    def __init__(self):
        # Display setup
        self.disp = self.setup_display()
        self.width = 170
        self.height = 320
        self.image = Image.new('RGB', (self.height, self.width), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        try:
            self.font_large = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
            self.font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
        except:
            # Fallback fonts
            self.font_large = ImageFont.load_default()
            self.font_small = ImageFont.load_default()

        # Button setup
        self.buttons = self.setup_buttons()

        # Alarm state
        self.alarm_time = (7, 30)  # (hour, minute)
        self.alarm_enabled = True
        self.alarm_ringing = False
        self.setting_mode = False
        self.setting_index = 0  # 0=hour, 1=minute

        # Text-to-Speech setup
        self.setup_tts()

    def setup_display(self):
        """Initialize SPI display"""
        try:
            import ST7789
            disp = ST7789.ST7789(
                port=0,
                cs=0,  # Change if using different CS pin
                dc=24,
                rst=25,
                backlight=5,
                width=170,
                height=320,
                rotation=90,
                spi_speed_hz=60 * 1000 * 1000
            )
            return disp
        except ImportError:
            print("Display driver not found. Running in simulation mode.")
            return None
        except Exception as e:
            print(f"Display initialization failed: {str(e)}")
            return None

    def setup_buttons(self):
        """Initialize GPIO buttons"""
        try:
            import RPi.GPIO as GPIO
            GPIO.setmode(GPIO.BCM)
            buttons = {
                "MODE": 5,
                "UP": 6,
                "DOWN": 13,
                "SET": 19,
                "ALARM": 26
            }
            for pin in buttons.values():
                GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            return buttons
        except ImportError:
            print("GPIO library not found. Buttons disabled.")
            return None
        except Exception as e:
            print(f"Button initialization failed: {str(e)}")
            return None

    def setup_tts(self):
        """Initialize text-to-speech"""
        try:
            import pyttsx3
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)
            self.tts_engine.setProperty('volume', 1.0)
        except ImportError:
            print("pyttsx3 not installed. TTS disabled.")
            self.tts_engine = None
        except Exception as e:
            print(f"TTS initialization failed: {str(e)}")
            self.tts_engine = None

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
        """Update the physical display"""
        if not self.disp:
            return

        # Clear display
        self.draw.rectangle((0, 0, self.height, self.width), fill=(0, 0, 0))

        # Get current time
        current_time = datetime.datetime.now()
        time_str = current_time.strftime("%H:%M:%S")

        # Draw time
        self.draw.text((60, 40), time_str, font=self.font_large, fill=(255, 255, 255))

        # Draw alarm status
        alarm_status = f"Alarm: {self.alarm_time[0]:02d}:{self.alarm_time[1]:02d}"
        self.draw.text((60, 100), alarm_status, font=self.font_small,
                       fill=(0, 255, 0) if self.alarm_enabled else (255, 0, 0))

        # Draw setting indicator
        if self.setting_mode:
            mode_text = ["SET HOUR", "SET MINUTE"][self.setting_index]
            self.draw.text((60, 130), mode_text, font=self.font_small, fill=(255, 255, 0))

        # Draw alarm ringing indicator
        if self.alarm_ringing:
            self.draw.text((200, 40), "ALARM!", font=self.font_large, fill=(255, 0, 0))

        # Update display
        self.disp.display(self.image)

    def check_buttons(self):
        """Check button states"""
        if not self.buttons:
            return

        try:
            import RPi.GPIO as GPIO
            # MODE button
            if GPIO.input(self.buttons["MODE"]) == GPIO.LOW:
                self.setting_mode = not self.setting_mode
                self.setting_index = 0
                time.sleep(0.2)

            # UP button
            if GPIO.input(self.buttons["UP"]) == GPIO.LOW:
                if self.setting_mode:
                    if self.setting_index == 0:
                        self.alarm_time = ((self.alarm_time[0] + 1) % 24, self.alarm_time[1])
                    else:
                        self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] + 1) % 60)
                time.sleep(0.1)

            # DOWN button
            if GPIO.input(self.buttons["DOWN"]) == GPIO.LOW:
                if self.setting_mode:
                    if self.setting_index == 0:
                        self.alarm_time = ((self.alarm_time[0] - 1) % 24, self.alarm_time[1])
                    else:
                        self.alarm_time = (self.alarm_time[0], (self.alarm_time[1] - 1) % 60)
                time.sleep(0.1)

            # SET button
            if GPIO.input(self.buttons["SET"]) == GPIO.LOW:
                if self.setting_mode:
                    self.setting_index = (self.setting_index + 1) % 2
                elif self.alarm_ringing:
                    self.alarm_ringing = False
                time.sleep(0.2)

            # ALARM ON/OFF button
            if GPIO.input(self.buttons["ALARM"]) == GPIO.LOW:
                self.alarm_enabled = not self.alarm_enabled
                time.sleep(0.2)

        except Exception as e:
            print(f"Button error: {str(e)}")

    def trigger_alarm(self):
        """Trigger alarm with text-to-speech"""
        if not self.alarm_ringing:
            return

        if self.tts_engine:
            message = self.get_message_text()
            try:
                self.tts_engine.say(message)
                self.tts_engine.runAndWait()
            except Exception as e:
                print(f"TTS failed: {str(e)}")
        else:
            print("ALARM! (TTS unavailable)")

    def check_alarm(self):
        """Check if alarm should trigger"""
        current_time = datetime.datetime.now()
        if (self.alarm_enabled and not self.alarm_ringing and
                current_time.hour == self.alarm_time[0] and
                current_time.minute == self.alarm_time[1] and
                current_time.second == 0):
            self.alarm_ringing = True
            # Run TTS in a separate thread to avoid blocking
            threading.Thread(target=self.trigger_alarm, daemon=True).start()

    def run(self):
        """Main hardware loop"""
        try:
            while True:
                self.check_buttons()
                self.check_alarm()
                self.update_display()
                time.sleep(0.1)
        except KeyboardInterrupt:
            if self.buttons:
                import RPi.GPIO as GPIO
                GPIO.cleanup()


# =============================================================================
# MAIN EXECUTION
# =============================================================================
if __name__ == "__main__":
    if os.name == 'nt' or os.name == 'posix' and 'DISPLAY' in os.environ:
        print("Running in simulation mode...")
        simulator = AlarmClockSimulator()
        simulator.run_simulation()
    else:
        print("Running on hardware...")
        clock = AlarmClockHardware()
        clock.run()
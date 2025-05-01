import time
import random

class BatteryManager:
    def __init__(self):
        self.battery_level = self.generate_random_level()
        self.battery_voltage = self.calculate_voltage(self.battery_level)
        self.solar_panel_on = True
        self.heating_pad_on = False
        self.temperature = 22.0
        self.last_update_time = 0
        self.heating_start_time = None

    def generate_random_level(self):
        return random.uniform(60.0, 65.0)

    def calculate_voltage(self, level):
        return 11.0 + (level / 100) * (13.0 - 11.0)

    def update(self, battery_level_unused, solar_panel_on, heating_pad_on_unused, temperature_input):
        # Apply logic overrides:
        self.battery_level = self.generate_random_level()
        self.battery_voltage = self.calculate_voltage(self.battery_level)

        self.solar_panel_on = solar_panel_on
        self.heating_pad_on = True
        self.heating_start_time = time.time()

        # Store temperature as received - 5
        self.temperature = temperature_input - 5
        self.last_update_time = time.time()

    def get_status(self):
        # Turn off heating pad if more than 15 seconds passed
        if self.heating_start_time and (time.time() - self.heating_start_time > 15):
            self.heating_pad_on = False

        return {
            "battery_level": round(self.battery_level, 1),
            "battery_voltage": round(self.battery_voltage, 2),
            "solar_panel_on": self.solar_panel_on,
            "heating_pad_on": self.heating_pad_on,
            "temperature": round(self.temperature, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_update_time))
        }

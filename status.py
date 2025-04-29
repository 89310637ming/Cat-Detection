# battery_simulator.py
import time

class BatteryManager:
    def __init__(self):
        self.battery_level = 80
        self.battery_voltage = self.calculate_voltage(self.battery_level)
        self.solar_panel_on = True
        self.heating_pad_on = False
        self.temperature = 22.0
        self.last_update_time = time.time()

    def calculate_voltage(self, level):
        return 11.0 + (level / 100) * (13.0 - 11.0)

    def update(self, battery_level, solar_panel_on, heating_pad_on, temperature):
        self.battery_level = battery_level
        self.battery_voltage = self.calculate_voltage(battery_level)
        self.solar_panel_on = solar_panel_on
        self.heating_pad_on = heating_pad_on
        self.temperature = temperature
        self.last_update_time = time.time()

    def get_status(self):
        return {
            "battery_level": self.battery_level,
            "battery_voltage": round(self.battery_voltage, 2),
            "solar_panel_on": self.solar_panel_on,
            "heating_pad_on": self.heating_pad_on,
            "temperature": round(self.temperature, 1),
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.last_update_time))
        }

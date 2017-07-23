from .device import Device
from typing import Any, Dict


class AirPurifier(Device):
    """Main class representing the air purifier."""

    def status(self):
        """Retrieve properties."""

        # A few more properties:
        properties = ['power', 'aqi', 'humidity', 'temp_dec',
                      'mode', 'led', 'led_b', 'buzzer', 'child_lock',
                      'limit_hum', 'trans_level', 'bright',
                      'favorite_level', 'filter1_life', 'act_det',
                      'f1_hour_used', 'use_time', 'motor1_speed']

        values = self.send(
            "get_prop",
            properties
        )
        return AirPurifierStatus(dict(zip(properties, values)))

    def set_mode(self, mode: str):
        """Set mode."""

        # auto, silent, favorite, medium, high, strong, idle
        return self.send("set_mode", [mode])

    def set_favorite_level(self, level: int):
        """Set favorite level."""

        # Set the favorite level used when the mode is `favorite`,
        # should be  between 0 and 16.
        return self.send("favorite_level", [level])  # 0 ... 16

    def set_led_brightness(self, brightness: int):
        """Set led brightness."""

        # bright: 0, dim: 1, off: 2
        return self.send("set_led_b", [brightness])

    def set_led(self, led: bool):
        """Turn led on/off."""

        if led:
            return self.send("set_led", ['on'])
        else:
            return self.send("set_led", ['off'])

    def set_buzzer(self, buzzer: bool):
        """Set buzzer."""

        if buzzer:
            return self.send("set_mode", ["on"])
        else:
            return self.send("set_mode", ["off"])

    def set_humidity_limit(self, limit: int):
        """Set humidity limit."""

        # 40, 50, 60, 70 or 80
        return self.send("set_limit_hum", [limit])


class AirPurifierStatus:
    """Container for status reports from the air purifier."""
    def __init__(self, data: Dict[str, Any]) -> None:
        # ['power', 'aqi', 'humidity', 'temp_dec',
        #  'mode', 'led', 'led_b', 'buzzer', 'child_lock',
        #  'limit_hum', 'trans_level', 'bright',
        #  'favorite_level', 'filter1_life', 'act_det',
        #  'f1_hour_used', 'use_time', 'motor1_speed']
        self.data = data

    @property
    def power(self) -> str:
        return self.data["power"]

    @property
    def is_on(self) -> bool:
        return self.power == "on"

    @property
    def aqi(self) -> int:
        return self.data["aqi"]

    @property
    def humidity(self) -> int:
        return self.data["humidity"]

    @property
    def temperature(self) -> float:
        return self.data["temp_dec"] / 10.0

    @property
    def mode(self) -> str:
        # auto, silent, favorite, medium, high, strong, idle
        return self.data["mode"]

    @property
    def led(self) -> bool:
        return self.data["led"] == "on"

    @property
    def led_b(self) -> str:
        brightness_levels = {
            0: "bright",
            1: "dim",
            2: "off"
        }
        return brightness_levels[self.data["led_b"]]

    @property
    def buzzer(self) -> bool:
        return self.data["buzzer"] == "on"

    @property
    def child_lock(self) -> str:
        return self.data["child_lock"]

    @property
    def limit_hum(self) -> str:
        return self.data["limit_hum"]

    @property
    def trans_level(self) -> str:
        return self.data["trans_level"]

    @property
    def bright(self) -> int:
        return self.data["bright"]

    @property
    def favorite_level(self) -> str:
        # Favorite level used when the mode is `favorite`. Between 0 and 16.
        return self.data["favorite_level"]

    @property
    def filter_life_remaining(self) -> int:
        return self.data["filter1_life"]

    @property
    def act_det(self) -> bool:
        return self.data["act_det"] == "on"

    @property
    def filter_hours_used(self) -> int:
        return self.data["f1_hour_used"]

    @property
    def use_time(self) -> int:
        return self.data["use_time"]

    @property
    def motor_speed(self) -> int:
        return self.data["motor1_speed"]

    def __str__(self) -> str:
        s = "<AirPurifierStatus power=%s, aqi=%s temperature=%s%%, " \
            "humidity=%s%% mode=%s%%, led=%s%% , led_b=%s%% buzzer=%s%%, " \
            "child_lock=%s%%, limit_hum=%s%%, trans_level=%s%%, " \
            "bright=%s%%, favorite_level=%s%%, filter_life_remaining=%s%%, " \
            "act_det=%s%%, filter_hours_used=%s%%, use_time=%s%%, " \
            "motor_speed=%s%%>" % \
            (self.power, self.aqi, self.temperature,
             self.humidity, self.mode, self.led, self.led_b, self.buzzer,
             self.child_lock, self.limit_hum, self.trans_level,
             self.bright, self.favorite_level, self.filter_life_remaining,
             self.act_det, self.filter_hours_used, self.use_time,
             self.motor_speed)
        return s
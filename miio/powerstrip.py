import enum
import logging
from collections import defaultdict
from typing import Dict, Any, Optional

import click

from .click_common import command, format_output, EnumType
from .device import Device, DeviceException

_LOGGER = logging.getLogger(__name__)


class PowerStripException(DeviceException):
    pass


class PowerMode(enum.Enum):
    Eco = 'green'
    Normal = 'normal'


class PowerStripStatus:
    """Container for status reports from the power strip."""

    def __init__(self, data: Dict[str, Any]) -> None:
        """
        Supported device models: qmi.powerstrip.v1, zimi.powerstrip.v2

        Response of a Power Strip 2 (zimi.powerstrip.v2):
        {'power','on', 'temperature': 48.7, 'current': 0.05, 'mode': None,
         'power_consume_rate': 4.09, 'wifi_led': 'on', 'power_price': 49}
        """
        self.data = data

    @property
    def power(self) -> str:
        """Current power state."""
        return self.data["power"]

    @property
    def is_on(self) -> bool:
        """True if the device is turned on."""
        return self.power == "on"

    @property
    def temperature(self) -> float:
        """Current temperature."""
        return self.data["temperature"]

    @property
    def current(self) -> Optional[float]:
        """Current, if available. Meaning and voltage reference unknown."""
        if self.data["current"] is not None:
            return self.data["current"]
        return None

    @property
    def load_power(self) -> Optional[float]:
        """Current power load, if available."""
        if self.data["power_consume_rate"] is not None:
            return self.data["power_consume_rate"]
        return None

    @property
    def mode(self) -> Optional[PowerMode]:
        """Current operation mode, can be either green or normal."""
        if self.data["mode"] is not None:
            return PowerMode(self.data["mode"])
        return None

    @property
    def wifi_led(self) -> bool:
        """True if the wifi led is turned on."""
        return self.data["wifi_led"] == "on"

    @property
    def power_price(self) -> Optional[int]:
        """The stored power price, if available."""
        if self.data["power_price"] is not None:
            return self.data["power_price"]
        return None

    @property
    def leakage_current(self) -> Optional[int]:
        """The leakage current, if available."""
        if self.data["elec_leakage"] is not None:
            return self.data["elec_leakage"]
        return None

    @property
    def voltage(self) -> Optional[int]:
        """The voltage, if available."""
        if self.data["voltage"] is not None:
            return self.data["voltage"]
        return None

    @property
    def power_factor(self) -> Optional[float]:
        """The power factor, if available."""
        if self.data["power_factor"] is not None:
            return self.data["power_factor"]
        return None

    def __repr__(self) -> str:
        s = "<PowerStripStatus power=%s, " \
            "temperature=%s, " \
            "voltage=%s, " \
            "current=%s, " \
            "load_power=%s, " \
            "power_factor=%s " \
            "power_price=%s, " \
            "leakage_current=%s, " \
            "mode=%s, " \
            "wifi_led=%s>" % \
            (self.power,
             self.temperature,
             self.voltage,
             self.current,
             self.load_power,
             self.power_factor,
             self.power_price,
             self.leakage_current,
             self.mode,
             self.wifi_led)
        return s

    def __json__(self):
        return self.data


class PowerStrip(Device):
    """Main class representing the smart power strip."""

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Temperature: {result.temperature} °C\n"
            "Voltage: {result.voltage} V\n"
            "Current: {result.current} A\n"
            "Load power: {result.load_power} W\n"
            "Power factor: {result.power_factor}\n"
            "Power price: {result.power_price}\n"
            "Leakage current: {result.leakage_current} A\n"
            "Mode: {result.mode}\n"
            "WiFi LED: {result.wifi_led}\n")
    )
    def status(self) -> PowerStripStatus:
        """Retrieve properties."""
        properties = ['power', 'temperature', 'current', 'mode',
                      'power_consume_rate', 'wifi_led', 'power_price',
                      'voltage', 'power_factor', 'elec_leakage']
        values = self.send(
            "get_prop",
            properties
        )

        properties_count = len(properties)
        values_count = len(values)
        if properties_count != values_count:
            _LOGGER.debug(
                "Count (%s) of requested properties does not match the "
                "count (%s) of received values.",
                properties_count, values_count)

        return PowerStripStatus(
            defaultdict(lambda: None, zip(properties, values)))

    @command(
        default_output=format_output("Powering on"),
    )
    def on(self):
        """Power on."""
        return self.send("set_power", ["on"])

    @command(
        default_output=format_output("Powering off"),
    )
    def off(self):
        """Power off."""
        return self.send("set_power", ["off"])

    @command(
        click.argument("mode", type=EnumType(PowerMode, False)),
        default_output=format_output(
            "Setting mode to {mode}")
    )
    def set_power_mode(self, mode: PowerMode):
        """Set the power mode."""

        # green, normal
        return self.send("set_power_mode", [mode.value])

    @command(
        click.argument("led", type=bool),
        default_output=format_output(
            lambda led: "Turning on WiFi LED"
            if led else "Turning off WiFi LED"
        )
    )
    def set_wifi_led(self, led: bool):
        """Set the wifi led on/off."""
        if led:
            return self.send("set_wifi_led", ["on"])
        else:
            return self.send("set_wifi_led", ["off"])

    @command(
        click.argument("price", type=int),
        default_output=format_output("Setting power price to {price}")
    )
    def set_power_price(self, price: int):
        """Set the power price."""
        if price < 0 or price > 999:
            raise PowerStripException("Invalid power price: %s" % price)

        return self.send("set_power_price", [price])

    @command(
        click.argument("power", type=bool),
        default_output=format_output(
            lambda led: "Turning on real-time power measurement"
            if led else "Turning off real-time power measurement"
        )
    )
    def set_realtime_power(self, power: bool):
        """Set the realtime power on/off."""
        if power:
            return self.send("set_rt_power", [1])
        else:
            return self.send("set_rt_power", [0])

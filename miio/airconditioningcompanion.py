import enum
from typing import Optional

import click

from .click_common import command, format_output, EnumType
from .device import Device


class OperationMode(enum.Enum):
    Heat = 0
    Cool = 1
    Auto = 2
    Dehumidify = 3
    Ventilate = 4


class FanSpeed(enum.Enum):
    Low = 0
    Medium = 1
    High = 2
    Auto = 3


class SwingMode(enum.Enum):
    On = 0
    Off = 1


class Power(enum.Enum):
    On = 1
    Off = 0


class Led(enum.Enum):
    On = '0'
    Off = 'a'


STORAGE_SLOT_ID = 30
POWER_OFF = 'off'

# Command templates per model number (f.e. 0180111111)
# [po], [mo], [wi], [sw], [tt], [tt1], [tt4] and [tt7] are markers which will be replaced
DEVICE_COMMAND_TEMPLATES = {
    'fallback': {
        'deviceType': 'generic',
        'base': '[po][mo][wi][sw][tt][li]'
    },
    '0100010727': {
        'deviceType': 'gree_2',
        'base': '[po][mo][wi][sw][tt]1100190[tt1]205002102000[tt7]0190[tt1]207002000000[tt4]',
        'off': '01011101004000205002112000D04000207002000000A0'
    },
    '0100004795': {
        'deviceType': 'gree_8',
        'base': '[po][mo][wi][sw][tt][li]10009090000500'
    },
    '0180333331': {
        'deviceType': 'haier_1',
        'base': '[po][mo][wi][sw][tt]1'
    },
    '0180666661': {
        'deviceType': 'aux_1',
        'base': '[po][mo][wi][sw][tt]1'
    },
    '0180777771': {
        'deviceType': 'chigo_1',
        'base': '[po][mo][wi][sw][tt]1'
    }
}


class AirConditioningCompanionStatus:
    """Container for status reports of the Xiaomi AC Companion."""

    def __init__(self, data):
        # Device model: lumi.acpartner.v2
        #
        # Response of "get_model_and_state":
        # ['010500978022222102', '010201190280222221', '2']
        #
        # AC turned on by set_power=on:
        # ['010507950000257301', '011001160100002573', '807']
        #
        # AC turned off by set_power=off:
        # ['010507950000257301', '010001160100002573', '6']
        # ...
        # ['010507950000257301', '010001160100002573', '1']
        self.data = data

    @property
    def load_power(self) -> int:
        """Current power load of the air conditioner."""
        return int(self.data[2])

    @property
    def air_condition_model(self) -> str:
        """Model of the air conditioner."""
        return str(self.data[0])

    @property
    def power(self) -> str:
        """Current power state."""
        return 'on' if (int(self.data[1][2:3]) == Power.On.value) else 'off'

    @property
    def led(self) -> str:
        """Current LED state."""
        return 'on' if (int(self.data[1][8:9]) == Led.On.value) else 'off'

    @property
    def is_on(self) -> bool:
        """True if the device is turned on."""
        return self.power == 'on'

    @property
    def target_temperature(self) -> Optional[int]:
        """Target temperature."""
        try:
            return int(self.data[1][6:8], 16)
        except TypeError:
            return None

    @property
    def swing_mode(self) -> Optional[SwingMode]:
        """Current swing mode."""
        try:
            mode = int(self.data[1][5:6])
            return SwingMode(mode)
        except TypeError:
            return None

    @property
    def fan_speed(self) -> Optional[FanSpeed]:
        """Current fan speed."""
        try:
            speed = int(self.data[1][4:5])
            return FanSpeed(speed)
        except TypeError:
            return None

    @property
    def mode(self) -> Optional[OperationMode]:
        """Current operation mode."""
        try:
            mode = int(self.data[1][3:4])
            return OperationMode(mode)
        except TypeError:
            return None

    def __repr__(self) -> str:
        s = "<AirConditioningCompanionStatus " \
            "power=%s, " \
            "load_power=%s, " \
            "air_condition_model=%s, " \
            "led=%s, " \
            "target_temperature=%s, " \
            "swing_mode=%s, " \
            "fan_speed=%s, " \
            "mode=%s>" % \
            (self.power,
             self.load_power,
             self.air_condition_model,
             self.led,
             self.target_temperature,
             self.swing_mode,
             self.fan_speed,
             self.mode)
        return s

    def __json__(self):
        return self.data


class AirConditioningCompanion(Device):
    """Main class representing Xiaomi Air Conditioning Companion."""

    @command(
        default_output=format_output(
            "",
            "Power: {result.power}\n"
            "Load power: {result.load_power}\n"
            "Air Condition model: {result.air_condition_model}\n"
            "LED: {result.led}\n"
            "Target temperature: {result.target_temperature} °C\n"
            "Swing mode: {result.swing_mode}\n"
            "Fan speed: {result.fan_speed}\n"
            "Mode: {result.mode}\n"
        )
    )
    def status(self) -> AirConditioningCompanionStatus:
        """Return device status."""
        status = self.send("get_model_and_state", [])
        return AirConditioningCompanionStatus(status)

    @command(
        default_output=format_output("Powering the air condition on"),
    )
    def on(self):
        """Turn the air condition on by infrared."""
        return self.send("set_power", ["on"])

    @command(
        default_output=format_output("Powering the air condition off"),
    )
    def off(self):
        """Turn the air condition off by infrared."""
        return self.send("set_power", ["off"])

    @command(
        click.argument("slot", type=int),
        default_output=format_output(
            "Learning infrared command into storage slot {slot}")
    )
    def learn(self, slot: int=STORAGE_SLOT_ID):
        """Learn an infrared command."""
        return self.send("start_ir_learn", [slot])

    @command(
        default_output=format_output("Reading learned infrared commands")
    )
    def learn_result(self):
        """Read the learned command."""
        return self.send("get_ir_learn_result", [])

    @command(
        click.argument("slot", type=int),
        default_output=format_output(
            "Learning infrared command into storage slot {slot} stopped")
    )
    def learn_stop(self, slot: int=STORAGE_SLOT_ID):
        """Stop learning of a infrared command."""
        return self.send("end_ir_learn", [slot])

    @command(
        click.argument("command", type=str),
        default_output=format_output("Sending the supplied infrared command")
    )
    def send_ir_code(self, command: str):
        """Play a captured command.

        :param str command: Command to execute"""
        return self.send("send_ir_code", [str(command)])

    @command(
        click.argument("command", type=str),
        default_output=format_output("Sending a command to the air conditioner")
    )
    def send_command(self, command: str):
        """Send a command to the air conditioner.

        :param str command: Command to execute"""
        return self.send("send_cmd", [str(command)])

    @command(
        click.argument("model", type=str),
        click.argument("power", type=EnumType(Power, False)),
        click.argument("operation_mode", type=EnumType(OperationMode, False)),
        click.argument("target_temperature", type=int),
        click.argument("fan_speed", type=EnumType(FanSpeed, False)),
        click.argument("swing_mode", type=EnumType(SwingMode, False)),
        click.argument("led", type=EnumType(Led, False)),
        default_output=format_output(
            "Sending a configuration to the air conditioner")
    )
    def send_configuration(self, model: str, power: Power,
                           operation_mode: OperationMode,
                           target_temperature: int, fan_speed: FanSpeed,
                           swing_mode: SwingMode, led: Led):

        prefix = str(model[0:2] + model[8:16])
        suffix = model[-1:]

        # Static turn off command available?
        if (power is Power.Off) and (prefix in DEVICE_COMMAND_TEMPLATES) and \
                (POWER_OFF in DEVICE_COMMAND_TEMPLATES[prefix]):
            return self.send_command(
                prefix + DEVICE_COMMAND_TEMPLATES[prefix][POWER_OFF])

        if prefix in DEVICE_COMMAND_TEMPLATES:
            configuration = prefix + DEVICE_COMMAND_TEMPLATES[prefix]['base']
        else:
            configuration = \
                prefix + DEVICE_COMMAND_TEMPLATES['fallback']['base']

        configuration = configuration.replace('[po]', str(power.value))
        configuration = configuration.replace('[mo]', str(operation_mode.value))
        configuration = configuration.replace('[wi]', str(fan_speed.value))
        configuration = configuration.replace('[sw]', str(swing_mode.value))
        configuration = configuration.replace('[tt]', format(target_temperature, 'X'))
        configuration = configuration.replace('[li]', str(led.value))

        temperature = format((1 + target_temperature - 17) % 16, 'X')
        configuration = configuration.replace('[tt1]', temperature)

        temperature = format((4 + target_temperature - 17) % 16, 'X')
        configuration = configuration.replace('[tt4]', temperature)

        temperature = format((7 + target_temperature - 17) % 16, 'X')
        configuration = configuration.replace('[tt7]', temperature)

        configuration = configuration + suffix

        return self.send_command(configuration)

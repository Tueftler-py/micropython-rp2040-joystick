# Calibration (will be automatically written)
[]
# Created by Tueftler.py

import machine, os, asyncio

@micropython.native
def find_file(path="", first_line="# Calibration (will be automatically written)", file_type=".py"):
    """
    Recursively search for the first Python file that starts with a specific line.

    Args:
        path (str): Directory to start searching from.
        first_line (str): Line that must match the first line of the file.
        file_type (str): File ending of searched file, if you don't want this then only use a period for all files to be searched.'

    Returns:
        str: Path to the matching file, or None if not found.
    """
    for entry in os.listdir(path):
        newpath = path + "/" + entry
        if entry.endswith(file_type):
            with open(newpath, "r") as file:
                if file.readline().strip() == first_line:
                    return newpath
        if os.stat(newpath)[0] & 0x4000:
            return_val = find_file(newpath)
            if return_val:
                return return_val

class Joystick:
    """
    Class to handle analog joystick input with calibration and direction detection.
    """

    def __init__(self, a1, a2, button_pin, samples=3, deadzone=3, async_timeout=10):
        """
        Initialize the Joystick with ADC pins and button pin.

        Args:
            a1 (int): ADC ID for X axis.
            a2 (int): ADC ID for Y axis.
            button_pin (int): GPIO pin number for the button.
            samples (int): how much values for each measurement.
            deadzone (int): A zone around the center where nothing will not be recognized, useful for stickdrift problems. The value is in percent.
            async_timeout (int): time in ms for polling in async functions.
        """
        self.a1 = machine.ADC(a1)
        self.a2 = machine.ADC(a2)
        self.btn = machine.Pin(button_pin, machine.Pin.IN, machine.Pin.PULL_UP)
        self.samples = samples
        self.deadzone = deadzone
        self.at = async_timeout
        self.file = find_file()
        if not self.file:
            raise OSError("This file couldn't be found in the filesystem")

        with open(self.file, "r") as file:
            file.readline()
            raw_data = file.readline().strip()
        try:
            self.cal_data = eval(raw_data)
        except:
            raise OSError("Calibration data is corrupted. Replace second line with '[]' to reset.")

        if self.cal_data == []:
            self.calibrate()
        self.load_calib(self.cal_data)

    @micropython.native
    def button(self):
        """Return True if the joystick button is pressed."""
        return self.btn.value() == 0

    @micropython.native
    async def button_waiter(self):
        """
        Wait asynchronously until the joystick button is released.

        """
        while self.button():
            await asyncio.sleep_ms(self.at)

    def calibrate(self):
        """
        Run interactive joystick calibration. Stores new calibration data in the file.
        """
        print("Calibration started...")
        directions = ["MIDDLE", "LEFT", "RIGHT", "UP", "DOWN"]
        self.cal_data = []

        for direction in directions:
            input(f"Push the joystick to the {direction} and hold it there and then press ENTER")
            aval1 = self.a1.read_u16()
            aval2 = self.a2.read_u16()

            diff1 = abs(32767.5 - aval1)
            diff2 = abs(32767.5 - aval2)
            if diff1 > diff2:
                data, axis = aval1, 1
            else:
                data, axis = aval2, 2

            if direction == "MIDDLE":
                self.cal_data.append([direction, 1, aval1, 2, aval2])
            else:
                self.cal_data.append([direction, axis, data])

        try:
            with open(self.file, "r") as file:
                lines = file.readlines()
            lines[1] = f'{self.cal_data}\n'
            with open(self.file, "w") as file:
                for line in lines:
                    file.write(line)
        except Exception as error:
            print(f"Couldn't change file ({error}), please manually insert this on the second line: '{self.cal_data}'")

    def load_calib(self, data):
        """
        Load calibration data and compute mid ranges and axis values.

        Args:
            data (list): Calibration data from second line of this file.
        """

        p_over = round((100 + self.deadzone) / 100,2)
        p_under = round((100 - self.deadzone) / 100,2)

        self.middle1 = data[0][2]
        self.middle1_range = [round(self.middle1 * p_under), self.middle1, round(self.middle1 * p_over)]

        self.middle2 = data[0][4]
        self.middle2_range = [round(self.middle2 * p_under), self.middle2, round(self.middle2 * p_over)]

        self.middle = [self.middle1_range, self.middle2_range]
        
        self.leftval = data[1][2]
        self.leftaxis = data[1][1]

        self.rightval = data[2][2]
        self.rightaxis = data[2][1]

        self.upval = data[3][2]
        self.upaxis = data[3][1]

        self.downval = data[4][2]
        self.downaxis = data[4][1]

    @micropython.native
    def axis_reader(self, axis):
        """
        Read analog values from a specified axis and return average.

        Args:
            axis (int): 1 for X-axis, 2 for Y-axis.

        Returns:
            int: Averaged ADC value.
        """
        adc = self.a1 if axis == 1 else self.a2
        return round(sum(adc.read_u16() for _ in range(self.samples)) / self.samples)

    @micropython.native
    def converter(self, axis, maxval):
        """
        Convert analog input into percent offset from center.

        Args:
            axis (int): Axis number (1 or 2).
            maxval (int): Calibration value for the direction.

        Returns:
            int: Percentage from center (0–100).
        """
        val = self.axis_reader(axis)
        mid1 = self.middle[axis - 1][0]
        mid2 = self.middle[axis - 1][2]

        if val > mid2:
            percent = (val - mid2) / (maxval - mid2) * 100
        elif val < mid1:
            percent = (mid1 - val) / (mid1 - maxval) * 100
        else:
            return 0

        return round(min(100, max(0, percent)))

    @micropython.native
    def up(self, percent=False):
        """Return True/percent if joystick is pushed up."""
        p = self.converter(self.upaxis, self.upval)
        return p if percent else p > 50

    @micropython.native
    def down(self, percent=False):
        """Return True/percent if joystick is pushed down."""
        p = self.converter(self.downaxis, self.downval)
        return p if percent else p > 50

    @micropython.native
    def right(self, percent=False):
        """Return True/percent if joystick is pushed right."""
        p = self.converter(self.rightaxis, self.rightval)
        return p if percent else p > 50

    @micropython.native
    def left(self, percent=False):
        """Return True/percent if joystick is pushed left."""
        p = self.converter(self.leftaxis, self.leftval)
        return p if percent else p > 50

    @micropython.native
    def max_direction(self, as_bool):
        """
        Return the direction with the highest activation.

        Args:
            as_bool (bool): If True, returns only if above threshold.

        Returns:
            str or list: Direction name or [name, percent].
        """
        directions = []
        for direction in ["up", "down", "right", "left"]:
            method = getattr(self, direction)
            directions.append([direction, method(True)])
        directions.sort(key=lambda x: x[1], reverse=True)
        if directions[0][1] == 0:
            return None
        if as_bool:
            return directions[0][0] if directions[0][1] > 50 else None
        else:
            return directions[0]

    @micropython.native
    def get_all_states(self):
        """
        Return a list of all directions and button states with percent values.

        Returns:
            list: List of [direction, value] pairs.
        """
        directions = [["button", self.button()]]
        for direction in ["up", "down", "right", "left"]:
            method = getattr(self, direction)
            directions.append([direction, method(True)])
        return directions

    @micropython.native
    def get(self, as_bool=True):
        """
        Return the current active input.

        Args:
            as_bool (bool): Whether to return bool or percent.

        Returns:
            str or list: Direction name or [name, percent].
        """
        if self.button():
            return "button"
        else:
            return self.max_direction(as_bool)

    @micropython.native
    async def get_waiter(self, as_bool=True):
        """
        Wait asynchronously until joystick input is detected.

        Args:
            as_bool (bool): Whether to return bool or percent.

        Returns:
            str or list: Detected direction or "button".
        """
        val = None
        while not val:
            if self.button():
                val = "button"
            else:
                val = self.max_direction(as_bool)
            await asyncio.sleep_ms(self.at)
        return val

if __name__ == "__main__":
    print("Joystick lib started...")
    a1 = int(input("Input your first ADC ID: "))
    a2 = int(input("Input your second ADC ID: "))
    btn = int(input("Input your button Pin: "))
    joystick = Joystick(a1, a2, btn)
    mode = int(input("Enter 1 to test and 0 to calibrate again: "))
    if mode == 0:
        joystick.calibrate()
    elif mode == 1:
        valbef = ""
        while True:
            val = joystick.get()
            if val != valbef:
                print(val)
                valbef = val
    else:
        raise OSError(f"Invalid mode choice: {mode}")
    print("If you calibrated the Joystick, please reopen this file")

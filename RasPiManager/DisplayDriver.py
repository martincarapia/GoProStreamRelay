import smbus2
from time import sleep

# Define constants
I2CBUS = 1          # Bus 1 for modern Raspberry Pi models
ADDRESS = 0x3f      # I2C address for your LCD

# LCD Commands
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# LCD Display Flags
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# Flags for display entry mode
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01

# LCD Backlight control
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

# Enable, Read/Write, and Register Select bits
En = 0b00000100
Rw = 0b00000010
Rs = 0b00000001

# I2C Device class to handle low-level I2C communication
class i2c_device:
    def __init__(self, addr=ADDRESS, port=I2CBUS):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    def write_cmd(self, cmd):
        self.bus.write_byte(self.addr, cmd)
        sleep(0.0001)

class lcd:
    def __init__(self):
        self.lcd_device = i2c_device()

        # LCD initialization sequence
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x03)
        self.lcd_write(0x02)  # Set to 4-bit mode

        self.lcd_write(LCD_FUNCTIONSET | 0x08)  # 2-line display
        self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
        sleep(0.2)

    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        sleep(0.0005)
        self.lcd_device.write_cmd((data & ~En) | LCD_BACKLIGHT)
        sleep(0.0001)

    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self.lcd_strobe(data)

    def lcd_write(self, cmd, mode=0):
        # Send high nibble
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        # Send low nibble
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    def lcd_display_string(self, string, line=1, pos=0):
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        self.lcd_write(0x80 + pos_new)

        for char in string:
            self.lcd_write(ord(char), Rs)

    def lcd_clear(self):
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_RETURNHOME)

    def backlight(self, state):  # Turn backlight on/off
        if state == 1:
            self.lcd_device.write_cmd(LCD_BACKLIGHT)
        else:
            self.lcd_device.write_cmd(LCD_NOBACKLIGHT)

    def lcd_load_custom_chars(self, fontdata):
        self.lcd_write(0x40)
        for char in fontdata:
            for line in char:
                self.lcd_write(line, Rs)

    def lcd_scroll_text(self, text, delay=0.1):
        str_pad = " " * 16
        my_long_string = str_pad + text + str_pad
        for i in range(len(my_long_string) - 15):
            lcd_text = my_long_string[i:(i + 16)]
            self.lcd_display_string(lcd_text, 1)
            sleep(delay)
            self.lcd_display_string(str_pad, 1)

if __name__ == "__main__":
    mylcd = lcd()

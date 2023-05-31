print('start program.py')

from machine import Pin, I2C, SoftI2C, ADC, PWM, UART, lightsleep, deepsleep, sleep
import network, os, webrepl, time
import ssd1306
import config

right_but = Pin(6, Pin.IN, Pin.PULL_UP)
left_but  = Pin(7, Pin.IN, Pin.PULL_UP)

blue_led = Pin(8, Pin.OUT, Pin.PULL_UP)
p9 = Pin(9, Pin.OUT, Pin.PULL_UP, hold=True)
p10 = Pin(10, Pin.OUT, Pin.PULL_UP)

def peripheral_power(on):
    p10.value(on)

def wifi_off():
    wlan_sta = network.WLAN(network.STA_IF)
    wlan_sta.active(False)

def beep(freq):
    pwm = PWM(blue_led)
    pwm.duty(512)
    pwm.freq(freq)
    for _ in range(10000): pass
    pwm.deinit()
    for _ in range(100000): pass

def screen_init():
    global screen
    screen = ssd1306.SSD1306_I2C(128, 32, i2c)

def screen_write(line, text):
    screen.text(text, 0, line*8, 1)

# Initialize I2C bus

i2c =I2C(0)  # uses pins scl=18 and sda=19


peripheral_power(True)

wifi_off()

screen_init()



import font8x12 as font

def write(text, w, h):
    screen.fill(0)
    for i in range(len(text)):
        bitmap = font.bitmap[ord(text[i])]
        posx = (i+1) * font.width
        if posx * w > 128: break
        for yy in range(font.height):
            y = yy * h
            if y >= 32: break
            b = bitmap[yy]
            for xx in range(font.width):
                x = (posx - xx - 1) * w
                col = b & 1
                screen.rect(x, y, w, h, col)
                b >>= 1
    screen.show()


freq = 4000
adc2 = ADC(Pin(2, Pin.IN), atten=ADC.ATTN_11DB)
adc3 = ADC(Pin(3, Pin.IN), atten=ADC.ATTN_11DB)
adc4 = ADC(Pin(4, Pin.IN, Pin.PULL_UP), atten=ADC.ATTN_11DB)
adc5 = ADC(Pin(5, Pin.IN, Pin.PULL_DOWN), atten=ADC.ATTN_11DB)

write(config.device_id, 2, 3)

for _ in range(1000000): pass

while True:
    for _ in range(100000): pass
    screen.fill(0)
    val2 = adc2.read_u16()  # read a raw analog value in the range 0-65535
    val3 = adc3.read_u16()  # read a raw analog value in the range 0-65535
    val4 = adc4.read_u16()  # read a raw analog value in the range 0-65535
    val5 = adc5.read_u16()  # read a raw analog value in the range 0-65535
    screen_write(0, str(val2))
    screen_write(1, str(val3))
    screen_write(2, str(val4))
    screen_write(3, str(val5))
    screen.show()
    #write(str(val2), 2, 3)
    #screen_write(str(freq) + ' ' + str(val))
    beep(freq)


exit(0)





def blink(n):
    global blue_led
    k = 300000
    while n > 0:
        blue_led.off()
        blue_led = Pin(8, Pin.OUT, Pin.PULL_UP, hold=True)
        for _ in range(k): pass
        blue_led.on()
        blue_led = Pin(8, Pin.OUT, Pin.PULL_UP, hold=True)
        for _ in range(k): pass
        n -= 1

def buzz(n):
    global blue_led
    while True:
        blue_led.off()
        blue_led = Pin(8, Pin.OUT, Pin.PULL_UP, hold=True)
        for _ in range(n): pass
        blue_led.on()
        blue_led = Pin(8, Pin.OUT, Pin.PULL_UP, hold=True)
        for _ in range(n): pass

def cycle():
    global blue_led
    global p9
    global p10
    while True:
        p10.on()
        p10 = Pin(10, Pin.OUT, Pin.PULL_UP, hold=True)
        blink(20)
        #print(I2C.scan())
        blue_led.on()
        p9.on()
        p10.off()
        blue_led = Pin(8, Pin.OUT, Pin.PULL_UP, hold=True)
        p9 = Pin(9, Pin.OUT, Pin.PULL_UP, hold=True)
        p10 = Pin(10, Pin.OUT, Pin.PULL_DOWN, hold=True)
        #for _ in range(1000000): pass
        deepsleep(3000)


#while True: blink(100)

p7 = Pin(7, Pin.IN, Pin.PULL_UP)



#buzz(300)

#if p7.value():
#    cycle()
#else:
#    while True:
#        blink(20)

print('end program.py')

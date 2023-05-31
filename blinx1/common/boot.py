import time, os, sys, json, network, binascii                                   
from machine import Pin, I2C, SoftI2C, ADC, PWM, UART
wlan_sta = network.WLAN(network.STA_IF)
wlan_sta.active(True)                                                           
wlan_ap = network.WLAN(network.AP_IF)                                           
wlan_ap.active(False)

import blinxTtgo
blinxTtgo.launch(site = False, blue=True)

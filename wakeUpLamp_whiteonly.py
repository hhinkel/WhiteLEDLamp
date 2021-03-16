''' Copyright 2021 Heidi Hinkel 

Permission is hereby granted, free of charge, to any person obtaining a copy of this software
and associated documentation files (the "Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be included in all copies or
substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED
TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE. '''

from machine import Pin, PWM
import machine
import network
import utime
import ntptime
import uasyncio

# User constants
SSID = 'SSID'
PW = 'password'
TIME_ZONE = -4  # hours from GMT. This is EDT (-5 is EST time)
SEC_IN_HOUR = 3600 #Seconds in an hour
LIT_LENGTH = 2  # Hours at brightest setting
WAKEUP_TUPLE = (4, 45)  # time lights come on in 24hr format, hour and minute
PIN = 27  # Pin that connects the lights to the microcontroller
FULL_BRIGHTNESS = 1023  # 100 % duty cycle for the LEDs


async def setup(led):
    """ Test the LEDs, set the clock for the first time and get the wake up time.
    Arguments:
        led - pin object
    Local Variables:
        None
    Returns:
        Nothing """
    await fade(led)
    updateRTCFromNTP(led)


def updateRTCFromNTP(led):
    """ Update the microcontrollers real time clock (RTC) from
        network time protocol (NTP) servers. The RTC of the ESP8266 is notoriously inaccurate.
        https://docs.micropython.org/en/latest/esp8266/general.html#real-time-clock
    Arguments:
        led - pin object (for flashing if can not connect to NTP server)
    Local Variables:
        wifi - wifi object
        localTime - as a time tuple (see setup)
    Returns:
        Nothing """
    wifi = connectToWifi(led)
    try:
        ntptime.settime()
    except OSError:
        flash(led, 4, FULL_BRIGHTNESS)
        machine.reset()
    localTime = getLocalTime()
    disconnectFromWifi(wifi)


def flash(led, num, dutyCycle):
    """ Flash the led strip the designated number of times
    Arguments:
        led - Pin object
        num - number of times to flash the led strip
        dutyCycle - brightness of led strip
    Local Variables:
        i - counter
    Returns:
        Nothing """
    pwmLED = PWM(led, freq=5000)
    for i in range(0, num - 1):
        utime.sleep(0.5)
        pwmLED.duty(dutyCycle)
        utime.sleep(0.5)
        pwmLED.duty(0)
    pwmLED.deinit()


def connectToWifi(led):
    """ Setup the wifi object and connect to the network defined above
    Arguments:
        led - pin object
    Local Variables:
        wifi - network object
    Returns:
        wifi - network object """
    wifi = network.WLAN(network.STA_IF)
    wifi.active(True)
    wifi.connect(SSID, PW)
    while not wifi.isconnected():
        flash(led, 2, 100)
        pass
    return wifi


def disconnectFromWifi(wifi):
    """ Disconnect from wifi
    Arguments:
        wifi - network object
    Local Variables:
        None
    Returns:
        Nothing """
    wifi.disconnect()
    wifi.active(False)


def getLocalTime():
    """ Get local Time
    Arguments:
        None
    Local Variables:
        None
    Returns:
        local time tuple """
    return utime.localtime(utime.time() + TIME_ZONE * SEC_IN_HOUR)


async def clock(led):
    """ processing loop. Loop continuosly. Keep track of the time, when the wakeup
        time comes around set off the lights. Every 6 hours query the time NTP server
        and update the microcontrollers clock.
    Arguments:
        led - pin object
    Local Variables:
        hourMin - the current hour and minute
    Returns:
        Nothing """
    while True:
        hourMin = getLocalTime()[3:5]
        if hourMin == WAKEUP_TUPLE:
            await fade(led, LIT_LENGTH * SEC_IN_HOUR)
        if hourMin == (0, 0) or hourMin == (6, 0) or hourMin == (12, 0) or hourMin == (18, 0):
            updateRTCFromNTP(led)
        utime.sleep(30)


async def fade(led, litTime=1, t=0.005):
    """ Setup the pulse width modulated (PWM) object and
        fade the single color led strip once. Signal frequency (freq) can be
        from 0 to 78125. dutyCycle controls the brightness and varies between
        0 and FULL_BRIGHTNESS. FULL_BRIGHTNESS is a 100% duty cycle
    Arguments:
        led - pin object
        litTime - how long the LED should remain at full brightness, 100% duty cycle (default = 1 second)
        t - time in seconds between changes in dutyCycle (default = 0.005 seconds)
    Local Variables:
        pwmLED - PWM object
        dutyCycle - looping variable indicating what the current dudty cycle is
    Returns:
        Nothing """
    pwmLED = PWM(led, freq=5000)
    for dutyCycle in range(0, FULL_BRIGHTNESS):
        pwmLED.duty(dutyCycle)
        utime.sleep(t)
    utime.sleep(litTime)
    for dutyCycle in range(FULL_BRIGHTNESS, 0, -1):
        pwmLED.duty(dutyCycle)
        utime.sleep(t)
    pwmLED.deinit()

def main():
    """ Setup Pin object, run setup function and start the processing loop (clock)
    Arguments:
        None
    Local Variables:
        led - Pin object
    Returns:
        Nothing """
    led = Pin(PIN, Pin.OUT)
    uasyncio.run(setup(led))
    uasyncio.run(clock(led))


if __name__ == '__main__':
    main()

# Microcifra 26
# Roni Bandini @ronibandini
# MIT License, August 2026
# Buenos Aires, Argentina

import sys
import time
import select
import random
from machine import Pin, PWM, SPI, ADC
import max7219

# Gpio
servoPin = 0
switchPin = 1
clkPin = 2
dinPin = 3
csPin = 4
buzzerPin = 10
potPin = 28

# matrix
spi = SPI(0, baudrate=10000000, polarity=0, phase=0, sck=Pin(clkPin), mosi=Pin(dinPin))
cs = Pin(csPin, Pin.OUT)
display = max7219.Matrix8x8(spi, cs, 1)

buzzer = PWM(Pin(buzzerPin))
buzzer.duty_u16(0)

servo = PWM(Pin(servoPin))
servo.freq(50)

toggleSwitch = Pin(switchPin, Pin.IN, Pin.PULL_UP)
pot = ADC(Pin(potPin))

minDuty = 1638
maxDuty = 8192

currentServoDuty = minDuty
lastTargetAngle = 0
servo.duty_u16(currentServoDuty)

def playBeep(freq=1000, duration=0.02):
    buzzer.freq(freq)
    buzzer.duty_u16(32768)
    time.sleep(duration)
    buzzer.duty_u16(0)

def updateDisplay(showImageFunc):
    display.brightness(15)
    showImageFunc()
    display.show()

def checkSerialCommand():
    if select.select([sys.stdin], [], [], 0)[0]:
        line = sys.stdin.readline().strip()
        return line
    return None

def readPotSmoothed():
    total = 0
    for _ in range(8):
        total += pot.read_u16()
        time.sleep_us(100)
    return total // 8

def moveServoTo(targetAngle):
    global currentServoDuty
    targetDuty = int(minDuty + (targetAngle / 180.0) * (maxDuty - minDuty))
    
    # to avoid flickering :(
    if abs(targetDuty - currentServoDuty) > 10:
        stepValue = 15 if targetDuty > currentServoDuty else -15
        
        for dutyValue in range(currentServoDuty, targetDuty, stepValue):
            servo.duty_u16(dutyValue)
            time.sleep(0.015)
            
        servo.duty_u16(targetDuty)
        currentServoDuty = targetDuty

def bootSplash():
    text = "Microcifra 26 - @ronibandini"
    textWidth = len(text) * 8
    for xPos in range(8, -textWidth, -1):
        if toggleSwitch.value() == 0:
            break
        display.brightness(15)
        display.fill(0)
        display.text(text, xPos, 0, 1)
        display.show()
        playBeep(1200, 0.005)
        time.sleep(0.06)
    display.fill(0)
    display.show()

def runShiftAnimationStep(currentHeights, targetHeights):
    growing = False
    for colIndex in range(8):
        if currentHeights[colIndex] < targetHeights[colIndex]:
            currentHeights[colIndex] += 1
            growing = True

    def renderCols():
        display.fill(0)
        for colIndex in range(8):
            heightValue = currentHeights[colIndex]
            for rowIndex in range(8 - heightValue, 8):
                display.pixel(colIndex, rowIndex, 1)

    updateDisplay(renderCols)
    time.sleep(0.04)

    if not growing:
        time.sleep(0.08)
        for colIndex in range(7):
            currentHeights[colIndex] = currentHeights[colIndex + 1]
            targetHeights[colIndex] = targetHeights[colIndex + 1]

        currentHeights[7] = 0
        targetHeights[7] = random.randint(1, 8)

def stepScrollText(text, xPos):
    textWidth = len(text) * 8
    def renderText():
        display.fill(0)
        display.text(text, xPos, 0, 1)
    updateDisplay(renderText)
    playBeep(1200, 0.005)
    xPos -= 1
    if xPos < -textWidth:
        xPos = 8
    return xPos

def main():
    global lastTargetAngle
    bootSplash()
    # for the cam turret
    surveillanceAngles = [0, 90, 180, 90]
    angleIndex = 0

    currentHeights = [0] * 8
    targetHeights = [random.randint(1, 8) for _ in range(8)]

    activeMessage = None
    textX = 8
    wasSurveillanceActive = False

    while True:
        switchState = toggleSwitch.value()

        if switchState == 0:
            wasSurveillanceActive = True
            targetAngle = surveillanceAngles[angleIndex]
            
            moveServoTo(targetAngle)
            lastTargetAngle = targetAngle
            time.sleep(1.0)

            def renderSurveillance():
                display.fill(0)
                display.text("S", 1, 0, 1)

            updateDisplay(renderSurveillance)
            playBeep(1500, 0.05)

            print("CAP:{}".format(targetAngle))

            angleIndex = (angleIndex + 1) % len(surveillanceAngles)
            time.sleep(1.5)

        else:
            if wasSurveillanceActive:
                print("SURV:OFF")
                wasSurveillanceActive = False

            potVal = readPotSmoothed()
            calculatedAngle = int((potVal / 65535.0) * 180.0)

            # Ignore less than 2 degrees variations 
            if abs(calculatedAngle - lastTargetAngle) > 2:
                moveServoTo(calculatedAngle)
                lastTargetAngle = calculatedAngle

            cmd = checkSerialCommand()
            if cmd:
                if cmd == "CANCEL":
                    activeMessage = None
                    display.fill(0)
                    display.show()
                elif cmd.startswith("MSG:"):
                    activeMessage = cmd[4:]
                    textX = 8

            if activeMessage:
                textX = stepScrollText(activeMessage, textX)
                time.sleep(0.06)
            else:
                runShiftAnimationStep(currentHeights, targetHeights)

if __name__ == "__main__":
    main()
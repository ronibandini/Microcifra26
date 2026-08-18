# Microcifra 26
# Roni Bandini, MIt Licensse, August 2026 @ronibandini
# Bridge betweel Linux and the RP2040 main.py
# Also, console to send messages to the Matrix and audio recording 

import os
import sys
import time
import serial
import threading
import subprocess
from PIL import Image, ImageOps, ImageDraw, ImageFont

outputDir = "pics"
wavDir = "wav"
serialPort = "/dev/ttyACM0"
baudRate = 115200

fehProcess = None
audioProcess = None
currentAudioFile = None

bannerArt = r"""
 __  __ ___ ___ ___  ___   ___ ___ ___ ___    _     ___  __ 
|  \/  |_ _/ __| _ \/ _ \ / __|_ _| __| _ \  /_\   |_  )/ / 
| |\/| || | (__|   / (_) | (__ | || _||   / / _ \   / // _ \
|_|  |_|___\___|_|_\\___/ \___|___|_| |_|_\/_/ \_\ /___\___/

                       Roni Bandini 8/2026
"""

def ensureOutputDir():
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

def ensureWavDir():
    if not os.path.exists(wavDir):
        os.makedirs(wavDir)

def processGreenRetro(inputPath, outputPath):
    try:
        img = Image.open(inputPath)
        w, h = img.size
        imgSmall = img.resize((320, 180), Image.NEAREST)
        imgPixelated = imgSmall.resize((w, h), Image.NEAREST)
        
        gray = ImageOps.grayscale(imgPixelated)
        greenImg = ImageOps.colorize(gray, black="#052205", white="#00FF41")
        
        draw = ImageDraw.Draw(greenImg)
        try:
            font = ImageFont.truetype("DejaVuSansMono.ttf", 26)
        except Exception:
            font = ImageFont.load_default()
            
        draw.rectangle([(15, h - 45), (250, h - 10)], fill="#052205")
        draw.text((20, h - 42), "Microcifra 26", fill="#00FF41", font=font)
        
        greenImg.save(outputPath)
    except Exception as e:
        print("[ERROR] Color proc:", e)

def closeFeh():
    global fehProcess
    if fehProcess and fehProcess.poll() is None:
        fehProcess.terminate()
        fehProcess = None

def showImageFeh(filePath):
    global fehProcess
    closeFeh()
    fehProcess = subprocess.Popen(["feh", "-F", "-Z", "--title", "Cyberdeck Cam", filePath])

def takePicture(angle="MANUAL"):
    ensureOutputDir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    rawPath = os.path.join(outputDir, "raw_{}deg_{}.jpg".format(angle, timestamp))
    procPath = os.path.join(outputDir, "{}deg_{}.jpg".format(angle, timestamp))
    
    # stabilize cam sensor
    cmd = "fswebcam -r 1280x720 -S 10 --no-banner {} > /dev/null 2>&1".format(rawPath)
    os.system(cmd)
    
    if os.path.exists(rawPath):
        processGreenRetro(rawPath, procPath)
        print("\n--- CAPTURED RETRO IMAGE ({}) ---".format(angle))
        showImageFeh(procPath)
        print("------------------------------------\n")


def startAudioRecording():
    global audioProcess, currentAudioFile
    if audioProcess and audioProcess.poll() is None:
        print("[AUDIO] Recording session already active.")
        return
    
    ensureWavDir()
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    currentAudioFile = os.path.join(wavDir, "audio_{}.wav".format(timestamp))
    
    cmd = [
        "arecord",
        "-D", "plughw:1,0",
        "-f", "S16_LE",
        "-r", "16000",
        "-c", "1",
        "-t", "wav",
        currentAudioFile
    ]
    
    try:
        audioProcess = subprocess.Popen(cmd, stderr=subprocess.PIPE)
        time.sleep(0.2)
        
        if audioProcess.poll() is not None:
            _, err = audioProcess.communicate()
            print("[AUDIO ERROR!] arecord failed instantly:\n", err.decode('utf-8', errors='ignore'))
            audioProcess = None
        else:
            print("\n[AUDIO] Webcam recording started: {}".format(currentAudioFile))
    except Exception as e:
        print("[AUDIO ERROR !!] Failed to execute arecord:", e)

def stopAudioRecording():
    global audioProcess, currentAudioFile
    if audioProcess and audioProcess.poll() is None:
        audioProcess.terminate()
        audioProcess.wait()
        audioProcess = None
        print("[AUDIO] Recording stopped and saved to: {}\n".format(currentAudioFile))
    else:
        print("[AUDIO] No active recording session found.")

def listenToRP2040(ser):
    while True:
        try:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if line.startswith("CAP:"):
                    angle = line.split(":")[1]
                    takePicture(angle)
                elif line == "SURV:OFF":
                    closeFeh()
        except Exception as e:
            break

def main():
    os.system("clear")
    print(bannerArt)
    try:
        ser = serial.Serial(serialPort, baudRate, timeout=1)
        time.sleep(2)
    except Exception as e:
        print("Could not open serial port {}: {}".format(serialPort, e))
        sys.exit(1)

    t = threading.Thread(target=listenToRP2040, args=(ser,), daemon=True)
    t.start()

    print("Available Commands:")
    print("  <text>      : Scroll text message on matrix")
    print("  cancel / c  : Stop active scroll message")
    print("  photo / snap: Capture instant photo")
    print("  rec start   : Begin audio recording")
    print("  rec stop    : Stop audio recording\n")

    try:
        while True:
            userInput = input("> ").strip()
            if not userInput:
                continue
            
            cmdLower = userInput.lower()
            
            if cmdLower in ["cancel", "c"]:
                ser.write(b"CANCEL\n")
            elif cmdLower in ["photo", "snap"]:
                takePicture("MANUAL")
            elif cmdLower == "rec start":
                startAudioRecording()
            elif cmdLower == "rec stop":
                stopAudioRecording()
            else:
                cmd = "MSG:{}\n".format(userInput)
                ser.write(cmd.encode('utf-8'))
    except KeyboardInterrupt:
        stopAudioRecording()
        closeFeh()
        ser.close()

if __name__ == "__main__":
    main()
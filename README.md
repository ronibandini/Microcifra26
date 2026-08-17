# 📟 Microcifra 26 Cyberdeck

<img width="1532" height="1026" alt="Microcifra26Aviso" src="https://github.com/user-attachments/assets/4f149b2b-18a0-457f-b6be-5f8ef597fea0" />

# 🖥️ Microcifra 26 Cyberdeck

**Microcifra 26** is a custom cyberdeck built around a **LattePanda IOTA**, combining an Intel N150 Linux host with an RP2040 coprocessor for direct hardware control.

The system includes a 7" EDP display, movable USB camera, physical controls, audio, an 8×8 LED matrix, battery power, and GPIO-connected peripherals.

The name **Microcifra** is a tribute to the Microcifra calculators manufactured by Fate Electrónica in Argentina during the 1970s.

---

## ⚙️ Hardware

| Component                   | Purpose                   |
| --------------------------- | ------------------------- |
| **LattePanda IOTA**         | Main computer             |
| **Intel N150 / 16 GB RAM**  | Linux host                |
| **RP2040**                  | GPIO coprocessor          |
| **7" EDP display**          | Main display              |
| **USB mini keyboard**       | Input                     |
| **USB camera + microphone** | Image and audio capture   |
| **SG90 servo**              | Camera turret             |
| **Potentiometer**           | Manual camera positioning |
| **Toggle switch**           | Surveillance mode         |
| **8×8 MAX7219 LED matrix**  | Messages and status       |
| **3 W speaker + amplifier** | Audio output              |
| **Buzzer**                  | Alerts                    |
| **UPS + 3× 18650 cells**    | Battery power             |
| **KY-023 joystick**         | GPIO game controller      |

---

## 🧠 Architecture

Microcifra 26 uses two processing layers. Ubuntu runs on the Intel N150, while the RP2040 handles the physical peripherals through GPIO.

```text
┌──────────────────────────────────────┐
│          Intel N150 / Ubuntu         │
│                                      │
│   host.py                            │
│   OpenClaw                           │
│   llama.cpp                          │
│   n8n                                │
│   MAME                               │
└──────────────────┬───────────────────┘
                   │
                USB / mpremote
                   │
┌──────────────────▼───────────────────┐
│                RP2040                │
│                                      │
│   MicroPython / main.py              │
│                                      │
│   ├── Servo                          │
│   ├── Potentiometer                  │
│   ├── Toggle switch                  │
│   ├── Buzzer                         │
│   ├── MAX7219 LED matrix             │
│   └── Joystick                       │
└──────────────────────────────────────┘
```

This separation keeps high-level software on Linux while delegating deterministic hardware interaction to the RP2040.

---

## 👁️ Camera System

The USB camera is mounted on an **SG90 servo**, creating a simple motorized turret.

A physical toggle switch enables surveillance mode. In this mode, the camera automatically pans across three positions:

```text
0°   → Capture
90°  → Capture
180° → Capture
```

Captured images are converted to green tones to resemble an old CCTV terminal. The turret can also be positioned manually using the side potentiometer.

Images and audio recordings are stored in:

```text
/pics
/wav
```

---

## 🟩 8×8 LED Matrix

A rear **MAX7219 8×8 LED matrix** can display scrolling messages such as announcements, identifiers or public keys.

When no message is active, the matrix displays a bar animation. A buzzer can provide an audible signal together with the messages.

---

## 🔌 GPIO Mapping

| Device              | RP2040 GPIO |
| ------------------- | ----------: |
| Potentiometer       |        GP11 |
| Buzzer              |        GP10 |
| Surveillance toggle |         GP1 |
| SG90 servo          |         GP0 |
| MAX7219 DIN         |         GP3 |
| MAX7219 CS          |         GP4 |
| MAX7219 CLK         |         GP2 |
| Joystick X          |        GP26 |
| Joystick Y          |        GP27 |
| Joystick button     |         GP7 |

---

## 🐍 RP2040 Firmware

The RP2040 runs `main.py` under **MicroPython**.

Copy the firmware:

```bash
mpremote cp main.py :main.py
```

Reset the RP2040:

```bash
mpremote reset
```

Because the program is stored as `main.py`, it runs automatically after boot.

---

## 🐧 Linux Host

The Linux side runs `host.py`, which communicates with `main.py` and provides higher-level access to the cyberdeck hardware.

It can be used to:

* Send messages to the rear LED matrix
* Trigger and retrieve camera captures
* Record audio
* Communicate with RP2040 peripherals

External applications can also send commands directly through `mpremote`.

Example:

```bash
mpremote exec "import sys; sys.stdout.write('MSG:Hello world\n')"
```

---

## 📷 Camera Dependencies

Install `fswebcam`:

```bash
sudo apt update
sudo apt install fswebcam
```

---

## 🔊 Ubuntu Audio Fix

During development, the internal audio device intermittently failed with:

```text
snd_hda_intel: cannot find the slot for index 0
error: -16 (EBUSY)
```

The issue was caused by old configuration files forcing `snd_hda_intel` into ALSA slot `0`. If the USB webcam audio interface registered first as card 0, the Intel audio driver could not claim the same slot.

The obsolete configuration files were removed:

```text
/etc/modprobe.d/intelaudio.conf
/etc/modprobe.d/lattepanda-audio.conf
```

Then:

```bash
sudo update-initramfs -u
sudo reboot
```

The kernel can then handle device detection automatically.

---

## 🤖 AI and Local LLMs

The Linux layer also runs **OpenClaw** and local LLMs through **llama.cpp**. Remote n8n calls provide text-mode access to services such as email, calendars and personal files.

This architecture makes it possible to expose physical cyberdeck functions to an AI agent—for example, allowing an agent to interact with the camera or other hardware rather than limiting it to conventional software interfaces.

---
## Demo

https://youtu.be/6wZkjQE8VtE
---

## 👤 Author

**Roni Bandini**

Maker · AI Developer · Electronic Artist · Writer



🖱️ AI Control System

📄 Abstract

This project is a contactless hardware controller that enables users to control their computer system using Hand Gestures, Eye Movements, Head Movements and Voice Commands. By leveraging Computer Vision and AI (MediaPipe), it eliminates the need for physical peripherals, making human-computer interaction more intuitive and accessible.

✨ Key Features

Virtual Mouse: Move the cursor using hand movements with high precision.

Gesture Clicks:

Left Click: Pinch Index + Middle Finger.

Dwell Mode: Hover over a spot for 1 second to auto-click.

System Controls: Adjust Volume and Brightness using hand distance/gestures.

Voice Assistant: Execute commands hands-free (launch apps, type text, etc.).

Eye Tracking: Experimental control using eye gaze (eye.py).

GUI Dashboard: A web-based interface (built with Eel) to toggle features and settings.

🛠️ Tech Stack

Core: Python 3

Computer Vision: OpenCV, MediaPipe (Hands & Face Mesh)

Automation: PyAutoGUI, Pynput

Audio/Voice: PyAudio, SpeechRecognition, Pyttsx3

GUI: Eel (HTML/CSS/JS frontend for Python)

Utilities: Screen-brightness-control, Pycaw (Volume)

📂 Project Structure

├── src/
│   ├── web/                 # HTML/CSS Interface for the settings
│   ├── main.py              # Entry point of the application
│   ├── Gesture_Controller.py # Main logic for hand tracking & mouse control
│   ├── eye.py               # Eye tracking module
│   ├── Proton.py            # Voice assistant module
│   └── ...
├── requirements.txt         # Dependencies
└── README.md


🚀 Installation & Setup

Download the ZIP file.

Create a Virtual Environment (Recommended)

python -m venv .venv
# Windows:
.venv\Scripts\activate
# Mac/Linux:
source .venv/bin/activate


Install Dependencies

pip install -r requirements.txt


🎮 How to Run

Navigate to the src directory and run the main file:

cd src
python main.py


🕹️ Controls & Hotkeys

Action

Gesture / Key

Move Cursor

Move Hand / Index Finger

Left Click

Pinch Index + Middle Finger

Dwell Click

Hover cursor for 1 second (if enabled)

Volume/Brightness

(Specific gesture, usually thumb+index pinch distance)

Exit App

Press Q

Pause/Resume

Press P

Toggle Dwell Mode

Press D

Sensitivity

Press + or - to adjust


⚠️ Troubleshooting

Laggy Cursor? Ensure you are in a well-lit room so the camera can see your hands clearly.

Audio Errors? Make sure you have a working microphone enabled for the Voice Assistant.

Install Errors? If pyaudio fails to install, you may need to install pipwin first: pip install pipwin then pipwin install pyaudio.

📜 License

This project is open-source and available for educational purposes.
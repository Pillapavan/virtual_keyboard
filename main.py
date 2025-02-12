import cv2
from cvzone.HandTrackingModule import HandDetector
import time
import numpy as np
import streamlit as st
import os

# Define paths
OUTPUT_FILE = "typed_text.txt"

# Initialize the webcam
cap = cv2.VideoCapture(0)
cap.set(3, 1280)  # Set width
cap.set(4, 720)   # Set height

# Hand detector with higher detection confidence
detector = HandDetector(detectionCon=0.9, maxHands=1)

# Keyboard layout
keys = [['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
        ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L', ';'],
        ['Z', 'X', 'C', 'V', 'B', 'N', 'M', ',', '.', '/']]

numkeys = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0']
opkeys = ['+', '-', '*', '/', '=', 'Caps', 'Back', 'Enter', 'Space']

# Initialize text and Caps Lock state
finalText = ""
calculation = ""
caps_lock_on = False

class Button:
    def __init__(self, pos, text, size=[85, 85]):
        self.pos = pos
        self.size = size
        self.text = text

# Draw buttons
def drawAll(img, buttonList, typedText, caps_lock_on):
    overlay = img.copy()
    height, width, _ = img.shape

    # Output bar
    cv2.rectangle(overlay, (50, height - 90), (width - 50, height - 30), (50, 50, 50), cv2.FILLED)
    cv2.putText(img, typedText, (60, height - 45), cv2.FONT_HERSHEY_PLAIN, 3, (255, 255, 255), 3)

    for button in buttonList:
        x, y = button.pos
        w, h = button.size
        color = (0, 0, 255) if button.text == "Caps" and caps_lock_on else (255, 255, 255)
        cv2.rectangle(overlay, button.pos, (x + w, y + h), color, cv2.FILLED)
        cv2.rectangle(img, button.pos, (x + w, y + h), (0, 0, 0), 3)
        cv2.putText(img, button.text, (x + 20, y + 60), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 0), 3)

    alpha = 0.5
    img = cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)
    return img

# Create buttons
buttonList = []
for i in range(len(keys)):
    for x, key in enumerate(keys[i]):
        buttonList.append(Button([100 * x + 50, 100 * i + 50], key))

for x, key in enumerate(numkeys):
    buttonList.append(Button([100 * x + 50, 100 * len(keys) + 50], key))

for x, key in enumerate(opkeys):
    buttonList.append(Button([100 * x + 50, 100 * (len(keys) + 1) + 50], key))

# Save text to a file
def save_text_to_file(text):
    with open(OUTPUT_FILE, "w") as file:
        file.write(text)

# Initialize Streamlit session state
if "continue_loop" not in st.session_state:
    st.session_state["continue_loop"] = False

if "typed_text" not in st.session_state:
    st.session_state["typed_text"] = ""

# Home Page Design
st.title("📜 Virtual Keyboard Application")
st.sidebar.header("Navigation")

page = st.sidebar.radio(
    "Choose a page:",
    ["🏠 Home", "⌨️ Virtual Keyboard", "📁 File Operations"]
)

if page == "🏠 Home":
    st.header("Welcome to the Virtual Keyboard App")
    st.write("This app lets you use a virtual keyboard controlled by hand gestures via webcam.")
    st.markdown("""
    ### Features:
    - **Type** text using a webcam-based virtual keyboard.
    - **Save** your text to a file for future use.
    - **Edit** or **download** the text file conveniently.

    ### How to Use:
    1. Navigate to **Virtual Keyboard** to start typing.
    2. Save and manage your typed content under **File Operations**.
    3. Download or edit your file easily after typing.

    """)

elif page == "⌨️ Virtual Keyboard":
    st.header("Virtual Keyboard 🖐️")

    if st.button("Start Virtual Keyboard"):
        st.session_state["continue_loop"] = True
        st.write("**Virtual Keyboard is running...** Use your hand gestures to type.")
        frame_placeholder = st.empty()
        stop_button_placeholder = st.empty()

        if stop_button_placeholder.button("Stop Virtual Keyboard"):
            st.session_state["continue_loop"] = False

        prev_y = None
        is_tap_down = False
        tap_cooldown = time.time()
        active_key = None

        while st.session_state["continue_loop"] and cap.isOpened():
            success, img = cap.read()
            if not success:
                st.error("Failed to capture webcam feed.")
                break

            img = cv2.flip(img, 1)
            hands, img = detector.findHands(img, draw=True)
            img = drawAll(img, buttonList, st.session_state["typed_text"], caps_lock_on)

            if hands:
                hand = hands[0]
                lmlist = hand["lmList"]
                fingers = detector.fingersUp(hand)

                if fingers == [0, 1, 0, 0, 0]:
                    if len(lmlist) >= 21:
                        index_tip = lmlist[8][:2]
                        index_y = index_tip[1]

                        cv2.circle(img, tuple(index_tip), 15, (0, 255, 0), cv2.FILLED)

                        if prev_y is not None:
                            if not is_tap_down and index_y > prev_y + 10:
                                is_tap_down = True
                                active_key = None

                            elif is_tap_down and index_y < prev_y - 10 and time.time() - tap_cooldown > 0.3:
                                tap_cooldown = time.time()
                                is_tap_down = False

                                for button in buttonList:
                                    x, y = button.pos
                                    w, h = button.size
                                    if x < index_tip[0] < x + w and y < index_tip[1] < y + h:
                                        if active_key != button.text:
                                            active_key = button.text

                                            if button.text == "Caps":
                                                caps_lock_on = not caps_lock_on
                                            elif button.text == "Space":
                                                st.session_state["typed_text"] += ' '
                                            elif button.text == "Back":
                                                st.session_state["typed_text"] = st.session_state["typed_text"][:-1]
                                            elif button.text == "Enter":
                                                st.session_state["typed_text"] += '\n'
                                            elif button.text == '=':
                                                try:
                                                    result = str(eval(calculation))
                                                    st.session_state["typed_text"] = result
                                                    calculation = result
                                                except:
                                                    st.session_state["typed_text"] = "Error"
                                                    calculation = ""
                                            else:
                                                char = button.text.upper() if caps_lock_on else button.text.lower()
                                                st.session_state["typed_text"] += char

                                            save_text_to_file(st.session_state["typed_text"])

                        prev_y = index_y

            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            frame_placeholder.image(imgRGB, channels="RGB")

        cap.release()

elif page == "📁 File Operations":
    st.header("File Operations 📂")

    # Load file content
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, "r") as file:
            file_content = file.read()
    else:
        file_content = ""

    edited_content = st.text_area("Edit File Content:", value=file_content, height=200)

    if st.button("Save Changes"):
        with open(OUTPUT_FILE, "w") as file:
            file.write(edited_content)
        st.success("File updated successfully!")

    with open(OUTPUT_FILE, "rb") as file:
        st.download_button("Download File", data=file, file_name="typed_text.txt", mime="text/plain")

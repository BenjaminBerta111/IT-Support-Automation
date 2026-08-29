import os
import keyboard

# Standard Firefox path
FIREFOX_PATH = r"C:\Program Files\Mozilla Firefox\firefox.exe"
# The clean website you want to show
URL = "https://google.com"

def open_cover_tab():
    try:
        # Opens a brand new window with the normal URL bar and maximizes it
        os.system(f'"{FIREFOX_PATH}" -new-window {URL}')
    except Exception as e:
        pass

# TRIGGERS: Choose ONE of these options by uncommenting it (remove the #)
# Option A: A combination that won't interrupt normal typing (Recommended)
keyboard.add_hotkey('ctrl+space', open_cover_tab)

# Option B: A single button you never use for typing
# keyboard.add_hotkey('f12', open_cover_tab)

# Keeps the script running
keyboard.wait()

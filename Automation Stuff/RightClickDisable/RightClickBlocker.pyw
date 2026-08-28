import ctypes
from ctypes import wintypes
import threading
import time
import keyboard

# Native Windows Constants
WH_MOUSE_LL = 14
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205

# Global toggle state
right_click_blocked = True

# Explicitly load user32 and kernel32
user32 = ctypes.WinDLL('user32', use_last_error=True)
kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)

# 64-bit CRITICAL FIX: Define exact argument types for CallNextHookEx to prevent OverflowError
user32.CallNextHookEx.argtypes = [wintypes.HANDLE, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM]
user32.CallNextHookEx.restype = ctypes.c_int64

# Define the Callback type signature matching 64-bit Windows rules
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int64, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)

# This function intercepts mouse events safely
def low_level_mouse_handler(nCode, wParam, lParam):
    global right_click_blocked
    
    if nCode >= 0 and right_click_blocked:
        # Check for right click down or up
        if wParam in (WM_RBUTTONDOWN, WM_RBUTTONUP):
            return 1 # Drops the right-click cleanly
            
    # Safely forward all other actions (like moving the mouse) to Windows
    return user32.CallNextHookEx(None, nCode, wParam, lParam)

# Maintain the pointer globally so garbage collection doesn't delete it
mouse_pointer = HOOKPROC(low_level_mouse_handler)

def toggle_block():
    global right_click_blocked
    right_click_blocked = not right_click_blocked
    print(f"Right-click blocked status: {right_click_blocked}")
    time.sleep(0.2)

def start_mouse_hook():
    global mouse_pointer
    # Pass 0/None as the third argument to hook globally without error 128
    hook = user32.SetWindowsHookExW(WH_MOUSE_LL, mouse_pointer, 0, 0)
    
    if not hook:
        print(f"Hook Failed with error code: {ctypes.get_last_error()}")
        return

    print("Native Hook registered successfully!")
    
    # Run the continuous Windows message pump
    msg = wintypes.MSG()
    while user32.GetMessageW(ctypes.byref(msg), 0, 0, 0) != 0:
        user32.TranslateMessage(ctypes.byref(msg))
        user32.DispatchMessageW(ctypes.byref(msg))

# Bind the F8 hotkey
keyboard.add_hotkey('f8', toggle_block)
print("64-bit Hook Ready... Press F8 to toggle.")

# Spin off the hook into a background thread
hook_thread = threading.Thread(target=start_mouse_hook, daemon=True)
hook_thread.start()

# Keep script alive
while True:
    time.sleep(1)

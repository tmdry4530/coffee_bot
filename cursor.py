import pyautogui

try:
    while True:
        x, y = pyautogui.position()
        print(f"Current position: ({x}, {y})")
        pyautogui.sleep(1)
except KeyboardInterrupt:
    print("Program terminated")

2037,580
2157,306
2048,503
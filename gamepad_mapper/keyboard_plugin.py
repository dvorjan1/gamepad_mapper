import pyautogui
from time import sleep


class KeyboardPlugin:
    def __init__(self):
        pass

    def _keydown_action(self, params, event):
        pyautogui.keyDown(params[0])

    def _keyup_action(self, params, event):
        pyautogui.keyUp(params[0])

    def _keypress_action(self, params, event):
        pyautogui.press(params[0])

    def get_actions(self):
        return [
            ("keydown", self._keydown_action),
            ("keyup", self._keyup_action),
            ("keypress", self._keypress_action),
        ]

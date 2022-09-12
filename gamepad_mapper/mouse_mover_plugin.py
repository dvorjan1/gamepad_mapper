import pyautogui
from threading import Lock
import time


class MouseMoverPlugin:
    def __init__(self, period=10):
        self._period = period
        self._v_x = 0.0
        self._v_y = 0.0
        self._wanted_x = 0.0
        self._wanted_y = 0.0
        self._vlock = Lock()
        self._stop_flag = False
        self._last_sleep_timestamp = time.time()

    def deamon(self):
        self._stop_flag = False
        while True:
            wakeup_time = time.time()
            delta = wakeup_time - self._last_sleep_timestamp
            self._last_sleep_timestamp = wakeup_time
            xoffset, yoffset = None, None
            with self._vlock:
                if self._v_x != 0.0 or self._v_y != 0.0:
                    xoffset, yoffset = (self._v_x * delta, self._v_y * delta)
            if xoffset is not None:
                cur_x, cur_y = pyautogui.position()
                diff_x, diff_y = (abs(cur_x - self._wanted_x), abs(cur_y - self._wanted_y))
                if diff_x > 2.0 or diff_y > 2.0:
                    self._wanted_x, self._wanted_y = (cur_x, cur_y)
                self._wanted_x, self._wanted_y = (self._wanted_x + xoffset, self._wanted_y + yoffset)
                pyautogui.moveTo(self._wanted_x, self._wanted_y)
            sleep_delay = wakeup_time + self._period/1000.0 - time.time()
            if sleep_delay > 0:
                time.sleep(sleep_delay)
            if self._stop_flag:
                break

    def stop_deamon(self):
        self._stop_flag = True

    def _parse_scaled_value(self, params, event):
        variable = float(params[0]) if params[0].isnumeric() else event.state
        multiplier = float(params[1]) if len(params) > 1 else 1.0
        offset = float(params[2]) if len(params) > 2 else 0.0
        return multiplier * variable + offset

    def _set_mouse_velocity_x(self, params, event):
        v_x = self._parse_scaled_value(params, event)
        pyautogui.getActiveWindowTitle()
        with self._vlock:
            self._v_x = v_x

    def _set_mouse_velocity_y(self, params, event):
        v_y = self._parse_scaled_value(params, event)
        with self._vlock:
            self._v_y = v_y

    def _click(self, params, event):
        x, y = pyautogui.position()
        if len(params) > 0:
            if params[0] == 'right':
                pyautogui.click(x, y, button=pyautogui.RIGHT)
            elif params[0] == 'left':
                pyautogui.click(x, y, button=pyautogui.LEFT)
            elif params[0] == 'middle':
                pyautogui.click(x, y, button=pyautogui.MIDDLE)
            else:
                pyautogui.click(x, y)
        else:
            pyautogui.click(x, y)

    def _move_to(self, params, event):
        x, y = pyautogui.position()
        x = int(params[0]) if params[0].isnumeric() else x
        y = int(params[1]) if params[1].isnumeric() else y
        pyautogui.moveTo(x, y)

    def get_actions(self):
        return [
            ("mousevelx", self._set_mouse_velocity_x),
            ("mousevely", self._set_mouse_velocity_y),
            ("click", self._click),
            ("mousemove", self._move_to)
        ]

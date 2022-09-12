import pyautogui
from threading import Lock
from time import sleep


class MouseMoverPlugin:
    def __init__(self, period=10):
        self._period = period
        self._v_x = 0.0
        self._v_y = 0.0
        self._wanted_x = 0.0
        self._wanted_y = 0.0
        self._vlock = Lock()
        self._stop_flag = False

    def deamon(self):
        self._stop_flag = False
        while True:
            xoffset, yoffset = None, None
            with self._vlock:
                if self._v_x != 0.0 or self._v_y != 0.0:
                    xoffset = self._v_x * self._period / 1000
                    yoffset = self._v_y * self._period / 1000
            if xoffset is not None:
                cur_x, cur_y = pyautogui.position()
                diff_x = abs(cur_x - self._wanted_x)
                diff_y = abs(cur_y - self._wanted_y)
                if diff_x > 2.0 or diff_y > 2.0:
                    self._wanted_x = cur_x
                    self._wanted_y = cur_y
                self._wanted_x += xoffset
                self._wanted_y += yoffset
                pyautogui.moveTo(self._wanted_x, self._wanted_y, self._period)
            sleep(self._period)
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
        with self._vlock:
            self._v_x = v_x

    def _set_mouse_velocity_y(self, params, event):
        v_y = self._parse_scaled_value(params, event)
        with self._vlock:
            self._v_y = v_y

    def get_actions(self):
        return [
            ("mousevelx", self._set_mouse_velocity_x),
            ("mousevely", self._set_mouse_velocity_y),
        ]

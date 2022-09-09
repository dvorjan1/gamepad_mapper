import pyautogui
from threading import Lock
from time import sleep

class MouseMover:
    def __init__(self, period):
        self._period = period
        self._v_x = 0.0
        self._v_y = 0.0
        self._wanted_x = 0.0
        self._wanted_y = 0.0
        self._vlock = Lock()

    def run(self):
        while True:
            xoffset, yoffset = None, None
            with self._vlock:
                if self._v_x != 0.0 or self._v_y != 0.0:
                    xoffset = self._v_x*self._period/1000
                    yoffset = self._v_y*self._period/1000
            if xoffset is not None:
                cur_x, cur_y = pyautogui.position()
                diff_x = abs(cur_x - self._wanted_x)
                diff_y = abs(cur_y - self._wanted_y)
                if  diff_x > 2.0 or diff_y > 2.0:
                    self._wanted_x = cur_x
                    self._wanted_y = cur_y
                self._wanted_x += xoffset
                self._wanted_y += yoffset
                pyautogui.moveTo(self._wanted_x, self._wanted_y, self._period)
            sleep(self._period)

    def set_velocity(self, velocity_x = None, velocity_y = None):
        with self._vlock:
            if velocity_x is not None:
                self._v_x = velocity_x
            if velocity_y is not None:
                self._v_y = velocity_y

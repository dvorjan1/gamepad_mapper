import pyautogui
import re

class MapperAction:
    def __init__(self, action_string: str):
        self._action = self._parse_action_string(action_string)

    def _keydown_action(self, params, event):
        pyautogui.keyDown(params[0])

    def _keyup_action(self, params, event):
        pyautogui.keyUp(params[0])

    def _keypress_action(self, params, event):
        pyautogui.press(params[0])

    def _dummy_action(self, params, event):
        print("Error: Dummy action called")

    def _generate_action(self, function_name:str, params):
        fcn = self._dummy_action
        function_name_lc = function_name.lower()
        if function_name_lc == "keydown":
            fcn = self._keydown_action
        elif function_name_lc == "keyup":
            fcn = self._keyup_action
        elif function_name_lc == "keypress":
            fcn = self._keypress_action
        return lambda event: fcn(params, event)
    
    def _parse_action_string(self, action_string: str):
        match = re.match("([^\(].*)\(([^\)]*)\).*", action_string)
        function_name = match.group(1)
        params = list(map(lambda x: x.strip(), match.group(2).split(",")))
        if len(params) == 2 and params[0] == '' and params[1] == '': # TODO: Dirty hack to include also comma
            params = [',']
        return self._generate_action(function_name, params)

    def perform(self, event):
        self._action(event)
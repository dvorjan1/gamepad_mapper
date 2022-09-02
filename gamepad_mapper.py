import inputs
import pyautogui
import json
import os
import re
from pystray import Icon, Menu, MenuItem
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from PIL import Image

IMAGE_FOLDER = 'images'
CONFIG_FOLDER = 'configurations'
ICON_FILE_NAME = 'icon.png'
DEFAULT_PROFILE_NAME = 'Default profile'

class MapperConfiguration:
    def __init__(self, file_name):
        self.json = self._read_configuration(file_name)

    def _read_configuration(self, file_name):
        with open(file_name, 'r') as configuration_file:
            return json.load(configuration_file)

    def get_name(self):
        return self.json['profile']['name']

    def get_mappings(self):
        return self.json['mappings']

    def get_mapping(self, mapping_id):
        return self.get_mappings()[mapping_id]

class GamePadRouting:
    def __init__(self, routing_tuples = None):
        self.routing = routing_tuples if routing_tuples is not None else {0:0}

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

class MapperCondition:
    def __init__(self, condition_string: str) -> None:
        self._condition, self._code = self._parse_condition_string(condition_string)

    def _dummy_check(self, params):
        print("Error: Dummy function checked")

    def _set_check(self, params, event):
        return event.code == params[0] and \
            event.ev_type == 'Key' and \
            event.state == 1

    def _unset_check(self, params, event):
        return event.code == params[0] and \
            event.ev_type == 'Key' and \
            event.state == 0

    def _equal_check(self, params, event):
        return event.code == params[0] and \
            event.ev_type == 'Absolute' and \
            event.state == int(params[1])

    def _generate_condition(self, condition_name, params):
        fcn = self._dummy_check
        function_name_lc = condition_name.lower()
        if function_name_lc == "set":
            fcn = self._set_check
        elif function_name_lc == "unset":
            fcn = self._unset_check
        elif function_name_lc == "equal":
            fcn = self._equal_check
        return lambda event: fcn(params, event)

    def _parse_condition_string(self, condition_string:str):
        match = re.match("([^\(].*)\(([^\)]*)\).*", condition_string)
        condition_name = match.group(1)
        params = list(map(lambda x: x.strip(), match.group(2).split(",")))
        if len(params) == 2 and params[0] == '' and params[1] == '': # TODO: Dirty hack to include also comma
            params = [',']
        return self._generate_condition(condition_name, params), params[0]

    def get_code(self):
        return self._code

    def check(self, event):
        return self._condition(event)

class GamepadMapper:
    class GamepadMapperEventTuple:
        def __init__(self, checker, action) -> None:
            self.checker = checker
            self.action = action

    def __init__(self, mapper_configuration, routing = GamePadRouting()) -> None:
        self.mapping_evaluation_map = self._generate_evaluation_map(mapper_configuration)
        self.mapping_evaluation_map_counter = 0
        self._mapping_evaluation_map_lock = Lock()
        self.routing = routing
        self.routing_counter = 0
        self._routing_lock = Lock()
        self._pool = None
        self._futures = []

    def _generate_evaluation_map(self, mapping: MapperConfiguration):
        evaluation_map = []
        for device_mapping in mapping.get_mappings():
            device_evaluation_map = dict()
            for key in device_mapping:
                checker = MapperCondition(key)
                action = MapperAction(device_mapping[key])
                code = checker.get_code()
                if code not in device_evaluation_map:
                    device_evaluation_map[code] = []
                device_evaluation_map[code].append(self.GamepadMapperEventTuple(checker, action))
            evaluation_map.append(device_evaluation_map)
        return evaluation_map

    def evaluate_event(self, device_id, event):
        # print((device_id, event.code, event.state, event.ev_type))
        if event.code in self.mapping_evaluation_map[device_id]:
            for possible_record in self.mapping_evaluation_map[device_id][event.code]:
                if possible_record.checker.check(event):
                    possible_record.action.perform(event)

    def set_configuration(self, configuration: MapperConfiguration):
        self.mapping_evaluation_map = self._generate_evaluation_map(configuration)

    def set_routing(self, routing: GamePadRouting):
        self.routing = routing

    def _gamepad_main_loop(self, gamepad_index):
        while 1:
            events = inputs.devices.gamepads[gamepad_index].read()
            for event in events:
                self.evaluate_event(self.routing.routing[gamepad_index], event)

    def _thread_done(self, future):
        if future:
            if future.done():
                if future.exception():
                    future.result()
                future = None

    def run(self):
        num_devices = len(inputs.devices.gamepads)
        if num_devices == 0:
            print('No gamepad device found')
        else:
            self._pool = ThreadPoolExecutor(num_devices)
            self._futures = []
            for device in range(num_devices):
                self._futures.append(self._pool.submit(lambda: self._gamepad_main_loop(device)))
                self._futures[-1].add_done_callback(self._thread_done)


class GamepadMapperGui:
    def __init__(self) -> None:
        configurations = self._get_configurations()
        self.configuration_dict = dict()
        for configuration in configurations:
            self.configuration_dict[configuration.get_name()] = configuration
        self.mapper = GamepadMapper(self.configuration_dict[DEFAULT_PROFILE_NAME])

    def _get_configurations(self):
        configurations = []
        configs_folder = os.path.join(os.path.dirname(__file__), CONFIG_FOLDER)
        for file_name in os.listdir(configs_folder):
            configurations.append(MapperConfiguration(os.path.join(configs_folder, file_name)))
        return configurations

    def _select_configuration(self, icon, item: MenuItem):
        self.mapper.set_configuration(self.configuration_dict[item.text])

    def _close(self, icon, item: MenuItem):
        icon.stop()
        os._exit(0) # Kill process => kill also stuck threads

    def run(self):
        menuitems = []
        for configuration_name in self.configuration_dict:
            menuitems.append(MenuItem(configuration_name, self._select_configuration))
        menuitems.append(MenuItem("Close", self._close))
        
        icon_image = Image.open(os.path.join(os.path.dirname(__file__), IMAGE_FOLDER, ICON_FILE_NAME))

        self.mapper.run()

        Icon(
            "Gamepad mapper",
            icon_image,
            menu=Menu(*menuitems),
        ).run()

if __name__ == "__main__":
    GamepadMapperGui().run()
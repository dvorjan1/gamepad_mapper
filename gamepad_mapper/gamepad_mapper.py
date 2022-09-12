import inputs
import copy
import re
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from .gamepad_routing import GamePadRouting
from .mapper_configuration import MapperConfiguration
from .mapper_action import MapperAction
from .mapper_condition import MapperCondition

MAX_PLUGINS = 500  # 500 in magic number! - probably we will never use more plugins ;-)


class GamepadMapper:
    class GamepadMapperEventTuple:
        def __init__(self, checker, action) -> None:
            self.checker = checker
            self.action = action

    def __init__(self, mapper_configuration, routing=GamePadRouting()) -> None:
        self._plugins = self._load_plugins(mapper_configuration)
        self.mapping_evaluation_map = self._generate_evaluation_map(
            mapper_configuration, self._plugins
        )
        self.mapping_evaluation_map_counter = 0
        self._mapping_evaluation_map_lock = Lock()
        self.routing = routing
        self.routing_counter = 0
        self._routing_lock = Lock()
        self._pool = None
        self._futures = []

    def _load_plugins(self, mapping: MapperConfiguration):
        plugins = []
        camel_to_snake_pattern = re.compile(r"(?<!^)(?=[A-Z])")
        for plugin_class_name in mapping.get_plugins():
            plugin_file_name = camel_to_snake_pattern.sub(
                "_", plugin_class_name
            ).lower()
            plugin_ns = {}
            exec(
                f"from .{plugin_file_name} import {plugin_class_name}\nplugin={plugin_class_name}()\n",
                globals(),
                plugin_ns
            )
            plugins.append(plugin_ns["plugin"])
        return plugins

    def _generate_evaluation_map(self, mapping: MapperConfiguration, plugins):
        evaluation_map = []
        for device_mapping in mapping.get_mappings():
            device_evaluation_map = dict()
            for key in device_mapping:
                checker = MapperCondition(key)
                action = MapperAction(device_mapping[key], plugins)
                code = checker.get_code()
                if code not in device_evaluation_map:
                    device_evaluation_map[code] = []
                device_evaluation_map[code].append(
                    self.GamepadMapperEventTuple(checker, action)
                )
            evaluation_map.append(device_evaluation_map)
        return evaluation_map

    def evaluate_event(self, device_id, event, mapping_evaluation_map):
        # print((device_id, event.code, event.state, event.ev_type))
        if event.code in mapping_evaluation_map[device_id]:
            for possible_record in mapping_evaluation_map[device_id][event.code]:
                if possible_record.checker.check(event):
                    possible_record.action.perform(event)

    def set_configuration(self, configuration: MapperConfiguration):
        with self._mapping_evaluation_map_lock:
            self.mapping_evaluation_map_counter += 1
            plugins = self._load_plugins(configuration)
            self.mapping_evaluation_map = self._generate_evaluation_map(configuration, plugins)
            self._refresh_deamons(plugins)
            self._plugins = plugins

    def set_routing(self, routing: GamePadRouting):
        with self._routing_lock:
            self.routing_counter += 1
            self.routing = routing

    def _gamepad_main_loop(self, gamepad_index):
        mapping_evaluation_map_local = None
        mapping_evaluation_map_counter_local = -1
        routing_local = None
        routing_counter_local = -1

        while 1:
            events = inputs.devices.gamepads[gamepad_index].read()

            with self._mapping_evaluation_map_lock:
                if (
                    mapping_evaluation_map_counter_local
                    != self.mapping_evaluation_map_counter
                ):
                    mapping_evaluation_map_local = copy.deepcopy(
                        self.mapping_evaluation_map
                    )
            with self._routing_lock:
                if routing_counter_local != self.routing_counter:
                    routing_local = copy.deepcopy(self.routing)

            for event in events:
                self.evaluate_event(
                    routing_local.routing[gamepad_index],
                    event,
                    mapping_evaluation_map_local,
                )

    def _thread_done(self, future):
        if future:
            if future.done():
                if future.exception():
                    future.result()
                future = None

    def kill_running_deamons(self):
        num_devices = len(inputs.devices.gamepads)
        old_plugins_with_deamon = filter(
            lambda plugin: hasattr(plugin, "stop_deamon"), self._plugins
        )
        if (
            len(self._futures) > num_devices
        ):  # Refresh while changing profile, not during first run (no need to stop deamons which are not running yet)
            for old_plugin in old_plugins_with_deamon:
                old_plugin.stop_deamon()

    def _refresh_deamons(self, new_plugins):
        num_devices = len(inputs.devices.gamepads)
        self.kill_running_deamons()
        del self._futures[num_devices:]  # Remove killed deamons from futures
        plugins_with_deamon = filter(
            lambda plugin: hasattr(plugin, "deamon"), new_plugins
        )
        for plugin in plugins_with_deamon:
            self._futures.append(self._pool.submit(plugin.deamon))
            self._futures[-1].add_done_callback(self._thread_done)

    def run(self):
        num_devices = len(inputs.devices.gamepads)
        self._pool = ThreadPoolExecutor(num_devices + MAX_PLUGINS)
        self._futures = []

        if num_devices == 0:
            print("No gamepad device found")
        else:
            for device in range(num_devices):
                self._futures.append(
                    self._pool.submit(lambda: self._gamepad_main_loop(device))
                )
                self._futures[-1].add_done_callback(self._thread_done)

        self._refresh_deamons(self._plugins)

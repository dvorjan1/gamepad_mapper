import inputs
import copy
from threading import Lock
from concurrent.futures import ThreadPoolExecutor
from .gamepad_routing import GamePadRouting
from .mapper_configuration import MapperConfiguration
from .mapper_action import MapperAction
from .mapper_condition import MapperCondition


class GamepadMapper:
    class GamepadMapperEventTuple:
        def __init__(self, checker, action) -> None:
            self.checker = checker
            self.action = action

    def __init__(self, mapper_configuration, routing=GamePadRouting()) -> None:
        self.mapping_evaluation_map = self._generate_evaluation_map(
            mapper_configuration
        )
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
            self.mapping_evaluation_map = self._generate_evaluation_map(configuration)

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

    def run(self):
        num_devices = len(inputs.devices.gamepads)
        if num_devices == 0:
            print("No gamepad device found")
        else:
            self._pool = ThreadPoolExecutor(num_devices)
            self._futures = []
            for device in range(num_devices):
                self._futures.append(
                    self._pool.submit(lambda: self._gamepad_main_loop(device))
                )
                self._futures[-1].add_done_callback(self._thread_done)

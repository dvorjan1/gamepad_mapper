class GamePadRouting:
    def __init__(self, routing_tuples = None):
        self.routing = routing_tuples if routing_tuples is not None else {0:0}
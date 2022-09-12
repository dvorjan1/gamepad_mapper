import re


class MapperAction:
    def __init__(self, action_string: str, plugins):
        self._possible_actions = self._generate_possible_actions(plugins)
        self._action = self._parse_action_string(action_string)

    def _generate_possible_actions(self, plugins):
        actions = []
        plugins_with_actions = filter(
            lambda plugin: hasattr(plugin, "get_actions"), plugins
        )
        for plugin in plugins_with_actions:
            actions.extend(plugin.get_actions())
        return actions

    def _dummy_action(self, params, event):
        print("Error: Dummy action called")

    def _generate_action(self, function_name: str, params):
        function_name_lc = function_name.lower()
        for action_tuple in self._possible_actions:
            if action_tuple[0].lower() == function_name_lc:
                return lambda event: action_tuple[1](params, event)
        return lambda event: self._dummy_action(params, event)

    def _parse_action_string(self, action_string: str):
        match = re.match("([^\(].*)\(([^\)]*)\).*", action_string)
        function_name = match.group(1)
        params = list(map(lambda x: x.strip(), match.group(2).split(",")))
        if (
            len(params) == 2 and params[0] == "" and params[1] == ""
        ):  # TODO: Dirty hack to include also comma
            params = [","]
        return self._generate_action(function_name, params)

    def perform(self, event):
        self._action(event)

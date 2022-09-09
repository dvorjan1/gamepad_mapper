import re

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

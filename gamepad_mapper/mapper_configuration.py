import json

class MapperConfiguration:
    def __init__(self, file_name):
        self.json = self._read_configuration(file_name)

    def _read_configuration(self, file_name):
        with open(file_name, 'r') as configuration_file:
            return json.load(configuration_file)

    def get_name(self):
        return self.json['profile']['name']

    def get_plugins(self):
        try:
            return self.json['profile']['plugins']
        except:
            return None

    def get_mappings(self):
        return self.json['mappings']

    def get_mapping(self, mapping_id):
        return self.get_mappings()[mapping_id]
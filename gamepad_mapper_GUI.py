import os
from time import sleep
from pystray import Icon, Menu, MenuItem
from PIL import Image
from gamepad_mapper.gamepad_mapper import GamepadMapper
from gamepad_mapper.mapper_configuration import MapperConfiguration

IMAGE_FOLDER = "images"
CONFIG_FOLDER = "configurations"
ICON_FILE_NAME = "icon.png"
DEFAULT_PROFILE_NAME = "Default profile"


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
            configurations.append(
                MapperConfiguration(os.path.join(configs_folder, file_name))
            )
        return configurations

    def _select_configuration(self, icon, item: MenuItem):
        self.mapper.set_configuration(self.configuration_dict[item.text])

    def _close(self, icon, item: MenuItem):
        icon.stop()

    def run(self):
        menuitems = []
        for configuration_name in self.configuration_dict:
            menuitems.append(MenuItem(configuration_name, self._select_configuration))
        menuitems.append(MenuItem("Close", self._close))

        icon_image = Image.open(
            os.path.join(os.path.dirname(__file__), IMAGE_FOLDER, ICON_FILE_NAME)
        )

        self.mapper.run()

        Icon(
            "Gamepad mapper",
            icon_image,
            menu=Menu(*menuitems),
        ).run()


if __name__ == "__main__":
    GamepadMapperGui().run()
    os._exit(0)  # Kill process => kill also stuck threads

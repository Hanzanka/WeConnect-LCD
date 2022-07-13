import logging
from display.lcd_controller import LCDController
from .lcd_scene import LCDScene
from threading import Thread


LOG = logging.getLogger("lcd_scene_controller")


class LCDSceneController:
    def __init__(self) -> None:
        LOG.debug("Initializing LCDSceneController")
        self.__selected_scene = None
        self.__last_scenes = {}
        self.__lcd_controller = LCDController(self)

    @property
    def lcd_controller(self) -> LCDController:
        return self.__lcd_controller

    def restore_last_view(self) -> None:
        LOG.debug("Restoring last LCDScene")
        if self.__selected_scene is not None:
            self.refresh(self.__selected_scene)

    def refresh(self, scene) -> None:
        if self.__selected_scene.id == scene.id:
            self.__lcd_controller.update_lcd(scene.content)

    def start(self, scene: LCDScene) -> None:
        LOG.debug("Starting LCDSceneController")
        self.__selected_scene = scene
        scene.load()

    def add_scene(self, scene: LCDScene) -> None:
        LOG.debug(f"Adding new LCDScene (ID: {scene.id}) to LCDSceneController")
        self.__scenes.append(scene)

    def back(self) -> None:
        if not self.__lcd_controller.can_interact:
            return

        target_scene = None
        try:
            target_scene = self.__last_scenes[self.__selected_scene]
        except KeyError:
            return

        LOG.debug(f"Returning to last LCDScene (ID: {target_scene.id})")

        self.__last_scenes.pop(self.__selected_scene, None)
        self.__selected_scene.exit()

        self.__selected_scene = target_scene
        self.__selected_scene.load()

    def __load_next_scene(self, scene: LCDScene) -> None:
        LOG.info(f"Loading next LCDScene (ID: {scene.id})")
        self.__last_scenes[scene] = self.__selected_scene
        self.__selected_scene.exit()

        self.__selected_scene = scene
        self.__selected_scene.load()

    def next(self) -> None:
        if not self.__lcd_controller.can_interact:
            return

        target = self.__selected_scene.next
        
        if target is None:
            return

        if isinstance(target, tuple):
            function = target[0]
            args = target[1]
            Thread(target=function, args=([] if args is None else [args])).start()
            return

        if isinstance(target, LCDScene):
            self.__load_next_scene(scene=target)

    def up(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        self.__selected_scene.scroll(way="up")

    def down(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        self.__selected_scene.scroll(way="down")

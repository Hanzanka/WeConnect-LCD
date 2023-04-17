from display.lcd_controller import LCDController
from .lcd_scene import LCDScene
from threading import Thread
from .lcd_status_bar import LCDStatusBar
import logging


LOG = logging.getLogger("lcd_scene_controller")


class LCDSceneController:
    def __init__(self) -> None:
        '''
        Controls the LCDScenes displayed on the LCD screen.
        '''
        
        LOG.debug("Initializing LCDSceneController")
        self.__home_scene = None
        self.__selected_scene = None
        self.__status_bar = None
        self.__last_scenes = {}
        self.__lcd_controller = LCDController(self)
        LOG.debug("Successfully initialized LCDSceneController")

    @property
    def lcd_controller(self) -> LCDController:
        return self.__lcd_controller

    def set_status_bar(self, status_bar: LCDStatusBar) -> None:
        '''
        Sets the status bar displayed on top of the LCD screen.

        Args:
            status_bar (LCDStatusBar): Provides the icons to be displayed on the LCD screen.
        '''
        
        self.__status_bar = status_bar

    def update_status_bar(self) -> None:
        if self.__selected_scene is not None:
            self.refresh(self.__selected_scene)

    def set_home_scene(self, scene: LCDScene) -> None:
        '''
        Sets the home screen. This LCDScene is loaded when returning from LCDScenes that are not loaded by items.

        Args:
            scene (LCDScene): The LCDScene which will be used as home screen.
        '''
        
        LOG.info(f"Setting new home screen LCDScene (ID: {scene.id})")
        self.__home_scene = scene

    def home(self) -> None:
        '''
        Loads the home screen.
        '''
        
        self.__last_scenes.clear()
        self.load_scene(self.__home_scene)

    def restore_last_view(self) -> None:
        if self.__selected_scene is not None:
            self.refresh(self.__selected_scene)

    def refresh(self, scene) -> None:
        if self.__selected_scene.id == scene.id:
            if scene.has_title:
                scene_content = scene.content
                icons = self.__status_bar.icons
                scene_content[0] = scene_content[0][: -len(icons)] + icons
                self.__lcd_controller.update_lcd(scene_content)
                return
            self.__lcd_controller.update_lcd(scene.content)

    def load_scene(self, scene: LCDScene) -> None:
        self.__selected_scene = scene
        scene.load()

    def back(self) -> None:
        if not self.__lcd_controller.can_interact:
            return

        target_scene = None
        try:
            target_scene = self.__last_scenes[self.__selected_scene]
        except KeyError:
            return

        self.__last_scenes.pop(self.__selected_scene, None)
        self.__selected_scene.exit()

        self.__selected_scene = target_scene
        self.__selected_scene.load()

    def __load_next_scene(self, scene: LCDScene) -> None:
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
            Thread(target=function, args=([] if args is None else args)).start()
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

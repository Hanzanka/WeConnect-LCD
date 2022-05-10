import logging
from display.lcd_controller import LCDController
from .lcd_scene import LCDScene


logger = logging.getLogger("scene_controller")


class LCDSceneController:
    def __init__(self) -> None:
        logger.debug("Initializing lcd scene controller")
        self.__selected_scene = None
        self.__selected_scene_id = None
        self.__last_scenes = {}
        self.__lcd_controller = LCDController(self)
    
    def get_lcd_controller(self) -> LCDController:
        return self.__lcd_controller
    
    def restore_last_view(self) -> None:
        logger.debug("Restoring last lcd view")
        if self.__selected_scene is not None:
            self.__selected_scene.refresh()
    
    def refresh(self, scene_id, content: list) -> None:
        logger.debug("Refreshing current lcd view")
        if self.__selected_scene_id == scene_id:
            self.__lcd_controller.update_lcd(content)
    
    def start(self, scene: LCDScene) -> None:
        logger.debug("Starting lcd scene controller")
        self.__selected_scene = scene
        self.__selected_scene_id = scene.id
        scene.load()
    
    def add_scene(self, scene: LCDScene) -> None:
        logger.info("Added new lcd scene to lcd scene controller")
        self.__scenes.append(scene)
    
    def back(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        
        logger.info("Returning to last lcd scene")
        target_scene = None
        try:
            target_scene = self.__last_scenes[self.__selected_scene]
        except KeyError:
            return
        
        self.__last_scenes.pop(self.__selected_scene, None)
        self.__selected_scene.exit()
        
        self.__selected_scene = target_scene
        self.__selected_scene_id = target_scene.id
        self.__selected_scene.load()
    
    def next(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        
        target_scene = self.__selected_scene.get_selected_item().target
        if target_scene is None:
            return
        
        logger.info("Entering new lcd scene")
        self.__last_scenes[target_scene] = self.__selected_scene
        self.__selected_scene.exit()
        
        self.__selected_scene = target_scene
        self.__selected_scene_id = target_scene.id
        self.__selected_scene.load()
    
    def up(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        logger.debug("Going up")
        self.__selected_scene.scroll(way="up")
    
    def down(self) -> None:
        if not self.__lcd_controller.can_interact:
            return
        logger.debug("Going down")
        self.__selected_scene.scroll(way="down")

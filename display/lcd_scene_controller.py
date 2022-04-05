import logging
from display.lcd_controller import LCDController
from .lcd_scene import LCDScene


class LCDSceneController:
    def __init__(self) -> None:
        self.__selected_scene = None
        self.__selected_scene_id = None
        self.__last_scenes = {}
        self.__controls_enabled = True
        self.__lcd_controller = LCDController(self)
    
    def get_lcd_controller(self) -> LCDController:
        return self.__lcd_controller
    
    def restore_last_view(self) -> None:
        self.__selected_scene.refresh()
    
    def refresh(self, scene_id, content: list, bypass_screensaver=False) -> None:
        if self.__selected_scene_id == scene_id:
            self.__lcd_controller.update_lcd(content, bypass_screensaver=bypass_screensaver)
    
    def start(self, scene: LCDScene) -> None:
        self.__selected_scene = scene
        self.__selected_scene_id = scene.id
        scene.load()
    
    def add_scene(self, scene: LCDScene) -> None:
        self.__scenes.append(scene)
    
    def back(self) -> None:
        if not self.__controls_enabled:
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
    
    def next(self) -> None:
        if not self.__controls_enabled:
            return
        
        target_scene = self.__selected_scene.get_selected_item().target
        if target_scene is None:
            return
        
        self.__last_scenes[target_scene] = self.__selected_scene
        self.__selected_scene.exit()
        
        self.__selected_scene = target_scene
        self.__selected_scene.set_lcd_scene_controller(self)
        self.__selected_scene.load()
    
    def up(self) -> None:
        if not self.__lcd_controller.can_interact:
            logging.info("Controls are not enabled")
            return
        self.__selected_scene.scroll(way="up")
    
    def down(self) -> None:
        if not self.__lcd_controller.can_interact:
            logging.info("Controls are not enabled")
            return
        self.__selected_scene.scroll(way="down")

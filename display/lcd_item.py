class LCDItem:
    def __init__(self, title, target=None, center=True) -> None:
        self._scenes = []
        self._content = ""
        self._title = title
        self.__target = target
        self.__center = center
        self._selected = False
        if issubclass(LCDItem, self.__class__):
            self._convert_to_string()
    
    def _convert_to_string(self) -> None:
        if self._selected:
            self._content = f">{self._title}".center(20) if self.__center else f">{self._title}"
            return
        self._content = self._title.center(20) if self.__center else self._title
    
    def add_scene(self, scene) -> None:
        self._scenes.append(scene)
    
    def select(self) -> None:
        self._selected = True
        self._convert_to_string()
        
    def unselect(self) -> None:
        self._selected = False
        self._convert_to_string()
    
    @property
    def target(self):
        return self.__target
    
    @target.setter
    def target(self, scene) -> None:
        self.__target = scene
    
    @property
    def content(self) -> str:
        return self._content

class LCDItem:
    def __init__(
        self,
        id,
        title,
        second_title=None,
        target=None,
        target_args=None,
        content_centering=True,
    ) -> None:
        self._id = id
        self._title = title
        self._second_title = second_title
        self.__target = target
        self.__target_args = target_args
        self.__content_centering = content_centering
        self._scenes = []
        self._selected = False
        self.unselect()

    def update_content(self, title=None, second_title=None) -> None:
        if title is not None:
            self._title = title
        if second_title is not None:
            self._second_title = second_title
        if self._selected:
            self.select()
        else:
            self.unselect()
        for scene in self._scenes:
            scene.update()

    def select(self) -> None:
        self._selected = True
        if self.__content_centering:
            self._content = f">{self._title} {self._second_title}".center(20)
        else:
            self._content = (
                f">{self._title}{self._second_title:>{19 - len(self._title)}}"
            )

    def unselect(self) -> None:
        self._selected = False
        if self.__content_centering:
            self._content = f"{self._title} {self._second_title}".center(20)
        else:
            self._content = (
                f"{self._title}{self._second_title:>{20 - len(self._title)}}"
            )

    def add_scene(self, scene) -> None:
        self._scenes.append(scene)

    @property
    def content(self) -> str:
        return self._content

    @property
    def target(self):
        if callable(self.__target):
            return self.__target, self.__target_args
        return self.__target

    @property
    def id(self):
        return self._id

    @property
    def content_centering(self) -> bool:
        return self.__content_centering

    @content_centering.setter
    def content_centering(self, content_centering: bool) -> None:
        self.__content_centering = content_centering

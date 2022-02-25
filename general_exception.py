class GeneralException(Exception):
    def __init__(self, message: str, fatal: bool) -> None:
        super().__init__()
        self.message = message
        self.fatal = fatal
        
    def __str__(self) -> str:
        return self.message

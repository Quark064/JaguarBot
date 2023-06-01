class Logger:
    """ Log errors to the command line. """

    def __init__(self, moduleName: str) -> None:
        self.name = moduleName
    
    def log(self, msg: str, indent: int = 0) -> None:
        """ Log a message."""
        self.__print(msg, "•", indent)
    
    def warn(self, msg: str, indent: int = 0) -> None:
        """ Log a warning."""
        self.__print(msg, "!", indent)
    
    def question(self, msg: str, indent: int = 0) -> None:
        """ Log a question."""
        self.__print(msg, "?", indent)
    
    def __print(self, msg: str, icon: str, indent: int) -> None:  
        """ Internal helper method to standardize logging. """
        dents = []

        for _ in range(0, indent):
            dents.append("    ")

        print(f"[{icon}] {self.name: >16}: {''.join(dents)}{msg}")  
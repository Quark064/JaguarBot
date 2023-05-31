class Logger:
    """ Log errors to the command line. """

    def __init__(self, moduleName: str) -> None:
        self.name = moduleName
    
    def log(self, msg: str, indent: int = 0) -> None:
        self.__print(msg, "•", indent)
    
    def warn(self, msg: str, indent: int = 0) -> None:
        self.__print(msg, "!", indent)
    
    def question(self, msg: str, indent: int = 0) -> None:
        self.__print(msg, "?", indent)
    
    def __print(self, msg: str, icon: str, indent: int) -> None:  
        message = []

        for _ in range(0, indent):
            message.append("    ")

        message.append(f"[{icon}] {self.name: >16}: {msg}")  
        print("".join(message))
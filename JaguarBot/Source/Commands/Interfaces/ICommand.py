class ICommand:
    def register() -> None:
        """ Register the command with the Discord interface. """
        raise(NotImplementedError)
    
    async def run() -> None:
        """ Define code that should run when the command is triggered. """
        raise(NotImplementedError)
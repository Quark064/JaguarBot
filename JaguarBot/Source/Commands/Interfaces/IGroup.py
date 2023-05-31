from ICommand import ICommand

class IGroup:
    def addSubCommand(self, command: ICommand) -> None:
        """ Register a subcommand in a group. """
        raise(NotImplementedError)
    
    def register(self) -> None:
        """ Register the group and subcommands. """
        raise(NotImplementedError)
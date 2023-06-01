from Commands.NSO.Login import Login

from Commands.Debug.Ping import Ping
from Commands.Debug.Status import Status
from Commands.Debug.RefreshVolatileTokens import RefreshVolatileTokens
from Commands.Debug.ShowToken import ShowToken

from Commands.SplatNet3.OnlineFriends import OnlineFriends


# Define commands independent of a group.
INDEPENDENT = []

# Define groups and their associated commands.
GROUPS = {
    "debug": {
        "description": "Diagnose issues with the bot.",
        "guilds": [920851074116636692, 443128138331979776],
        "commands": [Ping, Status, RefreshVolatileTokens, ShowToken]
    },
    "nso": {
        "description": "Manage NSO Authentication.",
        "guilds": [920851074116636692, 443128138331979776],
        "commands": [Login]
    },
    "s3": {
        "description": "Interact with SplatNet3",
        "guilds": [920851074116636692, 443128138331979776],
        "commands": [OnlineFriends]
    }
}

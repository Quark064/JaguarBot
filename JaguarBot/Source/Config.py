from Commands.Debug.Status import Status
from Commands.Debug.Ping import Ping
from Commands.NSO.Login import Login

# COMMANDS ---------------
# Define commands independent of a group.
INDEPENDENT = []

# Define groups and their associated commands.
GROUPS = {
    "debug": {
        "description": "Diagnose issues with the bot.",
        "guilds": [920851074116636692, 443128138331979776],
        "commands": [Ping, Status]
    },
    "nso": {
        "description": "Manage NSO Authentication.",
        "guilds": [920851074116636692, 443128138331979776],
        "commands": [Login]
    }
}

# SERVER SETTINGS --------
SERVER_NAME    = "NSlashO"
SERVER_VERSION = "0.0.1"

DATABASE_PATH = "Database"
DATABASE_NAME = "UserDB.sqlite"

F_ENDPOINT = "https://nxapi-znca-api.fancy.org.uk/api/znca/f"

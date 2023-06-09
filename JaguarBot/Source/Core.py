import discord
from os import environ
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import Config
import CommandTree
from Helpers.Logger import Logger
from NSOAuth.VersionManager import VersionManager
from Database.Models import Base


def main():

    # Depends on CWD, run from 'Source' folder.
    engine = create_engine(f"sqlite:///{Config.DATABASE_PATH}/{Config.DATABASE_NAME}")
    Base.metadata.create_all(engine)
    
    logger = Logger("Core")
    bot = discord.Bot()

    with Session(engine) as session:
        logger.log("Attempting to get application newest versions...")
        if VersionManager(session).updateVersions():
            logger.log("Got the latest versions!")
        else:
            logger.warn("Failed to get the latest versions.")
   
    for command in CommandTree.INDEPENDENT:
        command.register(bot, engine)
    
    for group in CommandTree.GROUPS:
        currGroup = CommandTree.GROUPS[group]
        slashGroup = bot.create_group(
            group,
            currGroup["description"],
            currGroup["guilds"]
        )
        for command in currGroup["commands"]:
            command.register(bot, engine, slashGroup)


    @bot.event
    async def on_ready():
        logger.log(f"Connected to {bot.user}!")


    logger.log("Logging into Discord...")
    bot.run(environ["DiscordBotToken"])


if __name__ == "__main__":
    main()
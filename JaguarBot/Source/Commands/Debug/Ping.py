from discord import Bot, ApplicationContext, SlashCommandGroup
from sqlalchemy import Engine
from Commands.Interfaces.ICommand import ICommand

class Ping(ICommand):
    """ Test the bot latency. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def ping(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):
        await ctx.respond(f"Running at {round(bot.latency*1000)}ms")
from discord import Bot, ApplicationContext, SlashCommandGroup
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from Database.Models import User, Token, AppVersion
from Commands.Interfaces.ICommand import ICommand


class Status(ICommand):
    """ A Hello World to ensure the bot is operational. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def status(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):
        with Session(dbEngine) as session:
            msg = ["**WOLF-BOT** *Jaguar rev.*"]
            
            msg.append(f"\t• Running at {round(bot.latency*1000)}ms.")
            msg.append("\t• Database Status:")
            msg.append(f"\t\t| User: {len(session.query(User).all())} rows.")
            msg.append(f"\t\t| Token: {len(session.query(Token).all())} rows.")
            msg.append(f"\t\t| AppVersion: {len(session.query(AppVersion).all())} rows.")
            
            await ctx.respond("\n".join(msg))
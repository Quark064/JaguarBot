from discord import Bot, ApplicationContext, SlashCommandGroup
from discord import Embed, Colour, EmbedField
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from Database.Models import User, Token, AppVersion, GraphQLQuery
from Commands.Interfaces.ICommand import ICommand


class Status(ICommand):
    """ Request the database and network status of the bot. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def status(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):
        with Session(dbEngine) as session:

            dbObjects = [User, Token, AppVersion, GraphQLQuery]

            fieldList = []
            fieldList.append(EmbedField("Latency", f"```Running at {round(bot.latency*1000)}ms```"))

            for object in dbObjects:
                fieldList.append(EmbedField(f"{object.__name__} Rows", f"```{len(session.query(object).all())}```", inline=True))

            outEmbed = Embed(
                title="**Bot Status:** Jaguar.ink",
                color=Colour.from_rgb(0, 255, 255),
                fields=fieldList
            )
            
            await ctx.respond(embed=outEmbed)
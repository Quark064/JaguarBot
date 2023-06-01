from discord import Bot, ApplicationContext, SlashCommandGroup
from discord import Embed, Colour, EmbedField
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from time import time

from Commands.Interfaces.ICommand import ICommand
from Database.Models import FindAbstractor, TokenType
from Helpers.Logger import Logger
from NSOAuth.RefreshManager import RefreshManager
from Config import INFO_EMBED_COLOR

class RefreshVolatileTokens(ICommand):
    """ Refresh GameWeb & Bullet tokens. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def refresh_volatile_tokens(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):
        startTime = time()
        logger = Logger("RefreshVolTokens")
        
        with Session(dbEngine) as session:
            fAbs = FindAbstractor(session)
            userObj = fAbs.getUserFromDID(ctx.author.id)

            if userObj == None:
                await ctx.respond("Cannot refresh your tokens because you are not authenticated. Use `/login` to log in.")
                return
            
            await ctx.defer(ephemeral=True)

            updateToken = await RefreshManager.refreshGameWeb(session, userObj)
            if updateToken:
                logger.log(f"User {ctx.author.id} refreshed GameWeb and Bullet Tokens.")

                newGToken = fAbs.getToken(userObj, TokenType.GAME_WEB)
                newBToken = fAbs.getToken(userObj, TokenType.BULLET)

                outEmbed = Embed(
                    title="Refreshed GameWeb and Bullet tokens!",
                    color=Colour.from_rgb(*INFO_EMBED_COLOR),
                    fields=[
                        EmbedField("GameWeb Token", f"```{newGToken.value}```"),
                        EmbedField("Bullet Token", f"```{newBToken.value}```")
                    ]
                )
                outEmbed.set_footer(text=f"Took {(time()-startTime):.2f} seconds")

                await ctx.followup.send(embed=outEmbed, ephemeral=True)

            else:
                logger.warn(f"An issue occurred attempting to refresh tokens for User {ctx.author.id}!")
                await ctx.followup.send("The tokens failed to refresh.")

                

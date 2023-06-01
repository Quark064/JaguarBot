from discord import Bot, ApplicationContext, SlashCommandGroup, Option
from discord import Embed, EmbedField, Colour
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from time import time

from Commands.Interfaces.ICommand import ICommand
from Database.Models import TokenType
from Database.Ext import FindAbstractor
from Config import INFO_EMBED_COLOR

class ShowToken(ICommand):
    """ Display a token. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst

        tokenTypeType = Option(str, choices=['Session', 'GameWeb', 'Bullet'])
        
        @regGroup.command(description=__class__.__doc__)
        async def get_token(ctx: ApplicationContext, token_type: tokenTypeType): #type: ignore
            await __class__.run(ctx, botInst, db, token_type)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine, tokenType: str):      
        with Session(dbEngine) as session:
            fAbs = FindAbstractor(session)
            userObj = fAbs.getUserFromDID(ctx.author.id)

            if userObj == None:
                await ctx.respond("You have not authenticated with your Nintendo account. Use `/login` to log in.")
                return 
            
            match tokenType:
                case "Session":
                    tkType = TokenType.SESSION
                case "GameWeb":
                    tkType = TokenType.GAME_WEB
                case "Bullet":
                    tkType = TokenType.BULLET
                case _:
                    await ctx.respond("Invalid token type specified.")
                    return
            
            rToken = fAbs.getToken(userObj, tkType)
            timeRemaining = int(rToken.expiresAt - time())
                
            outEmbed = Embed(
                title=f"**{tokenType} Token**",
                color=Colour.from_rgb(*INFO_EMBED_COLOR),
                fields=[
                    EmbedField("Expires", f"```{rToken.expiresAt}```"),
                    EmbedField("Value", f"```{rToken.value}```")
                ]
            )

            if timeRemaining <= 0:
                outEmbed.set_footer(text=f"Token has expired.")
            else:
                outEmbed.set_footer(text=f"Estimated Time Remaining: {int(timeRemaining/60)} minutes")
            
            await ctx.respond(embed=outEmbed, ephemeral=True)
from discord import Bot, ApplicationContext, SlashCommandGroup
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from discord.channel import DMChannel
from discord import Message, Member, User
from functools import partial
from asyncio import TimeoutError
from time import time

from Commands.Interfaces.ICommand import ICommand
from NSOAuth.TokenManager import TokenManager, Status, TKError
from NSOAuth.VersionManager import VersionManager
from Database.Models import User as dbUser
from Database.Models import Token, TokenType
from NSOAuth.TokenManager import *

class EXP_OFFSET:
    SESSION = 63072000
    GTOKEN  = 21600
    BULLET  = 7000

class Login(ICommand):
    """ Login to provide access to NSO services. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def login(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)

    @staticmethod
    def waitCheck(msg: Message, author: User|Member) -> bool:
        return (type(msg.channel) == DMChannel) and (msg.author == author)

    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):

        # Preliminary Checks ------
        with Session(dbEngine) as dbSession:
            instance = dbSession.query(dbUser).filter_by(discordID=ctx.author.id).first()
            if instance:
                await ctx.respond("You've already logged into a Nintendo Account. Use the `nso logout` command to change accounts.", ephemeral=True, delete_after=8)
                return
            
            vInfo = VersionManager(dbSession).getAppVersions()

        if not ctx.author.can_send():
            await ctx.respond("You must have DM permissions enabled to log in.", ephemeral=True, delete_after=8)
        

        # Begin DM Login Process ------
        if type(ctx.channel) != DMChannel:
            await ctx.respond("Sent login URL to DMs!", ephemeral=True, delete_after=8)
        
        tkManager = TokenManager(vInfo)
        authInfo = await tkManager.generateNSOLoginLink()

        loginMsg = await ctx.author.send(f"Please log in to your Nintendo Account using the following link: {authInfo.url}")

        try:
            userWaitCheck = partial(__class__.waitCheck, author=ctx.author)
            urlResponse: Message = await bot.wait_for('message', check=userWaitCheck, timeout=240)
            await loginMsg.delete()
        except TimeoutError:
            await loginMsg.edit(content="The session timed out. Please run the command again to login.")
            return
        

        # Attempt Token Generation ------
        loginMsg = await ctx.author.send("Attempting authentication with your Nintendo Account...")

        sessionToken = await tkManager.generateSessionToken(urlResponse.content, authInfo)

        sessionExp = int(time()) + EXP_OFFSET.SESSION

        if sessionToken.result.status != Status.OK:
            match(sessionToken.result.errorType):
                case TKError.INVALID_URL:
                    await ctx.author.send("The provided URL was incorrect. Please try running the command again.")
                    return
                case TKError.GET_FAILURE:
                    await ctx.author.send("Failed to authenticate with Nintendo. Please try again later.")
                    return
                case _:
                    await ctx.author.send("An unknown error occurred. Please try again later.")
                    return
        
        await loginMsg.edit(content="Attempting authentication with SplatNet3...")

        gToken = await tkManager.generateGToken(sessionToken.value)
        gTokenExp = int(time()) + EXP_OFFSET.GTOKEN
        
        if gToken.result.status != Status.OK:
            await ctx.author.send(f"Something went wrong: {gToken.result.message}")
            return

        bulletToken = await tkManager.generateBulletToken(sessionToken.value, gToken.value)
        bulletTokenExp = int(time()) + EXP_OFFSET.GTOKEN

        if bulletToken.result.status != Status.OK:
            await ctx.author.send(f"Something went wrong: {bulletToken.result.message}")
            return


        # Add New Info to DataBase ------
        with Session(dbEngine) as dbSession:
            newUser = dbUser(discordID=ctx.author.id)

            newSToken = Token(user=newUser, type=TokenType.SESSION,  value=sessionToken.value, expiresAt=sessionExp)
            newGToken = Token(user=newUser, type=TokenType.GAME_WEB, value=gToken.value,       expiresAt=gTokenExp)
            newBToken = Token(user=newUser, type=TokenType.BULLET,   value=bulletToken.value,  expiresAt=bulletTokenExp)

            dbSession.add_all([newUser, newSToken, newGToken, newBToken])
            dbSession.commit()

        await ctx.author.send("Successfully authenticated! You can now use SplatNet3 commands.")
        await loginMsg.delete()
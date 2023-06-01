from discord import Bot, ApplicationContext, SlashCommandGroup
from discord import Embed, Colour, EmbedField
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from Commands.Interfaces.ICommand import ICommand
from Database.Ext import FindAbstractor
from NSOAuth.GraphQL.FriendListQuery import FriendListQuery
from Config import INFO_EMBED_COLOR, DISCORD_EMOJI

class OnlineFriends(ICommand):
    """ Displays all of your currently-playing Splatoon 3 friends. """

    @staticmethod
    def register(botInst: Bot, db: Engine, group: SlashCommandGroup|None = None) -> None:
        regGroup = group if group is not None else botInst
        
        @regGroup.command(description=__class__.__doc__)
        async def online_friends(ctx: ApplicationContext):
            await __class__.run(ctx, botInst, db)


    @staticmethod
    async def run(ctx: ApplicationContext, bot: Bot, dbEngine: Engine):
        with Session(dbEngine) as session:
            fAbs = FindAbstractor(session)
            userObj = fAbs.getUserFromDID(ctx.author.id)

            if userObj == None:
                await ctx.respond("Cannot use this command because you are not logged in. Use `/login` to log in.")
                return

            await ctx.defer()

            friendQuery = FriendListQuery(session, userObj)
            
            if not await friendQuery.sendGQLRequest():
                await ctx.followup.send(content="Failed to get friends from the server.")
                return
            
            onlineFriends = friendQuery.getPlayingFriends()
            if not onlineFriends:
                await ctx.followup.send(content="No friends are currently playing.")
                return
            
            embedFields = []
            for player in onlineFriends:
                if not player["vsMode"]:
                    embedFields.append(EmbedField(player["playerName"], f"{player['onlineState']} - {DISCORD_EMOJI.SALMON_RUN}"))
                else:
                    embedFields.append(EmbedField(player["playerName"], f"{player['vsMode']['name']} - {DISCORD_EMOJI.ANARCHY}"))
            
            outputEmbed = Embed(
                title  = f"Currently Playing Friends: {len(onlineFriends)}",
                color  = Colour.from_rgb(*INFO_EMBED_COLOR),
                fields = embedFields
            )
            
            await ctx.followup.send(embed=outputEmbed)
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
            
            numFriendsOnline, onlineFriends = friendQuery.getPlayingFriends()
            if not onlineFriends:
                await ctx.followup.send(content="No friends are currently playing.")
                return
            
            embedFields = []
            for player in onlineFriends:                
                if player["coopRule"]:
                    match(player["coopRule"]):
                        case "BIG_RUN":
                            mode  = "Big Run"
                            emoji = DISCORD_EMOJI.BIG_RUN
                        case "TEAM_CONTEST":
                            mode = "Eggstra Work"
                            emoji = DISCORD_EMOJI.EGGSTRA_WORK
                        case _:
                            mode = "Salmon Run"
                            emoji = DISCORD_EMOJI.SALMON_RUN

                elif player["vsMode"]:
                    mode = player["vsMode"]["name"]
                    match(player["vsMode"]["mode"]):
                        case "BANKARA":
                            emoji = DISCORD_EMOJI.ANARCHY
                        case "FEST":
                            emoji = DISCORD_EMOJI.SPLATFEST
                        case "LEAGUE":
                            emoji = DISCORD_EMOJI.LEAGUE
                        case "PRIVATE":
                            emoji = DISCORD_EMOJI.PRIVATE_BATTLE
                        case "REGULAR":
                            emoji = DISCORD_EMOJI.TURF_WAR
                            mode  = "Turf War"
                        case "X_MATCH":
                            emoji = DISCORD_EMOJI.X_BATTLE
                
                else:
                    continue

                nameStr = f"{emoji} {player['playerName']} {':lock:' if player['isLocked'] else ''}"

                embedFields.append(EmbedField(nameStr, mode))

            outputEmbed = Embed(
                title  = f"Currently Playing Friends: {numFriendsOnline}",
                color  = Colour.from_rgb(*INFO_EMBED_COLOR),
                fields = embedFields
            )

            outputEmbed.set_footer(text=f"{len(onlineFriends)} of {numFriendsOnline} displayed.")
            
            await ctx.followup.send(embed=outputEmbed)
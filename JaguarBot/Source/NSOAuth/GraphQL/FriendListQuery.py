from sqlalchemy.orm import Session

from Database.Models import User
from NSOAuth.GraphQL.GQLRequest import GQLRequest


class FriendListQuery(GQLRequest):
    MAX_PLAYERS = 25
    def __init__(self, dbSession: Session, user: User) -> None:
        self.queryName = __class__.__name__
        self.loggerName = __class__.__name__

        super().__init__(dbSession, user)

    def getPlayingFriends(self) -> list:
        """ Returns the first MAX_PLAYERS players currently in game. """
        
        friendList = self.gqlResult['data']['friends']['nodes']
        
        onlineFriends = []
        for friend in friendList:
            friendStatus = friend['onlineState']
            if friendStatus != 'ONLINE' and friendStatus != 'OFFLINE':
                onlineFriends.append(friend)
            else:
                break
        
        return onlineFriends[0:self.MAX_PLAYERS]

from sqlalchemy.orm import Session
from time import time

from Database.Models import User, TokenType, FindAbstractor
from NSOAuth.VersionManager import VersionManager
from NSOAuth.TokenManager import TokenManager, Status
from Config import EXP_OFFSET

class RefreshManager:
    """ Refresh expired tokens. """

    @staticmethod
    async def refreshGameWeb(dbSession: Session, user: User) -> bool:
        """ Refresh the GameWeb token and any tokens afterwards. """
        tkManager = TokenManager(VersionManager(dbSession).getAppVersions())
        fAbs = FindAbstractor(dbSession)

        sessionToken = fAbs.getToken(user, TokenType.SESSION).value
        gToken = await tkManager.generateGToken(sessionToken)

        if gToken.result.status != Status.OK:
            return False
        
        bToken = await tkManager.generateBulletToken(sessionToken, gToken.value)

        if bToken.result.status != Status.OK:
            return False
        
        userGTokenObj = fAbs.getToken(user, TokenType.GAME_WEB)
        userBTokenObj = fAbs.getToken(user, TokenType.BULLET)

        userGTokenObj.value = gToken.value
        userBTokenObj.value = bToken.value

        userGTokenObj.expiresAt = int(time() + EXP_OFFSET.GTOKEN)
        userBTokenObj.expiresAt = int(time() + EXP_OFFSET.BULLET)
        
        dbSession.commit()

        return True
    

    @staticmethod
    async def refreshBullet(dbSession: Session, user: User) -> bool:
        """ Refresh the Bullet Token. """
        tkManager = TokenManager(VersionManager(dbSession).getAppVersions())
        fAbs = FindAbstractor(dbSession)

        sessionToken = fAbs.getToken(user, TokenType.SESSION).value
        gToken =       fAbs.getToken(user, TokenType.GAME_WEB).value
        
        bToken = await tkManager.generateBulletToken(sessionToken, gToken)

        if bToken.result.status != Status.OK:
            return False
        
        userBTokenObj = fAbs.getToken(user, TokenType.BULLET)

        userBTokenObj.value = bToken.value
        userBTokenObj.expiresAt = int(time() + EXP_OFFSET.BULLET)
        dbSession.commit()

        return True
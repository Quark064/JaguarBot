from Database.Models import AppVersion
from sqlalchemy import select
from sqlalchemy.orm import Session
import requests, json
from dataclasses import dataclass

@dataclass
class VersionInfo:
    nsoVersion: str
    s3Version: str

class VersionManager:
    """ Manages and updates the AppVersions in the Database. """

    NSO_VALUE_NAME = "NSOVersion"
    S3_VALUE_NAME  = "S3Version"
    GQL_VALUE_NAME = "GraphQLHashes"

    NSO_UPDATE_URL = "https://raw.githubusercontent.com/nintendoapis/nintendo-app-versions/main/data/coral-google-play.json"
    S3_UPDATE_URL  = "https://raw.githubusercontent.com/nintendoapis/nintendo-app-versions/main/data/splatnet3-app.json"
    GQL_UPDATE_URL = "https://raw.githubusercontent.com/imink-app/SplatNet3/master/Data/splatnet3_webview_data.json"


    def __init__(self, dbSession: Session) -> None:
        self.dbSession = dbSession
    

    def getAppVersions(self) -> VersionInfo:
        """ Return a VersionInfo with the """
        return VersionInfo(self.__nsoVersion(), self.__s3Version())

    def getGQLHashes(self) -> dict:
        """ Return a dict of GraphQL Hashes. """
        return json.loads(self.__gqlVersion())

    def updateVersions(self) -> bool:
        """ Attempts to update the app versions from hosted API. """
        try:
            result = requests.get(self.NSO_UPDATE_URL)
            nsoVersion = json.loads(result.text)["version"]
            
            result = requests.get(self.S3_UPDATE_URL)
            s3Version = json.loads(result.text)["web_app_ver"]

            result = requests.get(self.GQL_UPDATE_URL)
            gqlHashes = str(json.loads(result.text)["graphql"]["hash_map"])
        except Exception:
            return False
        else:
            nsoEntry = self.__getEntry(self.NSO_VALUE_NAME)
            s3Entry  = self.__getEntry(self.S3_VALUE_NAME)
            gqlEntry = self.__getEntry(self.GQL_VALUE_NAME)

            nsoEntry.version = nsoVersion
            s3Entry.version  = s3Version
            gqlEntry.version = gqlHashes
            
            self.dbSession.commit()

            return True
    

    def __gqlVersion(self) -> str:
        """ Return a JSON of GraphQL Hashes from the DB."""
        return self.__getEntry(self.GQL_VALUE_NAME).version

    def __s3Version(self) -> str:
        """ Return the S3 Applet version stored in the DB. """
        return self.__getEntry(self.S3_VALUE_NAME).version
    
    def __nsoVersion(self) -> str:
        """ Return the NSO App Version Stored in the DB. """
        return self.__getEntry(self.NSO_VALUE_NAME).version

    def __getEntry(self, value: str) -> AppVersion:
        """ Internal helper method to retrieve AppVersion objects. """
        stmt = select(AppVersion).where(AppVersion.name==value)
        return self.dbSession.scalars(stmt).one()


            


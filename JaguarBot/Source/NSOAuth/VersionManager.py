from sqlalchemy import select
from sqlalchemy.orm import Session
import requests, json
from dataclasses import dataclass

from Database.Models import AppVersion, GraphQLQuery
from Database.Ext import getOrCreate

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
        """ Return a VersionInfo with NSO and S3 versions from the database."""
        return VersionInfo(self.__nsoVersion(), self.__s3Version())


    def updateVersions(self) -> bool:
        """ Attempts to update the app versions from hosted API. """
        try:
            result = requests.get(self.NSO_UPDATE_URL)
            nsoVersion = json.loads(result.text)["version"]
            
            result = requests.get(self.S3_UPDATE_URL)
            s3Version = json.loads(result.text)["web_app_ver"]

            result = requests.get(self.GQL_UPDATE_URL)
            gqlHashes = json.loads(result.text)["graphql"]["hash_map"]
        except Exception:
            return False
        else:
            self.__getEntry(self.NSO_VALUE_NAME).version = nsoVersion
            self.__getEntry(self.S3_VALUE_NAME).version  = s3Version
            
            for name, hash in gqlHashes.items():
                self.__getHashObj(name).hash = hash

            self.dbSession.commit()

            return True


    def __s3Version(self) -> str:
        """ Return the S3 Applet version stored in the DB. """
        return self.__getEntry(self.S3_VALUE_NAME).version
    
    def __nsoVersion(self) -> str:
        """ Return the NSO App Version Stored in the DB. """
        return self.__getEntry(self.NSO_VALUE_NAME).version

    def __getEntry(self, name: str) -> AppVersion:
        """ Internal helper method to retrieve AppVersion objects. """
        return getOrCreate(self.dbSession, AppVersion, name=name)
    
    def __getHashObj(self, name: str) -> GraphQLQuery:
        """ Internal helper method to retrieve AppVersion objects. """
        return getOrCreate(self.dbSession, GraphQLQuery, name=name)


import pypyodbc
import Constants 
class PoliticalPartyModel:
    def __init__(self, politicalPartyID=0, politicalPartyName=""):
        self.politicalPartyID = politicalPartyID
        self.politicalPartyName = politicalPartyName
    
    @staticmethod
    def getAllPolicalPartiesIDName():
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT politicalPartyID, politicalPartyName FROM PoliticalPartyMaster ORDER BY politicalPartyName"
        cur3.execute(sqlcmd)
        politicalpartiesList = []
        while True:
            crow = cur3.fetchone()
            if not crow:
                break
            ppmodel = PoliticalPartyModel(crow[0], crow[1])
            politicalpartiesList.append(ppmodel)
        return politicalpartiesList   
    
    @staticmethod
    def getPoliticalPartyByID(rid):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT politicalPartyID, politicalPartyName FROM PoliticalPartyMaster WHERE politicalPartyID = '"+str(rid)+"'"
        cur3.execute(sqlcmd)
        row = cur3.fetchone()
        politicalPartymodel = None
        if row:
            politicalPartymodel = PoliticalPartyModel(row[0], row[1])
        return politicalPartymodel    
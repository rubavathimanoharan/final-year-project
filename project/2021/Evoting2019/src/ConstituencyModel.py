import pypyodbc
import Constants 
class ConstituencyModel:
    def __init__(self, constituencyID=0, constituencyName="", state="", userID="", userModel=None):
        self.constituencyID = constituencyID
        self.constituencyName = constituencyName
        self.state = state
        self.userID = userID
        self.userModel = userModel
    
    @staticmethod
    def getAllConstituenciesIDName():
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT constituencyID, constituencyName FROM ConstituencyMaster ORDER BY constituencyName"
        cur3.execute(sqlcmd)
        constituencies = []
        while True:
            crow = cur3.fetchone()
            if not crow:
                break
            consmodel = ConstituencyModel(crow[0], crow[1])
            constituencies.append(consmodel)
        return constituencies
        
    @staticmethod
    def getConstituencyNameByID(rid):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT constituencyID, constituencyName FROM ConstituencyMaster WHERE constituencyID = '"+str(rid)+"'"
        cur3.execute(sqlcmd)
        row = cur3.fetchone()
        constituencyModel = None
        if row:
            constituencyModel = ConstituencyModel(row[0], row[1])
        return constituencyModel    
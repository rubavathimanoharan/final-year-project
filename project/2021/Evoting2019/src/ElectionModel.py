import pypyodbc
import Constants 
class ElectionModel:
    def __init__(self, electionID=0, electionName="", nominationLastDate=None, effDate=None, userID="", userModel=None):
        self.electionID = electionID
        self.electionName = electionName
        self.effDate = effDate
        self.nominationLastDate = nominationLastDate
        self.userID = userID
        self.userModel = userModel
    
    @staticmethod
    def getAllElection():
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT electionID, electionName FROM ElectionDetails ORDER BY electionName"
        cur3.execute(sqlcmd)
        elections = []
        while True:
            erow = cur3.fetchone()
            if erow == None:
                break;
            electionmodel = ElectionModel(erow[0], erow[1])
            elections.append(electionmodel)
        return elections 
    
    @staticmethod
    def getElectionNameByID(electionID):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT electionID, electionName FROM ElectionDetails WHERE electionID = '"+str(electionID)+"'"
        cur3.execute(sqlcmd)
        erow = cur3.fetchone()
        electionmodel = None
        if erow:
            electionmodel = ElectionModel(erow[0], erow[1])
        return electionmodel   

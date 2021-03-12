import pypyodbc
import Constants
from ContestantModel import ContestantModel
from ElectionModel import ElectionModel

from PoliticalPartyModel import PoliticalPartyModel
from ConstituencyModel import ConstituencyModel
class ElectionNominationModel:
    def __init__(self, uniqueID=0, electionID=0, electionModel=None, contestantID=0, contestantModel = None, politicalPartyID=0, politicalPartyModel=None, constituencyID=0, constituencyModel=None):
        self.uniqueID = uniqueID
        self.electionID = electionID
        self.electionModel = electionModel
        self.contestantID = contestantID
        self.contestantModel = contestantModel
        self.politicalPartyID = politicalPartyID
        self.politicalPartyModel = politicalPartyModel
        
        self.constituencyID = constituencyID
        self.constituencyModel = constituencyModel
        
        
    @staticmethod
    def ElectionNominationgetElectionByID(rid):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT * FROM ContestantElectionDetails WHERE uniqueID = '"+str(rid)+"'"
        print(sqlcmd)
        cur3.execute(sqlcmd)
        row = cur3.fetchone()
        electionNominationModel = None
        if row:
            contestantObject = ContestantModel.getContestantNameByID(row[1])
            politicalPartyObject = PoliticalPartyModel.getPoliticalPartyByID(row[2])
            electionObject = ElectionModel.getElectionNameByID(row[3])
            print(contestantObject.firstName)
            
            constituencyObject = ConstituencyModel.getConstituencyNameByID(row[4])
            
            electionNominationModel = ElectionNominationModel(row[0], electionID=row[1], electionModel=electionObject, contestantID= row[2],  contestantModel = contestantObject, politicalPartyID=row[3], politicalPartyModel = politicalPartyObject, constituencyID = row[4], constituencyModel=constituencyObject)
        return electionNominationModel  
    
    
    @staticmethod
    def getAllContestantByElectionByConstituency(electionID, constituencyID):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = """SELECT ContestantMaster.contestantID, firstName FROM ContestantMaster 
                    INNER JOIN ContestantElectionDetails ON ContestantElectionDetails.contestantID = ContestantMaster.contestantID 
                    AND  ContestantElectionDetails.electionID = '"""+str(electionID)+"""' 
                    AND ContestantElectionDetails.constituencyID = '"""+str(constituencyID)+"""'"""
        print(sqlcmd)
        cur3.execute(sqlcmd)
        
        contestantsList = []
        while True:
            row = cur3.fetchone()
            if not row:
                break
            contestantModel = ContestantModel(row[0], firstName=row[1])
            contestantsList.append(contestantModel)
        return contestantsList
    
    @staticmethod
    def getPoliticalPartyNameByElectionByConstituencyByContestantID(electionID, constituencyID, contestantID):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = """SELECT politicalPartyName FROM ContestantElectionDetails 
                    INNER JOIN PoliticalPartyMaster ON PoliticalPartyMaster.PoliticalPartyID = ContestantElectionDetails.PoliticalPartyID 
                    AND  ContestantElectionDetails.electionID = '"""+str(electionID)+"""' 
                    AND ContestantElectionDetails.constituencyID = '"""+str(constituencyID)+"""'
                    AND ContestantElectionDetails.contestantID = '"""+str(contestantID)+"""'"""
        print(sqlcmd)
        cur3.execute(sqlcmd)
        
        politicalPatyName = ""
        row = cur3.fetchone()
        if row:
            politicalPatyName = row[0]
        return politicalPatyName 
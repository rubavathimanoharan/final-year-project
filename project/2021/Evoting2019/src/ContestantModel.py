import pypyodbc
import Constants
class ContestantModel:
    def __init__(self, contestantID, title="", firstName="", middleName="", lastName="", wardNumber="", streetName="", area="", city="", district="", state="", dob=None, addressProof="", ageProof="", constituencyID=0, constituencyModel = None, isApproved=0, ssn="", mobileNbr="", emailID="", password=""):
        self.contestantID = contestantID
        self.title = title
        self.firstName = firstName
        self.middleName = middleName
        self.lastName = lastName
        self.wardNumber = wardNumber
        self.streetName = streetName
        self.city = city
        self.district = district
        self.state = state
        self.dob = dob
        self.addressProof = addressProof
        self.ageProof = ageProof
        self.constituencyID = constituencyID
        self.constituencyModel = constituencyModel
        self.isApproved = isApproved
        self.ssn = ssn
        self.mobileNbr = mobileNbr
        self.emailID = emailID
        self.password = password
        
        
    @staticmethod
    def getContestantNameByID(rid):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT contestantID, firstName FROM ContestantMaster WHERE contestantID = '"+str(rid)+"'"
       
        cur3.execute(sqlcmd)
        row = cur3.fetchone()
        contestantModel = None
        if row:
            contestantModel = ContestantModel(row[0], firstName= row[1])
            
        return contestantModel  
    
    @staticmethod
    def getContestantNameByEmailID(emailID):
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        
        sqlcmd = "SELECT contestantID, firstName FROM ContestantMaster WHERE emailID = '"+str(emailID)+"'"
        print("DDDDDDDDDDDDDDDDDDDDD", sqlcmd)
        cur3.execute(sqlcmd)
        row = cur3.fetchone()
        contestantModel = None
        if row:
            contestantModel = ContestantModel(row[0], firstName=row[1])
        return contestantModel   
    
      
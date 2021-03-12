class RoleModel:
    def __init__(self, roleID=0,roleName="",isVoter=0, isContestant=0, isAdmin=0,isElectionOfficer=0,isElectionCommissioner=0,isPolticalParty=0,isPublic=0,canBlockChainGeneration=0, canBlockChainReport=0):
        self.roleID = roleID
        self.roleName = roleName
        self.isVoter = isVoter
        self.isContestant = isContestant
        self.isAdmin = isAdmin
        self.isElectionOfficer = isElectionOfficer
        self.isElectionCommissioner = isElectionCommissioner
        self.isPolticalParty = isPolticalParty
        self.isPublic = isPublic
        self.canBlockChainGeneration = canBlockChainGeneration
        self.canBlockChainReport = canBlockChainReport
        
        
        
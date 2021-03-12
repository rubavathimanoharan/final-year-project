from flask import Flask, request, render_template, jsonify, redirect, url_for
import xml.etree.ElementTree as ET 
import pypyodbc 
import os
import hashlib
import json
import time
from datetime import datetime, timedelta, date
import ftplib


from PoliticalPartyModel import PoliticalPartyModel
from RoleModel import RoleModel

from UserModel import UserModel
from VoteDataModel import VoteDataModel
import Constants
from ConstituencyModel import ConstituencyModel
from Constants import connString
from VoterModel import VoterModel
from ContestantModel import ContestantModel
from ElectionModel import ElectionModel
from ElectionNominationModel import ElectionNominationModel

app = Flask(__name__)
globalUserObject = None
globalRoleObject = None

errorResult = ""
errType = ""

def initialize():
    errorResult = ""
    errType=""
    
@app.route("/")
def home():
    initialize()
    roleObject = None
    return render_template('Login.html')

@app.route("/processLogin", methods=['POST'])
def authenticateLogin():
    global globalUserObject, globalRoleObject
    global errorResult, errType
   
    initialize()
    
    emailID = request.form['emailID']
    print(11222)
    password = request.form['password']
    
    conn1 = pypyodbc.connect(Constants.connString)
    cur1 = conn1.cursor()
    sqlcmd1 = "SELECT * FROM UserMaster WHERE emailID = '"+emailID+"' AND password = '"+password+"'"; 
    cur1.execute(sqlcmd1)
    row = cur1.fetchone()
    cur1.commit()
    if not row:
        return render_template('Login.html', processResult="Invalid Userid / Password")
    globalUserObject = UserModel(row[0], emailID=emailID, password=password);
    cur2 = conn1.cursor()
    sqlcmd2 = "SELECT * FROM RoleMaster WHERE roleID = '"+str(row[4])+"'"; 
    cur2.execute(sqlcmd2)
    row2 = cur2.fetchone()
    if not row2:
        return render_template('Login.html', processResult="Invalid Role")
    globalRoleObject = RoleModel(row2[0], row2[1],row2[2],row2[3],row2[4],row2[5],row2[6],row2[7],row2[8])
    
    cur2.commit()
    conn1.close();
    
    #return render_template('Dashboard.html')
    return redirect(url_for('Dashboard')) 

@app.context_processor
def inject_role():
    global globalUserObject, globalRoleObject
    
    return dict(globalRoleObject=globalRoleObject)

@app.route("/ChangePassword")
def changePassword():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    initialize()
    return render_template('ChangePassword.html')

@app.route("/ProcessChangePassword", methods=['POST'])
def processChangePassword():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    initialize()
    oldPassword= request.form['oldPassword']
    newPassword= request.form['newPassword']
    confirmPassword= request.form['confirmPassword']
    conn1 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur1 = conn1.cursor()
    sqlcmd1 = "SELECT * FROM Users WHERE  emailID = '"+globalUserObject.emailID+"' AND password = '"+oldPassword+"'"; 
    cur1.execute(sqlcmd1)
    row = cur1.fetchone()
    cur1.commit()
    if not row:
        return render_template('ChangePassword.html', msg="Invalid Old Password")
    
    if newPassword.strip() != confirmPassword.strip() :
       return render_template('ChangePassword.html', msg="New Password and Confirm Password are NOT same")
    
    
    sqlcmd1 = "UPDATE Users SET password = '"+newPassword+"' WHERE emailID = '"+globalUserObject.emailID+"'"; 
    cur1.execute(sqlcmd1)
    cur1.commit()
    return render_template('ChangePassword.html', msg="Password Changed Successfully")

@app.route("/Dashboard")
def Dashboard():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    initialize()

    conn1 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur1 = conn1.cursor()
    
    if globalRoleObject.isVoter:
        sqlcmd1 = "SELECT * FROM VoterMaster WHERE  emailID = '"+globalUserObject.emailID+"'"; 

        cur1.execute(sqlcmd1)
        row = cur1.fetchone()
        cur1.commit()
        vmodel = VoterModel(0);
        if row:
            vmodel = VoterModel(row[0], row[1], row[2], row[3], row[4], isApproved=row[15])
        print(vmodel.firstName, vmodel.middleName, vmodel.lastName, vmodel.isApproved)
        cur1.close()
        conn1.close()
        return render_template('Dashboard.html', vmodel=vmodel, dashboardMsg="Voter Dashboard")
        
    if globalRoleObject.isContestant:
        sqlcmd1 = "SELECT * FROM ContestantMaster WHERE  emailID = '"+globalUserObject.emailID+"'"; 
        cur1.execute(sqlcmd1)
        row = cur1.fetchone()
        cur1.commit()
        cmodel = ContestantModel(0);
        if row:
            cmodel = ContestantModel(row[0], row[1], row[2], row[3], row[4], isApproved=row[15])
        cur1.close()
        conn1.close()
        return render_template('Dashboard.html', cmodel=cmodel, dashboardMsg="Contestant Dashboard")
    
    if globalRoleObject.isElectionCommissioner:
        return render_template('Dashboard.html', dashboardMsg="Election Commissioner Dashboard")
    if globalRoleObject.isElectionOfficer:
        return render_template('Dashboard.html', dashboardMsg="Election Officer Dashboard")
    if globalRoleObject.isPublic:
        return render_template('Dashboard.html', dashboardMsg="Public Dashboard")
    if globalRoleObject.isPolticalParty:
        return render_template('Dashboard.html', dashboardMsg="Political Dashboard")
    if globalRoleObject.isAdmin:
        return render_template('Dashboard.html', dashboardMsg="Admin Dashboard")
    errorResult = "Application Error Occurred"
    errType="Error"
    return redirect(url_for('Error')) 
'''
    Cloud Provider Data Operation Start
'''




@app.route("/RegisterAsVoter")
def RegisterAsVoter():
    global globalUserObject, globalRoleObject
    global errorResult, errType
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
    cur3.commit()
    return render_template('RegisterAsVoter.html', constituencies=constituencies)



@app.route("/ProcessRegisterAsVoter", methods=['POST'])
def ProcessRegisterAsVoter():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    title = request.form["title"]
    firstName = request.form['firstName']
    middleName = request.form['middleName']
    lastName = request.form['lastName']
    wardNumber = request.form['wardNumber']
    streetName = request.form['streetName']
    area = request.form['area']
    city = request.form['city']
    district = request.form['district']
    state = request.form['state']
    dob = request.form['dob']
    nricNumber = request.form['nricNumber']
    mobileNumber = request.form['mobileNumber']
    emailID = request.form['emailID']
    #addressProof = request.files['addressProof']
    #ageProof = request.files['ageProof']
    constituency = request.form['constituency']
    password = request.form['password']
    gender = request.form['gender']
    addressProofFileName = ""
    ageProofFileName = ""
    if len(request.files) != 0 :
        print("HELLO")
        file = request.files['addressProof']
        if file.filename != '':
            addressProofFileName = file.filename
            print(addressProofFileName)
            f = os.path.join('static/UPLOADED_FILES', addressProofFileName)
            file.save(f)
        file = request.files['addressProof']
        if file.filename != '':
            ageProofFileName = file.filename
            f = os.path.join('static/UPLOADED_FILES', ageProofFileName)
            file.save(f)
     
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    
    sqlcmd = "INSERT INTO VoterMaster(title, firstName,middleName,lastName,wardNumber,streetName,area,city,district,state,dob,addressProof, ageProof, ssn,mobileNbr,emailID,constituencyID,isApproved, password, gender) VALUES ('"+title+"', '"+firstName+"','"+middleName+"','"+lastName+"','"+wardNumber+"','"+streetName+"','"+area+"','"+city+"','"+district+"','"+state+"','"+dob+"','"+addressProofFileName+"', '"+ageProofFileName+"', '"+nricNumber+"','"+mobileNumber+"','"+emailID+"','"+constituency+"',0,'"+password+"', '"+gender+"')"
    cur3.execute(sqlcmd)
    cur3.commit()
    sqlcmd = "INSERT INTO UserMaster(userName, emailID,password, roleID) VALUES ('"+firstName+"','"+emailID+"','"+password+"', 1)"
    cur3.execute(sqlcmd)
    cur3.commit()
    globalRoleObject = RoleModel(1, 'Voter Role', True)
    globalUserObject = UserModel(0, emailID, password)
    return redirect(url_for('RegisterAsVoterSuccess')) 
     
     
@app.route("/RegisterAsVoterSuccess")
def RegisterAsVoterSuccess():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    return render_template('RegisterAsVoterSuccess.html')
                           
@app.route("/RegisterAsContestant")
def RegisterAsContestant():
    global globalUserObject, globalRoleObject
    global errorResult, errType
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
    cur3.commit()
    return render_template('RegisterAsContestant.html', constituencies=constituencies)


@app.route("/ProcessRegisterAsContestant", methods=['POST'])
def ProcessRegisterAsContestant():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    title = request.form["title"]
    firstName = request.form['firstName']
    middleName = request.form['middleName']
    lastName = request.form['lastName']
    wardNumber = request.form['wardNumber']
    streetName = request.form['streetName']
    area = request.form['area']
    city = request.form['city']
    district = request.form['district']
    state = request.form['state']
    dob = request.form['dob']
    nricNumber = request.form['nricNumber']
    mobileNumber = request.form['mobileNumber']
    emailID = request.form['emailID']
    #addressProof = request.files['addressProof']
    #ageProof = request.files['ageProof']
    constituency = request.form['constituency']
    password = request.form['password']
    addressProofFileName = ""
    ageProofFileName = ""
    if len(request.files) != 0 :
        print("HELLO")
        file = request.files['addressProof']
        if file.filename != '':
            addressProofFileName = file.filename
            print(addressProofFileName)
            f = os.path.join('static/UPLOADED_FILES/Contestant', addressProofFileName)
            file.save(f)
        file = request.files['addressProof']
        if file.filename != '':
            ageProofFileName = file.filename
            f = os.path.join('static/UPLOADED_FILES/Contestant', ageProofFileName)
            file.save(f)
     
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    
    sqlcmd = "INSERT INTO ContestantMaster(title, firstName,middleName,lastName,wardNumber,streetName,area,city,district,state,dob,addressProof, ageProof, ssn,mobileNbr,emailID,constituencyID,isApproved, password) VALUES ('"+title+"', '"+firstName+"','"+middleName+"','"+lastName+"','"+wardNumber+"','"+streetName+"','"+area+"','"+city+"','"+district+"','"+state+"','"+dob+"','"+addressProofFileName+"', '"+ageProofFileName+"', '"+nricNumber+"','"+mobileNumber+"','"+emailID+"','"+constituency+"',0, '"+password+"')"
    cur3.execute(sqlcmd)
    cur3.commit()
    sqlcmd = "INSERT INTO UserMaster(userName, emailID,password, roleID) VALUES ('"+firstName+"','"+emailID+"','"+password+"', 2)"
    cur3.execute(sqlcmd)
    cur3.commit()
    globalRoleObject = RoleModel(2, 'Constestant Role', False, True)
    return redirect(url_for('RegisterAsContestantSuccess')) 
     
     
@app.route("/RegisterAsContestantSuccess")
def RegisterAsContestantSuccess():
    global globalUserObject, globalRoleObject
    return render_template('RegisterAsContestantSuccess.html')




@app.route("/ApproveVoterListing")
def ApproveVoterListing():
    global globalUserObject, globalRoleObject
    
    initialize()
    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM VoterMaster WHERE IsApproved = 0"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = VoterModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4], dbrow[5], dbrow[6], dbrow[7], dbrow[8], dbrow[9], dbrow[10], dbrow[11], dbrow[12], dbrow[12], dbrow[13], dbrow[14], dbrow[15], dbrow[16], dbrow[17], dbrow[18])
        records.append(row)
    return render_template('ApproveVoterListing.html', records=records)

@app.route("/ApproveVoterOperation")
def ApproveVoterOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = VoterModel(0, "")
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM VoterMaster WHERE voteID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = VoterModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4], dbrow[5], dbrow[6], dbrow[7], dbrow[8], dbrow[9], dbrow[10], dbrow[11], dbrow[12], dbrow[12], dbrow[13], dbrow[14], dbrow[15], dbrow[16], dbrow[17], dbrow[18], dbrow[19])
    
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
        
    return render_template('ApproveVoterOperation.html', row = row, operation=operation, constituencies=constituencies )


@app.route("/ProcessApproveVoterOperation", methods=['POST'])
def ProcessApproveVoterOperation():
    
    global globalUserObject, globalRoleObject
    
    initialize()
    print("ProcessApproveVoter")
    
    unqid = request.form['unqid'].strip()
    isApproved = 0
    if request.form.get("isApproved") != None :
        isApproved = 1
    
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()

    sqlcmd = "UPDATE VoterMaster SET isApproved = '"+str(isApproved)+"', userID = '"+str(globalUserObject.userID)+"' WHERE voteID = '"+unqid+"'" 
    cur3.execute(sqlcmd)
    cur3.commit()
    return redirect(url_for('ApproveVoterListing')) 






@app.route("/ApproveContestantListing")
def ApproveContestantListing():
    global globalUserObject, globalRoleObject
    
    initialize()
    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM ContestantMaster WHERE IsApproved = 0"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = ContestantModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4], dbrow[5], dbrow[6], dbrow[7], dbrow[8], dbrow[9], dbrow[10], dbrow[11], dbrow[12], dbrow[12], dbrow[13], dbrow[14], dbrow[15], dbrow[16], dbrow[17], dbrow[18])
        records.append(row)
    return render_template('ApproveContestantListing.html', records=records)

@app.route("/ApproveContestantOperation")
def ApproveContestantOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = ContestantModel(0, "")
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM ContestantMaster WHERE contestantID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = ContestantModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4], dbrow[5], dbrow[6], dbrow[7], dbrow[8], dbrow[9], dbrow[10], dbrow[11], dbrow[12], dbrow[12], dbrow[13], dbrow[14], dbrow[15], dbrow[16], dbrow[17], dbrow[18])
    
    
        
    return render_template('ApproveContestantOperation.html', row = row, operation=operation)


@app.route("/ProcessApproveContestantOperation", methods=['POST'])
def ProcessApproveContestantOperation():
    
    global globalUserObject, globalRoleObject
    
    initialize()
    print("ProcessApproveContestant")
    
    unqid = request.form['unqid'].strip()
    isApproved = 0
    if request.form.get("isApproved") != None :
        isApproved = 1
    
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()

    sqlcmd = "UPDATE ContestantMaster SET isApproved = '"+str(isApproved)+"', userID = '"+str(globalUserObject.userID)+"' WHERE contestantID = '"+unqid+"'" 
    cur3.execute(sqlcmd)
    cur3.commit()
    return redirect(url_for('ApproveContestantListing')) 




@app.route("/PoliticalPartyListing")
def PoliticalPartyListing():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM PoliticalPartyMaster WHERE PoliticalPartyName LIKE '"+searchData+"%'"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = PoliticalPartyModel(dbrow[0], dbrow[1])
        records.append(row)
    return render_template('PoliticalPartyListing.html', records=records, searchData=searchData)

@app.route("/PoliticalPartyOperation")
def PoliticalPartyOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = PoliticalPartyModel(0, "")
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM PoliticalPartyMaster WHERE politicalPartyID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = PoliticalPartyModel(dbrow[0], dbrow[1])
    return render_template('PoliticalPartyOperation.html', row = row, operation=operation )


@app.route("/ProcessPoliticalPartyOperation", methods=['POST'])
def ProcessPoliticalPartyOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    initialize()
    print("ProcessPoliticalParty")
    politicalPartyName = request.form['politicalPartyName']
    operation = request.form['operation']
    unqid = request.form['unqid'].strip()
    print(operation)
    print("unqid>>>>>>>>>>>>>>>>>>>>>>>>.." , unqid)
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    sqlcmd = ""
    if operation == "Create" :
        sqlcmd = "INSERT INTO PoliticalPartyMaster (PoliticalPartyName) VALUES ('"+politicalPartyName+"')"
        
    if operation == "Edit" :
        sqlcmd = "UPDATE PoliticalPartyMaster SET politicalPartyName = '"+politicalPartyName+"' WHERE politicalPartyID = '"+unqid+"'" 
    if operation == "Delete" :
        sqlcmd = "DELETE FROM PoliticalPartyMaster WHERE politicalPartyID = '"+unqid+"'" 
    print(operation, sqlcmd)
    if sqlcmd == "" :
        return redirect(url_for('Error')) 
    cur3.execute(sqlcmd)
    cur3.commit()
    return redirect(url_for('PoliticalPartyListing'))






@app.route("/ConstituencyListing")
def ConstituencyListing():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM ConstituencyMaster WHERE ConstituencyName LIKE '"+searchData+"%'"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = ConstituencyModel(dbrow[0], dbrow[1], dbrow[2])
        records.append(row)
    return render_template('ConstituencyListing.html', records=records, searchData=searchData)

@app.route("/ConstituencyOperation")
def ConstituencyOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    ConstituencyModel
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = ConstituencyModel(0, "")
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM ConstituencyMaster WHERE ConstituencyID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = ConstituencyModel(dbrow[0], dbrow[1], dbrow[2])
    return render_template('ConstituencyOperation.html', row = row, operation=operation )


@app.route("/ProcessConstituencyOperation", methods=['POST'])
def ProcessConstituencyOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    initialize()
    print("ProcessConstituency")
    constituencyName = request.form['constituencyName']
    state = request.form['state']
    operation = request.form['operation']
    unqid = request.form['unqid'].strip()
    print(operation)
    print("unqid>>>>>>>>>>>>>>>>>>>>>>>>.." , unqid)
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    sqlcmd = ""
    if operation == "Create" :
        sqlcmd = "INSERT INTO ConstituencyMaster (constituencyName, state, userID) VALUES ('"+constituencyName+"', '"+state+"', '"+str(globalUserObject.userID)+"')"
        
    if operation == "Edit" :
        sqlcmd = "UPDATE ConstituencyMaster SET constituencyName = '"+constituencyName+"', state = '"+state+"', userID = '"+str(globalUserObject.userID)+"'  WHERE constituencyID = '"+unqid+"'" 
    if operation == "Delete" :
        sqlcmd = "DELETE FROM ConstituencyMaster WHERE constituencyID = '"+unqid+"'" 
    cur3.execute(sqlcmd)
    cur3.commit()
    return redirect(url_for('ConstituencyListing')) 








@app.route("/ElectionListing")
def ElectionListing():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM ElectionDetails WHERE electionName LIKE '"+searchData+"%'"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = ElectionModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3])
        records.append(row)
    return render_template('ElectionListing.html', records=records, searchData=searchData)

@app.route("/ElectionOperation")
def ElectionOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    ElectionModel
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = ElectionModel(0, "")
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM ElectionDetails WHERE electionID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = ElectionModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3])
    return render_template('ElectionOperation.html', row = row, operation=operation )


@app.route("/ProcessElectionOperation", methods=['POST'])
def ProcessElectionOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    initialize()
    print("ProcessElection")
    electionName = request.form['electionName']
    nominationLastDate = request.form['nominationLastDate']
    effDate = request.form['effDate']
    operation = request.form['operation']
    unqid = request.form['unqid'].strip()
    print(operation)
    print("unqid>>>>>>>>>>>>>>>>>>>>>>>>.." , unqid)
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    sqlcmd = ""
    if operation == "Create" :
        sqlcmd = "INSERT INTO ElectionDetails (electionName, nominationLastDate, effDate, userID) VALUES ('"+electionName+"', '"+nominationLastDate+"', '"+effDate+"', '"+str(globalUserObject.userID)+"')"
        
    if operation == "Edit" :
        sqlcmd = "UPDATE ElectionDetails SET electionName = '"+electionName+"', nominationLastDate = '"+nominationLastDate+"', effDate = '"+effDate+"', userID = '"+str(globalUserObject.userID)+"'  WHERE electionID = '"+unqid+"'" 
    if operation == "Delete" :
        sqlcmd = "DELETE FROM ElectionDetails WHERE electionID = '"+unqid+"'" 
    cur3.execute(sqlcmd)
    cur3.commit()
    return redirect(url_for('ElectionListing')) 






@app.route("/ElectionNominationListing")
def ElectionNominationListing():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    contestantModel = ContestantModel.getContestantNameByEmailID(globalUserObject.emailID)
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = """SELECT * FROM ElectionDetails WHERE NOT EXISTS 
                    (SELECT electionID FROM ContestantElectionDetails 
                    WHERE ElectionDetails.electionID =  ContestantElectionDetails.electionID AND contestantID = '"""+str(contestantModel.contestantID)+"""') 
                    AND nominationLastDate >= '"""+str(date.today())+"' "
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        row = ElectionModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3])
        records.append(row)
        
        
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor3 = conn3.cursor()
    sqlcmd3 = """SELECT * FROM ContestantElectionDetails WHERE EXISTS 
                    (SELECT electionID FROM ElectionDetails 
                    WHERE ElectionDetails.electionID =  ContestantElectionDetails.electionID 
                    AND nominationLastDate >= '"""+str(date.today())+"') AND contestantID = '"+str(contestantModel.contestantID)+"'" 
    print(sqlcmd3)
    cursor3.execute(sqlcmd3)
    cerecords = []
    
    while True:
        dbrow3 = cursor3.fetchone()
        if not dbrow3:
            break
        contestantObject = ContestantModel.getContestantNameByID(dbrow3[1])
        politicalPartyObject = PoliticalPartyModel.getPoliticalPartyByID(dbrow3[2])
        electionObject = ElectionModel.getElectionNameByID(dbrow3[3])
        constituencyObject = ConstituencyModel.getConstituencyNameByID(dbrow3[4])
        print("contestantObject.firstName>>>>>>>>>>>>>>>>",contestantObject.firstName)
        cerow = ElectionNominationModel(dbrow3[0], contestantID = dbrow3[1], contestantModel = contestantObject,  politicalPartyID=dbrow3[2], politicalPartyModel=politicalPartyObject,  electionID=dbrow3[3], electionModel=electionObject, constituencyID=dbrow3[4], constituencyModel = constituencyObject)
        cerecords.append(cerow)
        
    
    return render_template('ElectionNominationListing.html', records=records, cerecords=cerecords)

@app.route("/ElectionNominationOperation")
def ElectionNominationOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    initialize()
    operation = request.args.get('operation')
    if operation == "File":
        electionID = request.args.get('electionID')
        print("electionID", electionID)
        electionObject = ElectionModel.getElectionNameByID(electionID)
        constituencies = ConstituencyModel.getAllConstituenciesIDName()
        politicalpartiesList = PoliticalPartyModel.getAllPolicalPartiesIDName()
        return render_template('ElectionNominationOperation.html', electionObject=electionObject, operation=operation, constituencies=constituencies,politicalpartiesList=politicalpartiesList )
    if operation == "Withdraw":
        print("withDraw<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        uniqueID = request.args.get('uniqueID')
        print("uniqueID<<<<<<<<<<<<<<<<<<<<<<<<<<<<<",uniqueID)
        electionNominationObject = ElectionNominationModel.ElectionNominationgetElectionByID(uniqueID)
        print("electionNominationObject>>>>>>>>>>>>>>>>>>>>>>>>>",electionNominationObject.electionID)
       
        return render_template('ElectionNominationOperationWithdraw.html', uniqueID = uniqueID, operation=operation, electionNominationObject=electionNominationObject )

@app.route("/ProcessElectionNominationOperation", methods=['POST'])
def ProcessElectionNominationOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    initialize()
    operation = request.form['operation']
    
    if operation == "File":
        electionID = request.form['electionID']
        constituencyID = request.form['constituencyID']
        politicalPartyID = request.form['politicalPartyID']
        contestantID = ContestantModel.getContestantNameByEmailID(globalUserObject.emailID).contestantID
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        sqlcmd = "INSERT INTO ContestantElectionDetails (contestantID,  politicalPartyID, electionID, constituencyID) VALUES ('"+str(contestantID)+"', '"+str(politicalPartyID)+"', '"+str(electionID)+"', '"+str(constituencyID)+"')" 
        print("VVVVVVVVVVVVVVVVVVVVVVVVVV", sqlcmd)
        cur3.execute(sqlcmd)
        cur3.commit()
    if operation == "Withdraw":
        uniqueID = request.form['uniqueID']
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cur3 = conn3.cursor()
        sqlcmd = "DELETE  FROM ContestantElectionDetails WHERE UniqueID = '"+str(uniqueID)+"'"
        print("Delete", sqlcmd)
        cur3.execute(sqlcmd)
        cur3.commit()
    return redirect(url_for('ElectionNominationListing')) 





@app.route("/CastMyVoteListing")
def CastMyVoteListing():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    
    voterObject = VoterModel.getVoterByEmailID(globalUserObject.emailID)
        
        
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor3 = conn3.cursor()
    sqlcmd3 = """SELECT DISTINCT electionID, constituencyID FROM ContestantElectionDetails WHERE EXISTS 
                    (SELECT electionID FROM ElectionDetails 
                    WHERE ElectionDetails.electionID =  ContestantElectionDetails.electionID 
                    AND effDate = '"""+str(date.today())+"""')
                    AND NOT EXISTS (SELECT electionID FROM VoteCastDetails WHERE VoteCastDetails.electionID = ContestantElectionDetails.electionID and 
                    VoteCastDetails.constituencyID = ContestantElectionDetails.constituencyID and VoteCastDetails.voterID = '"""+str(voterObject.voteID)+"""')
                    AND EXISTS (SELECT constituencyID FROM VoterMaster WHERE  
                    VoterMaster.constituencyID = ContestantElectionDetails.constituencyID 
                    AND emailID = '"""+globalUserObject.emailID+"')"
    print(sqlcmd3)
    cursor3.execute(sqlcmd3)
    cerecords = []
    
    while True:
        dbrow3 = cursor3.fetchone()
        if not dbrow3:
            break
        
        electionObject = ElectionModel.getElectionNameByID(dbrow3[0])
        constituencyObject = ConstituencyModel.getConstituencyNameByID(dbrow3[1])
        
        cerow = ElectionNominationModel( electionID=dbrow3[0], electionModel=electionObject, constituencyID=dbrow3[1], constituencyModel = constituencyObject)
        cerecords.append(cerow)
        
    
    return render_template('CastMyVoteListing.html', cerecords=cerecords)

@app.route("/CastMyVoteOperation")
def CastMyVoteOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType
    
    initialize()
    electionID = request.args.get('electionID')
    constituencyID = request.args.get('constituencyID')
    
    electionObject = ElectionModel.getElectionNameByID(electionID)
    constituencyObject = ConstituencyModel.getConstituencyNameByID(constituencyID)
    
    contestantsList = ElectionNominationModel.getAllContestantByElectionByConstituency(electionID, constituencyID)
    print(len(contestantsList),"KKKKKKKKKKKKKKKKKKKKKKKKKKKK")
    
    return render_template('CastMyVoteOperation.html', electionObject=electionObject, constituencyObject=constituencyObject, contestantsList=contestantsList)
    
@app.route("/ProcessCastMyVoteOperation", methods=['POST'])
def ProcessCastMyVoteOperation():
    global globalUserObject, globalRoleObject
    global errorResult, errType

    initialize()
   
    

    electionID = request.form['electionID']
    constituencyID = request.form['constituencyID']
    contestantID = request.form['contestantID']
    voterObject = VoterModel.getVoterByEmailID(globalUserObject.emailID)
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()
    sqlcmd = "INSERT INTO VoteCastDetails (contestantID,  voterID, electionID, constituencyID) VALUES ('"+str(contestantID)+"', '"+str(voterObject.voteID)+"', '"+str(electionID)+"', '"+str(constituencyID)+"')" 
    cur3.execute(sqlcmd)
    cur3.commit()
    
    return redirect(url_for('CastMyVoteListing')) 







@app.route("/VoteOperation")
def VoteOperation():
    
    global errorResult, errType

    userID=""
    print(1)
    initialize()
    
    
    row = PoliticalPartyModel(0, "")

    conn2 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM VoteData WHERE userID = '"+str(userID)+"'"
    cursor.execute(sqlcmd1)
    dbrow = cursor.fetchone()
    if dbrow:
        return render_template('VoteDone.html')
    
    print(2)
    sqlcmd1 = "SELECT * FROM PoliticalData ORDER BY politicalPartyName"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    print(3)
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
      
        
        records.append(row)
    return render_template('VoteOperation.html', records = records)


@app.route("/ProcessVoteOperation", methods=['POST'])
def ProcessVoteOperation():
    
    global errorResult, errType
    userID=""
  
    
    
    initialize()
    print("ProcessVote")
    politicalPartyID = request.form['politicalPartyID']
    
    

    conn3 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
    cur3 = conn3.cursor()

    sqlcmd = "INSERT INTO VoteData (politicalPartyID, userID) VALUES ('"+str(politicalPartyID)+"', '"+str(userID)+"')"
 
    cur3.execute(sqlcmd)
    cur3.commit()
    
    return render_template('VoteResult.html')
    



'''
    Role Operation Start
'''

@app.route("/RoleListing")
def RoleListing():
    
   
    
    initialize()
    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn2 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT * FROM Role WHERE roleName LIKE '"+searchData+"%'"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        print(dbrow[0],dbrow[1],dbrow[2],dbrow[3],dbrow[4],dbrow[5],dbrow[6],dbrow[7])
        row = RoleModel(dbrow[0],dbrow[1],dbrow[2],dbrow[3],dbrow[4],dbrow[5],dbrow[6],dbrow[7])
        
        records.append(row)
    
    return render_template('RoleListing.html', records=records, searchData=searchData)

@app.route("/RoleOperation")
def RoleOperation():
    
   
    
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = RoleModel(0, "",0,0,0,0,0,0)
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        
        
        conn2 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM Role WHERE RoleID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            row = RoleModel(dbrow[0],dbrow[1],dbrow[2],dbrow[3],dbrow[4],dbrow[5],dbrow[6],dbrow[7])
        
    return render_template('RoleOperation.html', row = row, operation=operation )


@app.route("/ProcessRoleOperation", methods=['POST'])
def ProcessRoleOperation():
    global errorResult, errType
    
    
    initialize()
    print("ProcessRole")
    
    operation = request.form['operation']
    if operation != "Delete" :
        RoleName = request.form['RoleName']
    
    print(1)
    unqid = request.form['unqid'].strip()
    print(operation)
    conn3 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
    cur3 = conn3.cursor()
    
    CanPoliticalParty = 0
    CanVote = 0
    CanBlockChainReport = 0
    CanBlockChainGeneration = 0
    CanRole = 0
    CanUser = 0
    print(2)
    print("request.form.get('CanPoliticalParty')----------------------------------------------------", request.form.get("CanPoliticalParty"))
    if request.form.get("CanPoliticalParty") != None :
        CanPoliticalParty = 1
    if request.form.get("CanVote") != None :
        CanVote = 1
    if request.form.get("CanBlockChainReport") != None :
        CanBlockChainReport = 1
    if request.form.get("CanBlockChainGeneration") != None :
        CanBlockChainGeneration = 1
    if request.form.get("CanRole") != None :
        CanRole = 1
    if request.form.get("CanUser") != None :
        CanUser = 1
    sqlcmd = ""
    if operation == "Create" :
        sqlcmd = "INSERT INTO Role (RoleName, CanPoliticalParty, CanVote, CanBlockchainGeneration, CanBlockchainReport, CanRole, CanUser) VALUES ('"+RoleName+"', '"+str(CanPoliticalParty)+"', '"+str(CanVote)+"', '"+str(CanBlockChainGeneration)+"', '"+str(CanBlockChainReport)+"', '"+str(CanRole)+"', '"+str(CanUser)+"')"
    if operation == "Edit" :
        print("edit inside")
        sqlcmd = "UPDATE Role SET RoleName = '"+RoleName+"', CanPoliticalParty = '"+str(CanPoliticalParty)+"', CanVote = '"+str(CanVote)+"', CanBlockChainGeneration = '"+str(CanBlockChainGeneration)+"', canBlockChainReport = '"+str(CanBlockChainReport)+"', canRole = '"+str(CanRole)+"', canUser = '"+str(CanUser)+"' WHERE RoleID = '"+unqid+"'" 
    if operation == "Delete" :
        conn4 = pypyodbc.connect('Driver={SQL Server};Server=COMPUTER-PC\WISEN123;Integrated_Security=true;Database=E-Voting', autocommit=True)
        cur4 = conn4.cursor()
        sqlcmd4 = "SELECT RoleID FROM Users WHERE RoleID = '"+unqid+"'" 
        dbrow4 = cur4.fetchone()
        if dbrow4:
            errorResult = "You Can't Delete this Role Since it Available in Users Table"
            errType="Error"
            return redirect(url_for('Error')) 
        
        sqlcmd = "DELETE FROM Role WHERE RoleID = '"+unqid+"'" 
    print(operation, sqlcmd)
    if sqlcmd == "" :
        return redirect(url_for('Error')) 
    cur3.execute(sqlcmd)
    cur3.commit()
    
    return redirect(url_for('RoleListing')) 
    #return render_template('RoleListing.html',  msg="Cloud Provider Information Successfully Created")



'''
    Role Operation End
'''













'''
    Users Operation Start
'''

@app.route("/UserListing")
def UserListing():
    global globalUserObject, globalRoleObject
       
        
    initialize()
    searchData = request.args.get('searchData')
    print(searchData)
    if searchData == None:
        searchData = "";
    conn = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn.cursor()
    sqlcmd1 = "SELECT * FROM UserMaster WHERE UserName LIKE '"+searchData+"%'"
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        
        conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor3 = conn3.cursor()
        temp = str(dbrow[4])
        sqlcmd3 = "SELECT * FROM RoleMaster WHERE RoleID = '"+temp+"'"
        cursor3.execute(sqlcmd3)
        rolerow = cursor3.fetchone()
        roleObj = RoleModel(0)
        if rolerow:
           roleObj = RoleModel(rolerow[0],rolerow[1])
        else:
           print("Role Row is Not Available")
        print()
        row = UserModel(dbrow[0],dbrow[1],dbrow[2],dbrow[3],dbrow[4],roleModel=roleObj)
        print(row.roleModel.roleName)
        records.append(row)
    cursor.close()
    conn.close()
    return render_template('UserListing.html', records=records, searchData=searchData)

@app.route("/UserOperation")
def UserOperation():  
    global globalUserObject, globalRoleObject
    initialize()
    operation = request.args.get('operation')
    unqid = ""
    row = UserModel(0)
    rolesDDList = []
    
    conn4 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor4 = conn4.cursor()
    sqlcmd4 = "SELECT * FROM RoleMaster"
    cursor4.execute(sqlcmd4)
    while True:
        roleDDrow = cursor4.fetchone()
        if not roleDDrow:
            break
        roleDDObj = RoleModel(roleDDrow[0], roleDDrow[1])
        rolesDDList.append(roleDDObj)
    
    if operation != "Create" :
        unqid = request.args.get('unqid').strip()
        conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor = conn2.cursor()
        sqlcmd1 = "SELECT * FROM UserMaster WHERE userID = '"+unqid+"'"
        cursor.execute(sqlcmd1)
        while True:
            dbrow = cursor.fetchone()
            if not dbrow:
                break
            conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
            cursor3 = conn3.cursor()
            print("dbrow[4]", dbrow[4])
            temp = str(dbrow[4])
            sqlcmd3 = "SELECT * FROM RoleMaster WHERE RoleID = '"+temp+"'"
            cursor3.execute(sqlcmd3)
            rolerow = cursor3.fetchone()
            roleObj = None
            if rolerow:
                roleObj = RoleModel(rolerow[0], rolerow[1])
           
            row = UserModel(dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4], roleModel=roleObj)
            
        
    return render_template('UserOperation.html', row = row, operation=operation, rolesDDList=rolesDDList )


@app.route("/ProcessUserOperation", methods=['POST'])
def ProcessUserOperation():
    
   
    
    initialize()
    print("ProcessUserOperation")
    operation = request.form['operation']
    
    if operation != "Delete" :
        userName = request.form['userName']
        emailID = request.form['emailID']
        password = request.form['password']
        roleID = request.form['roleID']
        
    
    unqid = request.form['unqid'].strip()
    print(operation)
    conn3 = pypyodbc.connect(Constants.connString, autocommit=True)
    cur3 = conn3.cursor()

    if operation == "Create" :
        sqlcmd = "INSERT INTO UserMaster (userName, emailID, password, roleID) VALUES ('"+userName+"', '"+emailID+"', '"+password+"', '"+roleID+"')"
    if operation == "Edit" :
        print("edit inside")
        sqlcmd = "UPDATE UserMaster SET UserName = '"+userName+"', emailID = '"+emailID+"', password = '"+password+"', roleID = '"+roleID+"' WHERE userID = '"+unqid+"'" 
    if operation == "Delete" :
        sqlcmd = "DELETE FROM UserMaster WHERE UserID = '"+unqid+"'" 
    print(operation, sqlcmd)
    if sqlcmd == "" :
        return redirect(url_for('Error')) 
    cur3.execute(sqlcmd)
    cur3.commit()
    
    return redirect(url_for('UserListing')) 
    #return render_template('UserListing.html',  msg="Cloud Provider Information Successfully Created")



'''
    Users Operation End
'''





'''
    Video Data Operation Start
'''





    
@app.route("/BlockChainGeneration")
def BlockChainGeneration():
    
    initialize()
    conn = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn.cursor()
    sqlcmd = "SELECT COUNT(*) FROM VoteCastDetails WHERE isBlockChainGenerated = 1"
    cursor.execute(sqlcmd)
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        blocksCreated = dbrow[0]
    
    sqlcmd = "SELECT COUNT(*) FROM VoteCastDetails WHERE isBlockChainGenerated = 0 or isBlockChainGenerated is null"
    cursor.execute(sqlcmd)
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        blocksNotCreated = dbrow[0]
    return render_template('BlockChainGeneration.html', blocksCreated = blocksCreated, blocksNotCreated = blocksNotCreated)




@app.route("/ProcessBlockchainGeneration", methods=['POST'])
def ProcessBlockchainGeneration():
    initialize()
    conn = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn.cursor()
    sqlcmd = "SELECT COUNT(*) FROM VoteCastDetails WHERE isBlockChainGenerated = 1"
    cursor.execute(sqlcmd)
    blocksCreated = 0
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        blocksCreated = dbrow[0]
    
    prevHash = ""
    print("blocksCreated", blocksCreated)
    if blocksCreated != 0 :
        connx = pypyodbc.connect(Constants.connString, autocommit=True)
        cursorx = connx.cursor()
        sqlcmdx = "SELECT * FROM VoteCastDetails WHERE isBlockChainGenerated = 0 or isBlockChainGenerated is null ORDER BY uniqueID"
        cursorx.execute(sqlcmdx)
        dbrowx = cursorx.fetchone()
        print(2)
        if dbrowx:
            voteID = dbrowx[0]
            conny = pypyodbc.connect(Constants.connString, autocommit=True)
            cursory = conny.cursor()
            sqlcmdy = "SELECT Hash FROM VoteCastDetails WHERE voterID < '"+str(voteID)+"' ORDER BY uniqueID DESC"
            cursory.execute(sqlcmdy)
            dbrowy = cursory.fetchone()
            if dbrowy:
                print(3)
                prevHash = dbrowy[0]
                print("prevHash1111", prevHash)
            cursory.close()
            conny.close()
        cursorx.close()
        connx.close()
    conn = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn.cursor()
    sqlcmd = "SELECT * FROM VoteCastDetails WHERE isBlockChainGenerated = 0 or isBlockChainGenerated is null ORDER BY uniqueID"
    cursor.execute(sqlcmd)
    
    while True:
        sqlcmd1 = ""
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        unqid = str(dbrow[0])
        
        block_serialized = json.dumps(str(dbrow[1])+" "+str(dbrow[2]), sort_keys=True).encode('utf-8')
        block_hash = hashlib.sha256(block_serialized).hexdigest()
  
        conn1 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor1 = conn1.cursor()
        sqlcmd1 = "UPDATE VoteCastDetails SET isBlockChainGenerated = 1, hash = '"+block_hash+"', prevHash = '"+prevHash+"' WHERE uniqueID = '"+unqid+"'"
        cursor1.execute(sqlcmd1)
        cursor1.close()
        conn1.close()
        prevHash = block_hash
    return render_template('BlockchainGenerationResult.html')

from VoterCastModel import VoterCastModel
@app.route("/BlockChainReport")
def BlockChainReport():
    

    
        
    initialize()
    conn = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn.cursor()
    
    sqlcmd1 = "SELECT * FROM VoteCastDetails WHERE isBlockChainGenerated = 1"
    cursor.execute(sqlcmd1)
    records = VoterCastModel.getAllVoterCast()
    

    return render_template('BlockChainReport.html', records=records)


@app.route("/AnalysisVoterGenderWiseReport")
def AnalysisVoterGenderWiseReport():
    initialize()
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT gender, Count(*) FROm VoterMaster GROUP BY gender ORDER BY gender"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        records.append([dbrow[0], dbrow[1]])
    
    return render_template('AnalysisVoterGenderWiseReport.html', records=records)

@app.route("/DownloadConstituencyVoterList")
def DownloadConstituencyVoterList():
    initialize()
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = "SELECT constituencyName, firstName, middleName, lastName, gender FROM VoterMaster INNER JOIN ConstituencyMaster ON ConstituencyMaster.constituencyID = VoterMaster.constituencyID ORDER BY constituencyName"
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
                
        records.append([dbrow[0], dbrow[1], dbrow[2], dbrow[3], dbrow[4]])
    
    return render_template('DownloadConstituencyVoterList.html', records=records)

@app.route("/DownloadConstituencyElectionResult")
def DownloadConstituencyElectionResult():
    initialize()
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = """SELECT electionName, constituencyName, firstName, COUNT(*) FROM VoteCastDetails 
                    INNER JOIN ElectionDetails ON ElectionDetails.electionID = VoteCastDetails.electionID
                    INNER JOIN ConstituencyMaster ON ConstituencyMaster.constituencyID = VoteCastDetails.constituencyID
                    INNER JOIN ContestantMaster ON ContestantMaster.contestantID = VoteCastDetails.contestantID
                    GROUP BY electionName, constituencyName, firstName
                """
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        records.append([dbrow[0], dbrow[1], dbrow[2], dbrow[3]])
    
    return render_template('DownloadConstituencyElectionResult.html', records=records)


@app.route("/AnalysisElectionResultAgewiseReport")
def AnalysisElectionResultAgewiseReport():
    initialize()
    conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
    cursor = conn2.cursor()
    sqlcmd1 = """SELECT DATEDIFF(YY, dob, GETDATE()) as Age, COUNT(*) FROM VoteCastDetails 
                    INNER JOIN VoterMaster ON VoterMaster.voteID = VoteCastDetails.voterID
                    GROUP BY DATEDIFF(YY, dob, GETDATE()) ORDER BY DATEDIFF(YY, dob, GETDATE())
                    """
    print(sqlcmd1)
    cursor.execute(sqlcmd1)
    records = []
    
    while True:
        dbrow = cursor.fetchone()
        if not dbrow:
            break
        records.append([dbrow[0], dbrow[1]])
    return render_template('AnalysisElectionResultAgewiseReport.html', records=records)


@app.route("/ElectionResultPoliticalPartyWise")
def ElectionResultPoliticalPartyWise():
    initialize()
    elections = ElectionModel.getAllElection()
    electionID = request.args.get('electionID')
    ppwise = {}
    if electionID != None:
        conn1 = pypyodbc.connect(Constants.connString, autocommit=True)
        cursor1 = conn1.cursor()
        sqlcmd1 = """SELECT DISTINCT constituencyID FROM ContestantElectionDetails 
                    WHERE electionID = '"""+str(electionID)+"""' 
                        """
        print(sqlcmd1)
        cursor1.execute(sqlcmd1)
        
        while True:
           
            dbrow1 = cursor1.fetchone()
            if not dbrow1:
                break
            
            conn2 = pypyodbc.connect(Constants.connString, autocommit=True)
            cursor2 = conn2.cursor()
            sqlcmd2 = """SELECT contestantID, COUNT(*) FROM VoteCastDetails 
                        WHERE electionID = '"""+str(electionID)+"""' 
                        AND constituencyID = '"""+str(dbrow1[0])+"""'
                        GROUP BY contestantID
                        ORDER BY COUNT(*) DESC
                            """
            print(sqlcmd2)
            cursor2.execute(sqlcmd2)
            winnerContestantID = 0
            isFirst = True
            firstVotes = 0
            isSecond = False
            secondVotes = 0
            while True:
                
                dbrow2 = cursor2.fetchone()
                if not dbrow2:
                    
                    if isSecond == True:
                        politicalPartyName = ElectionNominationModel.getPoliticalPartyNameByElectionByConstituencyByContestantID(electionID, dbrow1[0], winnerContestantID)
                        if politicalPartyName in ppwise:
                            ppwise[politicalPartyName] = ppwise[politicalPartyName] + 1
                        else:
                            ppwise[politicalPartyName] = 1
                    break
                
                if isSecond:
                    secondVotes = dbrow2[1]
                    isSecond = False
                    
                    if firstVotes > secondVotes:
                        politicalPartyName = ElectionNominationModel.getPoliticalPartyNameByElectionByConstituencyByContestantID(electionID, dbrow1[0], winnerContestantID)
                        print(politicalPartyName, "politicalPartyName>>>>>>>>>>>>>>>>>>>>>")
                        if politicalPartyName in ppwise:
                            ppwise[politicalPartyName] = ppwise[politicalPartyName] + 1
                        else:
                            ppwise[politicalPartyName] = 1
                        
                        break
                if isFirst:
                    winnerContestantID = dbrow2[0]
                    firstVotes = dbrow2[1]
                    isFirst = False
                    isSecond = True
                    
        print(ppwise, len(ppwise))
    return render_template('ElectionResultPoliticalPartyWiseReport.html', ppwise=ppwise, elections=elections, electionID=electionID)


if __name__=='__main__':
    app.run()
    


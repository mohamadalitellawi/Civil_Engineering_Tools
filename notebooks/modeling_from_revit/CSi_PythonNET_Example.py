import os
import sys
import clr

from enum import Enum

clr.AddReference("System.Runtime.InteropServices")
from System.Runtime.InteropServices import Marshal

# set the following path to the installedSAP2000 program directory
clr.AddReference(R"C:\Program Files\Computersand Structures\SAP2000 24\SAP2000v1.dll")
from SAP2000v1 import *

# set the following flag to True to executeon a remote computer
Remote = False

# if the above flag is True, set the followingvariable to the hostname of the remote computer
# remember that the remote computer musthave SAP2000 installed and be running the CSiAPIService.exe
RemoteComputer = "SpareComputer-DT"

# set the following flag to True to attachto an existing instance of the program
# otherwise a new instance of the programwill be started
AttachToInstance = False

# set the following flag to True to manuallyspecify the path to SAP2000.exe
# this allows for a connection to a versionof SAP2000 other than the latest installation
# otherwise the latest installed versionof SAP2000 will be launched
SpecifyPath = False

# if the above flag is set to True, specifythe path to SAP2000 below
ProgramPath = r"C:\Program Files\Computersand Structures\SAP2000 24\SAP2000.exe"

# full path to the model
# set it to the desired path of your model
# if executing remotely, ensure that thisfolder already exists on the remote computer
# the below command will only create thefolder locally

APIPath = r"C:\CSi_SAP2000_API_Example"
if not os.path.exists(APIPath):
    try:
        os.makedirs(APIPath)
    except OSError:
        pass
ModelPath = APIPath + os.sep + "API_1-001.sdb"

# create API helper object
helper = cHelper(Helper())

if AttachToInstance:
    # attach to a runninginstance of SAP2000
    try:
        # get the active SAP2000 object
        if Remote:
            mySAPObject = cOAPI(
                helper.GetObjectHost(RemoteComputer, "CSI.SAP2000.API.SAPObject")
            )
        else:
            mySAPObject = cOAPI(helper.GetObject("CSI.SAP2000.API.SAPObject"))
    except:
        print("Norunning instance of the program found or failed to attach.")
        sys.exit(-1)

else:
    if SpecifyPath:
        try:
            #'createan instance of the SAP2000 object from the specified path
            if Remote:
                mySAPObject = cOAPI(
                    helper.CreateObjectHost(RemoteComputer, ProgramPath)
                )
            else:
                mySAPObject = cOAPI(helper.CreateObject(ProgramPath))
        except:
            print("Cannotstart a new instance of the program from " + ProgramPath)
            sys.exit(-1)
    else:
        try:
            # create an instance of the SAP2000 object from the latest installed SAP2000
            if Remote:
                mySAPObject = cOAPI(
                    helper.CreateObjectProgIDHost(
                        RemoteComputer, "CSI.SAP2000.API.SAPObject"
                    )
                )
            else:
                mySAPObject = cOAPI(
                    helper.CreateObjectProgID("CSI.SAP2000.API.SAPObject")
                )
        except:
            print("Cannotstart a new instance of the program.")
            sys.exit(-1)

    # start SAP2000 application
    mySAPObject.ApplicationStart()

# create SapModel object
SapModel = cSapModel(mySAPObject.SapModel)

# initialize model
SapModel.InitializeNewModel()

# create new blank model
File = cFile(SapModel.File)
ret = File.NewBlank()

# define material property
MATERIAL_CONCRETE = 2
PropMaterial = cPropMaterial(SapModel.PropMaterial)
ret = PropMaterial.SetMaterial("CONC", eMatType(MATERIAL_CONCRETE))

# assign isotropic mechanical propertiesto material
ret = PropMaterial.SetMPIsotropic("CONC", 3600, 0.2, 0.0000055)

# define rectangular frame section property
PropFrame = cPropFrame(SapModel.PropFrame)
ret = PropFrame.SetRectangle("R1", "CONC", 12, 12)

# define frame section property modifiers
ModValue = [1000, 0, 0, 1, 1, 1, 1, 1]
ret = PropFrame.SetModifiers("R1", ModValue)

# switch to k-ft units
kip_ft_F = 4
ret = SapModel.SetPresentUnits(eUnits(kip_ft_F))

# add frame object by coordinates
FrameObj = cFrameObj(SapModel.FrameObj)
FrameName1 = " "
FrameName2 = " "
FrameName3 = " "
[ret, FrameName1] = FrameObj.AddByCoord(
    0, 0, 0, 0, 0, 10, FrameName1, "R1", "1", "Global"
)
[ret, FrameName2] = FrameObj.AddByCoord(
    0, 0, 10, 8, 0, 16, FrameName2, "R1", "2", "Global"
)
[ret, FrameName3] = FrameObj.AddByCoord(
    -4, 0, 10, 0, 0, 10, FrameName3, "R1", "3", "Global"
)

# assign point object restraint at base
PointObj = cPointObj(SapModel.PointObj)
PointName1 = " "
PointName2 = " "
Restraint = [True, True, True, True, False, False]
[ret, PointName1, PointName2] = FrameObj.GetPoints(FrameName1, PointName1, PointName2)
ret = PointObj.SetRestraint(PointName1, Restraint)

# assign point object restraint at top
Restraint = [True, True, False, False, False, False]
[ret, PointName1, PointName2] = FrameObj.GetPoints(FrameName2, PointName1, PointName2)
ret = PointObj.SetRestraint(PointName2, Restraint)

# refresh view, update (initialize) zoom
View = cView(SapModel.View)
ret = View.RefreshView(0, False)

# add load patterns
LTYPE_OTHER = 8
LoadPatterns = cLoadPatterns(SapModel.LoadPatterns)
ret = LoadPatterns.Add("1", eLoadPatternType(LTYPE_OTHER), 1, True)
ret = LoadPatterns.Add("2", eLoadPatternType(LTYPE_OTHER), 0, True)
ret = LoadPatterns.Add("3", eLoadPatternType(LTYPE_OTHER), 0, True)
ret = LoadPatterns.Add("4", eLoadPatternType(LTYPE_OTHER), 0, True)
ret = LoadPatterns.Add("5", eLoadPatternType(LTYPE_OTHER), 0, True)
ret = LoadPatterns.Add("6", eLoadPatternType(LTYPE_OTHER), 0, True)
ret = LoadPatterns.Add("7", eLoadPatternType(LTYPE_OTHER), 0, True)

# assign loading for load pattern 2
[ret, PointName1, PointName2] = FrameObj.GetPoints(FrameName3, PointName1, PointName2)
PointLoadValue = [0, 0, -10, 0, 0, 0]
ret = PointObj.SetLoadForce(PointName1, "2", PointLoadValue)
ret = FrameObj.SetLoadDistributed(FrameName3, "2", 1, 10, 0, 1, 1.8, 1.8)

# assign loading for load pattern 3
[ret, PointName1, PointName2] = FrameObj.GetPoints(FrameName3, PointName1, PointName2)
PointLoadValue = [0, 0, -17.2, 0, -54.4, 0]
ret = PointObj.SetLoadForce(PointName2, "3", PointLoadValue)

# assign loading for load pattern 4
ret = FrameObj.SetLoadDistributed(FrameName2, "4", 1, 11, 0, 1, 2, 2)

# assign loading for load pattern 5
ret = FrameObj.SetLoadDistributed(FrameName1, "5", 1, 2, 0, 1, 2, 2, "Local")
ret = FrameObj.SetLoadDistributed(FrameName2, "5", 1, 2, 0, 1, -2, -2, "Local")

# assign loading for load pattern 6
ret = FrameObj.SetLoadDistributed(FrameName1, "6", 1, 2, 0, 1, 0.9984, 0.3744, "Local")
ret = FrameObj.SetLoadDistributed(FrameName2, "6", 1, 2, 0, 1, -0.3744, 0, "Local")

# assign loading for load pattern 7
ret = FrameObj.SetLoadPoint(FrameName2, "7", 1, 2, 0.5, -15, "Local")

# switch to k-in units
kip_in_F = 3
ret = SapModel.SetPresentUnits(eUnits(kip_in_F))

# save model
File = cFile(SapModel.File)
ret = File.Save(ModelPath)

# run model (this will create the analysismodel)
Analyze = cAnalyze(SapModel.Analyze)
ret = Analyze.RunAnalysis()

# initialize for results
ProgramResult = [0, 0, 0, 0, 0, 0, 0]
[ret, PointName1, PointName2] = FrameObj.GetPoints(FrameName2, PointName1, PointName2)

# get results for load cases 1 through 7
Results = cAnalysisResults(SapModel.Results)
Setup = cAnalysisResultsSetup(Results.Setup)

for i in range(0, 7):
    NumberResults = 0
    Obj = []
    Elm = []
    ACase = []
    StepType = []
    StepNum = []
    U1 = []
    U2 = []
    U3 = []
    R1 = []
    R2 = []
    R3 = []
    ObjectElm = 0
    ret = Setup.DeselectAllCasesAndCombosForOutput()
    ret = Setup.SetCaseSelectedForOutput(str(i + 1))

    if i <= 3:
        [
            ret,
            NumberResults,
            Obj,
            Elm,
            ACase,
            StepType,
            StepNum,
            U1,
            U2,
            U3,
            R1,
            R2,
            R3,
        ] = Results.JointDispl(
            PointName2,
            eItemTypeElm(ObjectElm),
            NumberResults,
            Obj,
            Elm,
            ACase,
            StepType,
            StepNum,
            U1,
            U2,
            U3,
            R1,
            R2,
            R3,
        )
        ProgramResult[i] = U3[0]
    else:
        [
            ret,
            NumberResults,
            Obj,
            Elm,
            ACase,
            StepType,
            StepNum,
            U1,
            U2,
            U3,
            R1,
            R2,
            R3,
        ] = Results.JointDispl(
            PointName1,
            eItemTypeElm(ObjectElm),
            NumberResults,
            Obj,
            Elm,
            ACase,
            StepType,
            StepNum,
            U1,
            U2,
            U3,
            R1,
            R2,
            R3,
        )
        ProgramResult[i] = U1[0]

# close the program
ret = mySAPObject.ApplicationExit(False)
SapModel = None
mySAPObject = None

# fill independent results
IndResult = [0, 0, 0, 0, 0, 0, 0]
IndResult[0] = -0.02639
IndResult[1] = 0.06296
IndResult[2] = 0.06296
IndResult[3] = -0.2963
IndResult[4] = 0.3125
IndResult[5] = 0.11556
IndResult[6] = 0.00651

# fill percent difference

PercentDiff = [0, 0, 0, 0, 0, 0, 0]
for i in range(0, 7):
    PercentDiff[i] = (ProgramResult[i] / IndResult[i]) - 1

# display results
for i in range(0, 7):
    print(ProgramResult[i])
    print(IndResult[i])
    print(PercentDiff[i])

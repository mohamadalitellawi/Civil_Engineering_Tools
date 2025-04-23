import clr
clr.AddReference("System.Runtime.InteropServices")
from System.Runtime.InteropServices import Marshal

#set the following path to the installed SAP2000 program directory
clr.AddReference(R'C:\Program Files\Computers and Structures\SAP2000 26\SAP2000v1.dll')
import SAP2000v1 as sap

#set the following path to the installed ETABS program directory
clr.AddReference(R'C:\Program Files\Computers and Structures\ETABS 22\ETABSv1.dll')
import ETABSv1 as etabs

etabs_units = {
'N_mm_C' : etabs.eUnits.N_mm_C,
'kN_m_C' : etabs.eUnits.kN_m_C,
}

sap_units = {
    'N_mm_C': sap.eUnits.N_mm_C,
    'kN_m_C': sap.eUnits.kN_m_C,
}



class CsiHelper:
    """Manage Csi Models and Objects."""

    _SapModel = None
    _mySapObject = None
    _myETABSObject = None

    @classmethod
    def connect_to_etabs(cls, units = etabs_units['N_mm_C']):
        """
        Connect To Running Etabs Instance.
        check if already connected.
        Args:
            SapModel: Etabs SapModel Object
        
        Returns:
            Etabs SapModel object
        """

        if cls._SapModel is not None:
            if units is not None:
                ret = cls._SapModel.SetPresentUnits(units)
            return cls._SapModel
        
        #create API helper object
        helper = etabs.cHelper(etabs.Helper())

        try:
            myETABSObject = etabs.cOAPI(helper.GetObject("CSI.ETABS.API.ETABSObject"))
            cls._myETABSObject = myETABSObject
        except:
            error_msg = "No running ETABS instance of the program found or failed to attach."
            raise Exception(error_msg)
            

        #create SapModel object
        SapModel = etabs.cSapModel(myETABSObject.SapModel)
        if units is not None:
            ret = SapModel.SetPresentUnits(units)

        cls._SapModel = SapModel
        return cls._SapModel



    @classmethod
    def connect_to_sap(cls, units = sap_units['N_mm_C']):
        """
        Connect To Running SAP2000 Instance.
        check if already connected.
        Args:
            SapModel: SAP2000 SapModel Object
        
        Returns:
            SAP2000 SapModel object
        """

        if cls._SapModel is not None:
            if units is not None:
                ret = cls._SapModel.SetPresentUnits(units)
            cls._SapModel = SapModel
            return cls._SapModel
        
        #create API helper object
        helper = sap.cHelper(sap.Helper())

        try:
            mySapObject = sap.cOAPI(helper.GetObject("CSI.SAP2000.API.SapObject"))
            cls._mySapObject = mySapObject
        except:
            error_msg = "No running SAP2000 instance of the program found or failed to attach."
            raise Exception(error_msg)
            

        #create SapModel object
        SapModel = sap.cSapModel(mySapObject.SapModel)
        if units is not None:
            ret = SapModel.SetPresentUnits(units)

        cls._SapModel = SapModel
        return cls._SapModel
    

    @classmethod
    def refresh_view(cls):
        """
        refresh ETABS/SAP2000 view.
        """
        if cls._SapModel:
            try:
                ret = cls._SapModel.View.RefreshView(0, False)
            except:
                pass
        

    @classmethod
    def set_etabs_units(cls, units = etabs_units['N_mm_C']):
        """
        set ETABS units.
        """
        if cls._SapModel:
            ret = cls._SapModel.SetPresentUnits(units)
    
    @classmethod
    def set_sap_units(cls, units = sap_units['N_mm_C']):
        """
        set SAP units.
        """
        if cls._SapModel:
            ret = cls._SapModel.SetPresentUnits(units)

    @classmethod
    def release_csi_models(cls, refresh_view = True):
        """
        clean and release current csi objects,
        with option to refresh view.
        """

        if refresh_view:
            #refresh view
            cls.refresh_view()

        cls._SapModel = None
        cls._mySapObject = None
        cls._myETABSObject = None


def _get_warning_area_coordinates(coordinates, size = 500.0):
    name = ''
    section_name = 'None'
    slab_pnt_count = 3

    x_loc = coordinates[0]
    y_loc = coordinates[1]
    z_loc = coordinates[2]

    x_left = x_loc - size 
    x_right = x_loc + size
    y_left = y_loc - size * 2
    y_right = y_loc - size * 2

    x = [x_loc,x_left,x_right]
    y = [y_loc,y_left,y_right]
    z = [z_loc]*3

    AddByCoord = {
        'NumberPoints':slab_pnt_count,
        'X' : x,
        'Y' : y,
        'Z' : z,
        'Name' : name,
        'PropName' : section_name or 'Default',
        'UserName' : name,
        'CSys' : 'Global'
    }
    return AddByCoord

def add_area(coords, group_name = 'Warnings'):
    SapModel = CsiHelper.connect_to_etabs(units=None)
    ret = SapModel.AreaObj.AddByCoord(**_get_warning_area_coordinates(coords))
    if ret[0] != 0:
        # print(f'Error in adding area; ETABS CODE {ret[0]}')
        return None
    
    area_name = str(ret[4])
    if group_name:
        _ = SapModel.AreaObj.SetGroupAssign(area_name, group_name)

    return area_name


def get_etabs_groups():
    SapModel = CsiHelper.connect_to_etabs(units=None)
    etabs_groups = {
        'NumberNames': 0,
        'MyName': []
    }

    ret = SapModel.GroupDef.GetNameList(**etabs_groups)
    if ret[0] != 0:
        # print(f'Error in reading groups names; ETABS CODE {ret[0]}')
        return None
    etabs_groups_names = list(ret[2])
    return etabs_groups_names


def create_etabs_group(group_name):
    SapModel = CsiHelper.connect_to_etabs(units=None)
    etabs_groups_names = get_etabs_groups()

    if group_name not in etabs_groups_names:
        SetGroup = {
            'Name' : group_name,
            'color' : -1,
            'SpecifiedForSelection' : True,
            'SpecifiedForSectionCutDefinition' : False,
            'SpecifiedForSteelDesign' : False,
            'SpecifiedForConcreteDesign' : False,
            'SpecifiedForAluminumDesign' : False,
            'SpecifiedForStaticNLActiveStage' : False,
            'SpecifiedForAutoSeismicOutput' : False,
            'SpecifiedForAutoWindOutput' : False,
            'SpecifiedForMassAndWeight' : False,
            'SpecifiedForSteelJoistDesign' : False,
            'SpecifiedForWallDesign' : False,
            'SpecifiedForBasePlateDesign' : False,
            'SpecifiedForConnectionDesign' : False,
        }
        ret = SapModel.GroupDef.SetGroup_1(**SetGroup)
        if ret != 0:
            #print(f'Error in reading groups names; ETABS CODE {ret[0]}')
            return None
    return group_name
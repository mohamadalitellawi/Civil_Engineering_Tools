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
    def connect_to_etabs(cls, SapModel = None, units = etabs_units['N_mm_C']):
        """
        Connect To Running Etabs Instance.
        check if already connected.
        Args:
            SapModel: Etabs SapModel Object
        
        Returns:
            Etabs SapModel object
        """

        if SapModel is not None:
            if units is not None:
                ret = SapModel.SetPresentUnits(units)
            cls._SapModel = SapModel
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
    def connect_to_sap(cls, SapModel = None, units = sap_units['N_mm_C']):
        """
        Connect To Running SAP2000 Instance.
        check if already connected.
        Args:
            SapModel: SAP2000 SapModel Object
        
        Returns:
            SAP2000 SapModel object
        """

        if SapModel is not None:
            if units is not None:
                ret = SapModel.SetPresentUnits(units)
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
            ret = cls._SapModel.View.RefreshView(0, False)


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
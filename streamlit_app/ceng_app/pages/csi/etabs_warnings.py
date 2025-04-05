import streamlit as st
import mat_ceng as mc
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from io import StringIO
import pandas as pd


st.set_page_config(
    page_title="Display ETABS Warnings",
    page_icon="👀",
)

st.sidebar.success("Display ETABS Warnings")

uploaded_file = st.file_uploader("Choose a Text file containing ETABS warnings", 
                                 accept_multiple_files=False)




def get_area_coordinates(coordinates):
    name = ''
    section_name = 'None'
    size = 500.0
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


def add_area_floor(SapModel, coords, warning_group_name = 'Warnings'):
    # display(get_area_coordinates(coords))
    ret = SapModel.AreaObj.AddByCoord(**get_area_coordinates(coords))
    if ret[0] != 0:
        # print(f'Error in adding area; ETABS CODE {ret[0]}')
        pass
    else:
        area_name = str(ret[4])
        _ = SapModel.AreaObj.SetGroupAssign(area_name, warning_group_name)
        return area_name


def run():
    bytes_data = uploaded_file.getvalue()
    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
    string_data = stringio.read()
#    st.write(string_data)

    result = {
        'total_warnings': 0,
        'colleced_warnings': 0,
        'warnings': defaultdict(list),  # Using defaultdict for automatic list initialization,
        'warning_locations': []
    }

    unit_conversion = 1.0

    lines = string_data.split('\n')
    for indx, line in enumerate(lines):
        if indx == 0:
            result['total_warnings'] = int(line.strip().split(', ')[1].split(' ')[0])
            continue
        row = line.strip()
        if 'Check at (' in row:
            result['colleced_warnings'] += 1
            coord = row.split('Check at (')[1].split(')')[0].split(' ')
            coord = [float(x) * unit_conversion for x in coord]
            coord = tuple(coord)
            result['warning_locations'].append(coord)
            result['warnings'][coord].append(row)


    result['warnings'] = dict(result['warnings'])  # Convert defaultdict to dict
    result['warning_locations'] = list(set(result['warning_locations']))  # Remove duplicates
    st.write(f'total warnings: {result["total_warnings"]}, collected warnings: {result["colleced_warnings"]}')



    import clr
    clr.AddReference("System.Runtime.InteropServices")
    from System.Runtime.InteropServices import Marshal

    #set the following path to the installed ETABS program directory
    clr.AddReference(R'C:\Program Files\Computers and Structures\ETABS 22\ETABSv1.dll')
    import ETABSv1 as etabs

    #create API helper object
    helper = etabs.cHelper(etabs.Helper())

    try:
        myETABSObject = etabs.cOAPI(helper.GetObject("CSI.ETABS.API.ETABSObject"))
    except:
        error_msg = "No running instance of the program found or failed to attach."
        st.error(error_msg)


    #create SapModel object
    SapModel = etabs.cSapModel(myETABSObject.SapModel)

    N_mm_C = etabs.eUnits.N_mm_C
    kN_m_C = etabs.eUnits.kN_m_C


    ret = SapModel.SetPresentUnits(N_mm_C)

    etabs_groups = {
        'NumberNames': 0,
        'MyName': []
    }

    ret = SapModel.GroupDef.GetNameList(**etabs_groups)
    if ret[0] != 0:
        print(f'Error in reading groups names; ETABS CODE {ret[0]}')
    etabs_groups_names = list(ret[2])


    warning_group_name = 'Warnings'

    if warning_group_name not in etabs_groups_names:
        SetGroup = {
            'Name' : warning_group_name,
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
            print(f'Error in reading groups names; ETABS CODE {ret[0]}')



    etabs_added_areas = [add_area_floor(SapModel, x) for x in result['warning_locations']]

    #refresh view
    ret = SapModel.View.RefreshView(0, False)

    SapModel = None
    myETABSObject = None
    df = pd.DataFrame(result['warnings'].items(), columns=['Coordinates', 'Warnings'])
    df['area_name'] = etabs_added_areas
    df['Warnings'] = df['Warnings'].apply(lambda x: '\n'.join(x))
    df.set_index('area_name', inplace=True)
    return df




st.markdown('## Results:')

if st.button("Run", help='Click Me!'):
    st.write(run())



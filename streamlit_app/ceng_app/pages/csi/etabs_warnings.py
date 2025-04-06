import streamlit as st
import mat_ceng as mc
from collections import defaultdict
import pandas as pd


st.set_page_config(
    page_title="Display ETABS Warnings",
    page_icon="👀",
)

st.sidebar.success("Display ETABS Warnings")


def load_file_from_upload() -> str|None:
    """
    Load file content from Streamlit's file uploader.
    
    Returns:
        String content of the file or None if no file uploaded
    """
    uploaded_file = st.file_uploader("Upload text file", type=['txt', 'csv', 'log'], accept_multiple_files=False)
    
    if uploaded_file is None:
        return None
    
    try:
        content = uploaded_file.getvalue().decode("utf-8")
        return content
    except Exception as e:
        st.error(f"Error processing uploaded file: {str(e)}")
        return None
    

uploaded_content = load_file_from_upload()

unit_conversion = st.number_input(
    label='unit conversion',
    value=1.0
)

def run():
    if uploaded_content:
        st.success("File uploaded successfully!")

    result = {
        'total_warnings': 0,
        'colleced_warnings': 0,
        'warnings': defaultdict(list),  # Using defaultdict for automatic list initialization,
        'warning_locations': []
    }

    try:
        lines = uploaded_content.split('\n')
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
    except Exception as e:
        st.error(f"Error processing file content: {str(e)}")
        return None
        

    #create SapModel object
    try:
        mc.csi.CsiHelper.connect_to_etabs()
    except Exception as e:
        st.error(f"Error connecting to ETABS: {str(e)}")
        return None
    

    warning_group_name = 'Warnings'
    try:
        mc.csi.create_etabs_group(warning_group_name)
        etabs_added_areas = [mc.csi.add_area(x, warning_group_name) for x in result['warnings'].keys()]
    except Exception as e:
        st.error(f"Error adding areas to ETABS: {str(e)}")
        return None
    

    #refresh view
    mc.csi.CsiHelper.refresh_view()
    mc.csi.CsiHelper.release_csi_models()
    st.markdown('---')

    if any(etabs_added_areas):
        try:
            df = pd.DataFrame(result['warnings'].items(), columns=['Coordinates', 'Warnings'])
            df['area_name'] = etabs_added_areas
            df['Warnings'] = df['Warnings'].apply(lambda x: '\n'.join(x))
            df.set_index('area_name', inplace=True)
            return df
        except Exception as e:
            st.error(f'Error creating Dataframe: {str(e)}')
            return None
    

st.markdown('## Results:')

if st.button("Run", help='Click Me!'):
    st.write(run())



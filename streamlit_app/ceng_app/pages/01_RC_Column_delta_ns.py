import streamlit as st
import mat_ceng as mc

st.set_page_config(page_title="Calculate delta_ns based on equation c", page_icon="🆘")
st.markdown('## Based on ACI318-19M')
st.markdown('## Inputs:')
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Material:")
    fc = st.number_input(
        label="specified compressive strength of concrete, MPa",
        min_value=17,
        max_value=80,
        value=40,
        step=1)
    fy = st.number_input(
        label="specified yield strength for nonprestressed reinforcement, MPa",
        min_value=240,
        max_value=550,
        value=420,)
    st.markdown("### Col Length:")

    lu_22= st.number_input( 'unsupported length of column or wall lu_22, mm' ,value=5000.0)
    lu_33= st.number_input( 'unsupported length of column or wall lu_33, mm',value=5000.0)
    k_22= st.number_input( 'effective length factor for compression members k_22', value=1.0)
    k_33= st.number_input( 'effective length factor for compression members k_33', value=1.0)

with col2:
    st.markdown("### Dimensions:")
    st.markdown('Note that the dimension c33 is the depth of the Section in the 2-2 direction and contributes primarily to I33')
    section_c22 = st.number_input( 'cross section width c22, mm',value=250.0)
    section_c33 = st.number_input( 'cross section depth c33, mm',value=800.0)
    section_cc = st.number_input( '20.5.1.3 clear cover of reinforcement, mm', value=40.0)
    rft_ratio = st.number_input( 'reinforcements ratio of longitudinal bars', value=0.02)

with col3:
    st.markdown("### Loads:")
    st.markdown(' factored axial force; to be taken as positive for compression and negative for tension, N')
    Pu = st.number_input( 'ultimate design axial force, kN', value=1000.0)
    Pu_sustained= st.number_input( 'ultimate sustained axial force, kN', value= 800.0)
    Mu_22 = st.number_input( 'ultimate desigm moment about local axis 2-2 as per ETABS, kN*m' , value=250.0)
    Mu_33 = st.number_input( 'ultimate desigm moment about local axis 3-3 as per ETABS, kN*m', value= 500.0)
    Cm = st.number_input('factor relating actual moment diagram to an equivalent uniform moment diagram Cm', value=0.6)


st.markdown('## Results:')

material=mc.Material(
    fc=fc,
    fy=fy)

dimensions=mc.Section_Dimensions(
    section_c22=section_c22,
    section_c33=section_c33, 
    section_cc=section_cc, 
    rft_ratio=rft_ratio)

load=mc.Load_Case(
    Pu=Pu, 
    Pu_sustained=Pu_sustained,
    Mu_22=Mu_22,
    Mu_33=Mu_33).import_from_etabs(flip_axial_sign=False)

column = mc.Column(
    lu_22=lu_22, 
    lu_33=lu_33,
    k_22=k_22,
    k_33=k_33)

actual_moment_of_inertia = mc.calculate_column_actual_moment_of_inertia(
    material,
    dimensions,
    load
)

minor_delta_ns = mc.calculate_minor_delta_ns(
    column,
    material,
    dimensions,
    load,
    Cm
)

major_delta_ns = mc.calculate_major_delta_ns(
    column,
    material,
    dimensions,
    load,
    Cm
)

with st.container(border=True):
    st.write('##### actual_moment_of_inertia, mm⁴:')
    st.write(f'I22 = {actual_moment_of_inertia["moment_of_inertia"][0]:,}')
    st.write(f'I33 = {actual_moment_of_inertia["moment_of_inertia"][1]:,}')
    st.write('##### actual_moment_of_inertia ratio to gross moment_of_inertia:')
    st.write(f'I22 / Ig22 = {actual_moment_of_inertia["ratio"][0]}')
    st.write(f'I33 / Ig33 = {actual_moment_of_inertia["ratio"][1]}')

with st.container(border=True):
    st.write('##### minor delta_non_sway (delta_ns):')
    st.write(f'Etabs: delta_ns = {minor_delta_ns["Etabs"]}')
    st.write(f'Method C: delta_ns = {minor_delta_ns["Method_C"]}')

with st.container(border=True):
    st.write('##### major delta_non_sway (delta_ns):')
    st.write(f'Etabs: delta_ns = {major_delta_ns["Etabs"]}')
    st.write(f'Method C: delta_ns = {major_delta_ns["Method_C"]}')


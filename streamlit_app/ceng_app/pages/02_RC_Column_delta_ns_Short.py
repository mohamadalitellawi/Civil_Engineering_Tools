import streamlit as st
import mat_ceng as mc

st.set_page_config(page_title="Calculate delta_ns based on equation c", page_icon="🆘")
st.markdown('## Based on ACI318-19M')
st.markdown('## Inputs:')
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("### Material:")
    fc = st.number_input(
        label="f'c, MPa",
        min_value=17,
        max_value=80,
        value=32,
        step=1)
    fy = st.number_input(
        label="fy, MPa",
        min_value=240,
        max_value=550,
        value=420,)
    st.markdown("### Col Length:")

    lu_22= st.number_input( 'length lu_22, mm' ,value=4800.0)
    lu_33= st.number_input( 'length lu_33, mm',value=4800.0)
    k_22= st.number_input( 'k_22', value=1.0)
    k_33= st.number_input( 'k_33', value=1.0)

with col2:
    st.markdown("### Dimensions:")
    st.markdown('Note that the dimension c33 is the depth of the Section in the 2-2 direction and contributes primarily to I33')
    section_c22 = st.number_input( 'width c22, mm',value=250.0)
    section_c33 = st.number_input( 'depth c33, mm',value=800.0)
    section_cc = st.number_input( 'clear cover, mm', value=40.0)
    rft_ratio = st.number_input( 'rft ratio', value=0.0141 )
    rft_bars_2dir = st.number_input( 'bars along 2-dir',value=7)
    rft_bars_3dir = st.number_input( 'bars along 3-dir',value=2)
    rft_bar_dia = st.number_input( 'bar diameter',value=16)



with col3:
    st.markdown("### Loads:")
    st.markdown(' factored axial force; to be taken as positive for compression and negative for tension, kN')
    Pu = st.number_input( 'Pu, kN', value=1385.0853)
    Pu_sustained= st.number_input( 'Pu_sustained, kN', value= 1150.0993)
    Mu_22 = st.number_input( 'Mu 2-2, kN*m' , value=2.727)
    Mu_33 = st.number_input( 'Mu 3-3, kN*m', value= 300.0)
    Cm = st.number_input('Cm', value=0.532)


st.markdown('## Results:')

material=mc.Material(
    fc=fc,
    fy=fy)

dimensions=mc.Section_Dimensions(
    section_c22=section_c22,
    section_c33=section_c33, 
    section_cc=section_cc, 
    rft_ratio=rft_ratio,
    rft_bar_dia = rft_bar_dia,
    rft_bars_2dir=rft_bars_2dir,
    rft_bars_3dir=rft_bars_3dir)

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
    st.write(f'Etabs: delta_ns = {minor_delta_ns["Etabs"]:.3f}')
    st.write(f'Method B: delta_ns = {minor_delta_ns["Method_B"]:.3f}')
    st.write(f'Method C: delta_ns = {minor_delta_ns["Method_C"]:.3f}')
    st.write(f"Pc: {minor_delta_ns['Pc'][0]/1000:.3f}---{minor_delta_ns['Pc'][1]/1000:.3f}---{minor_delta_ns['Pc'][2]/1000:.3f}")

with st.container(border=True):
    st.write('##### major delta_non_sway (delta_ns):')
    st.write(f'Etabs: delta_ns = {major_delta_ns["Etabs"]:.3f}')
    st.write(f'Method B: delta_ns = {major_delta_ns["Method_B"]:.3f}')
    st.write(f'Method C: delta_ns = {major_delta_ns["Method_C"]:.3f}')
    st.write(f"Pc: {major_delta_ns['Pc'][0]/1000:.3f}---{major_delta_ns['Pc'][1]/1000:.3f}---{major_delta_ns['Pc'][2]/1000:.3f}")


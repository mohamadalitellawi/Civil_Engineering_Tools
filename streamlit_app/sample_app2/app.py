import streamlit as st
from handcalcs.decorator import handcalc
import forallpeople as si

si.environment("structural")


@handcalc()
def calc_Mr(b: float, d: float, phi: float, f_y: float):
    """
    Calculates Mr of a rectangular section
    """
    S_x = (b * d**2) / 6  # Section modulus
    M_r = phi * S_x * f_y
    return M_r


b_value = st.sidebar.number_input("Section width (mm)")
d_value = st.sidebar.number_input("Section depth (mm)")
fy_value = st.sidebar.number_input("Steel yield strength (MPa)", value=350)

phi = 0.9
b = b_value * si.mm
d = d_value * si.mm
fy = fy_value * si.MPa

mr_latex, mr_value = calc_Mr(b, d, phi, fy)

st.markdown("# Calculating the moment capacity of a steel plate (no LTB)")
st.latex(mr_latex)

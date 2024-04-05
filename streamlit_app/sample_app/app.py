import streamlit as st
import sample_app_module as sam

# streamlit run app.py

st.header("Sample Calculation")


st.sidebar.subheader("Sample Parameters")
a = st.sidebar.number_input("Width (cm)", value=3)
b = st.sidebar.number_input("height (cm)", value=4)

example_latex, result = sam.sample_main_calculation(
    a,
    b
    )

st.write(result)
st.latex(example_latex[-1])
st.write(example_latex)

calc_expander = st.expander(label="Sample Calculation Equations")
with calc_expander:
    for calc in example_latex:
        st.latex(
            calc
        )


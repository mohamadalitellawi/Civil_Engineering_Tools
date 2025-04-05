import streamlit as st

st.set_page_config(
    page_title="Hello",
    page_icon="👋",
)

st.write("# Welcome to Civil Engineering Tools! 👋")
st.write(('streamlit version: ', st.__version__))
st.markdown(
    """
    ### Introduction
    This is under construction app collecting some useful tools for civil engineering that are needed regularly in the daily tasks for a civil engineer.\n
    There is no intent to be a full set of tools or as a replacement for some useful commercial softwares in the civil engineering eco system (Prokon, STEPS, TEDDS, ...).\n
    Most of the tools will be built by Python Programing language and following the American standards mostly with metric units.
"""
)

st.markdown(
    '''
### Credits
- big thanks for <a href="https://github.com/connorferster">Connor Ferster</a> for his good training, most of the work here is based on his good teaching.
'''
)
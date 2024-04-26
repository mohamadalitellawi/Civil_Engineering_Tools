import streamlit as st

st.bar_chart({"data": [1, 5, 2, 6, 2, 1]})

with st.expander(":writing_hand: :violet[See explanation]"):
    st.write("""
        The chart above shows some numbers I picked for you.
        I rolled actual dice for these, so they're *guaranteed* to
        be random.
    """)
    st.image("https://static.streamlit.io/examples/dice.jpg")

with st.expander(":thumbsup: :violet[See explanation 2]"):
    st.write("""
        The chart above shows some numbers I picked for you.
        I rolled actual dice for these, so they're *guaranteed* to
        be random.
    """)
    st.image("https://static.streamlit.io/examples/cat.jpg")
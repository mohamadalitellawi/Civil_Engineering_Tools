import streamlit as st

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def login():
    if st.button("Log in"):
        st.session_state.logged_in = True
        st.rerun()

def logout():
    if st.button("Log out"):
        st.session_state.logged_in = False
        st.rerun()

login_page = st.Page(login, title="Log in", icon=":material/login:")
logout_page = st.Page(logout, title="Log out", icon=":material/logout:")

dashboard = st.Page(
    "pages/main/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True
)

col_dns_short = st.Page(
    "pages/rc_columns/02_RC_Column_delta_ns_Short.py"
)

col_dns = st.Page(
    "pages/rc_columns/03_RC_Column_delta_ns.py"
)

col_trib_forces = st.Page(
    "pages/forces/01_Column_Trib_Forces.py"
)


if st.session_state.logged_in:
    pg = st.navigation(
        {
            "Account": [logout_page],
            "RC Column Tools": [dashboard, col_dns_short, col_dns],
            "Forces Tools": [col_trib_forces],
        }
    )
else:
    pg = st.navigation([login_page])

pg.run()
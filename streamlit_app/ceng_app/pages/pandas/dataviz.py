import streamlit as st
import pandas as pd

uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])

st.title('PANDAS Visualization Sample')

if uploaded_file is None:
    st.warning("Please select a valid csv file.")
    st.stop()  # Stop the app if the name is not entered

# Read the uploaded CSV file into a pandas DataFrame
df = pd.read_csv(uploaded_file)

# Now you can display or process the DataFrame
st.write("### Data Preview")
st.dataframe(df.head())

# create a dropdown menu for column selection
available_columns = [col for col in df.columns if col != 'Year']
selected_column = st.selectbox("Select a column to plot", available_columns)

# slider for filtering the years
year_min = int(df['Year'].min())
year_max = int(df['Year'].max())
selected_year = st.slider("Select a year range", year_min, year_max, (year_min, year_max))

# filter the DataFrame based on the selected year range
filtered_df = df[(df['Year'] >= selected_year[0]) & (df['Year'] <= selected_year[1])]

# create visualization with the selected columns
st.line_chart(filtered_df.set_index('Year')[selected_column])

# show filtered data preview
st.subheader("Filtered Data Preview")
st.dataframe(filtered_df.style.format({
    'Death Rate': '{:.2f}'
}))
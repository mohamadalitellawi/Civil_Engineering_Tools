import streamlit as st
import mat_ceng as mc
from io import StringIO

import shapely
from shapely import (
    Point, 
    MultiPoint, 
    Polygon, 
    MultiPolygon, 
    LineString, 
    MultiLineString,
    GeometryCollection
)
import json
import numpy as np
import plotly.graph_objects as go


st.set_page_config(page_title="Calculate Draw Columns/walls trib area and forces", page_icon="🕸️")
st.markdown('## Calculate Draw Columns/walls trib area and forces')
st.markdown('## Inputs:')
col1, col2 = st.columns(2)

with col1:
    st.write('**Step 1/** select json files for flood data and loading categories:')
    uploaded_files = st.file_uploader("Choose a JSON file", accept_multiple_files=True)
    st.write('***floor_data.json***: contain floor data (slab edge, columns, walls, and openings)')
    st.write('***occupancy_loading.json***: contain loading categories details (heavy, light)')
    for uploaded_file in uploaded_files:
        if uploaded_file.name.lower() == 'floor_data.json':
            floor_data = json.load(uploaded_file) 
        elif uploaded_file.name.lower() == 'occupancy_loading.json':
            occupancy_loading = json.load(uploaded_file)


with col2:
    st.write('**Step 2/** write the dead and live load factors:')
    dead_factor = st.number_input("Insert a Dead Load Factor", value=1.4)
    live_factor = st.number_input("Insert a Live Load Factor", value=1.7)
    st.write('---')
    wall_mesh = st.number_input("Insert a wall mesh distance", value=300.0)

def calculation():
    col_area_load = mc.get_column_area_loads(floor_data,occupancy_loading,wall_mesh)
    x_edge,y_edge = zip(*floor_data['slab_outline'])

    x_col, y_col = [],[]
    for col in col_area_load:
        x,y = col.column_outline.exterior.xy
        x_col = x_col + list(x) + [None]
        y_col = y_col + list(y) + [None]

    fig = go.Figure(go.Scatter(x=x_col, y=y_col, fill="toself",opacity =0.25,hoverinfo='skip'))

    x_col, y_col = [],[]
    for col in col_area_load:
        if col.trib_area.geom_type == 'Polygon':
            x,y = col.trib_area.exterior.xy
            x_col = x_col + list(x) + [None]
            y_col = y_col + list(y) + [None]
        elif col.trib_area.geom_type == 'MultiPolygon':
            for plg in col.trib_area.geoms:
                x,y = plg.exterior.xy
                x_col = x_col + list(x) + [None]
                y_col = y_col + list(y) + [None]

    fig.add_trace(go.Scatter(
        x=x_col,
        y=y_col,
        fill="toself",
        opacity =0.25,
        hoverinfo='skip'
    ))

    fig.add_trace(go.Scatter(
        x=x_edge,
        y=y_edge,
        mode="lines",
        hoverinfo='skip'
    ))

    x = [col.column_outline.centroid.x for col in col_area_load]
    y = [col.column_outline.centroid.y for col in col_area_load]
    labels = [round(col.get_combined_load(np.array([dead_factor,live_factor,0])),2) for col in col_area_load]
    trib_areas = [str(round(col.trib_area.area / 1e6,2)) + ' m²' for col in col_area_load]
    # Create scatter trace of text labels
    fig.add_trace(
        go.Scatter(
            x=x, y=y, mode="markers", 
            opacity = 0.25,
            hoverinfo='skip',
            showlegend=False,
            marker_size=[float(area[:-3])*1.5 for area in trib_areas],
            marker={"color": "green"}
    ))


    fig.add_trace(go.Scatter(
        x=x,
        y=y,
        text=labels,
        mode="text",
        hovertext = trib_areas,
        hoverinfo="text"
    ))

    fig.update_layout(
        width = 900,
        height = 900,
        title = "Column Design Forces [KN]"
    )

    fig.update_yaxes(
        scaleanchor = "x",
        scaleratio = 1,
    )
    # Plot!
    st.plotly_chart(fig, use_container_width=True)
    #fig.show()



st.markdown('## Results:')

if st.button("Start Calculations", help='Click Me!'):
    calculation()



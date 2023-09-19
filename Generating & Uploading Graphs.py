
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import plotly.graph_objects as go
import numpy as np
import pandas as pd

from google.cloud import storage

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson.json_util import dumps

from gcloud import storage
from oauth2client.service_account import ServiceAccountCredentials
import os

credentials_dict = {
}
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    credentials_dict
)
client = storage.Client(credentials=credentials, project='My First Project')
bucket = client.get_bucket('schematic.buildspace.biz')


uri = "mongodb+srv://@buildspace.3szcgnw.mongodb.net/?retryWrites=true&w=majority"

# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["BuildSpaceDB"]
collection = db["Maintenance-Info"]


def main(floor, ddate):
    p = collection.find()
    l = list(p)
    s = dumps(l)

    x = [0, 0.2, 0.4, 0.6, 0.8, 1]
    x_values = [0, 0.2, 0.4, 0.6, 0.8, 1]
    x_labels = ["Label 1", "Label 2", "Label 3", "Label 4", "Label 5", "Label 6"] 
    y = [0, 0.2, 0.4, 0.6, 0.8, 1]
    z = [[0] * 6 for _ in range(6)]  # Example data for the plane, all Z-values are set to 0

    # Create a 3D surface trace for the plane with a black outline
    trace_plane = go.Surface(
        x=x,
        y=y,
        z=z,
        colorscale='Viridis',
        hoverinfo='none',
        showscale=False,
    )

    # Calculate the dimensions of each grid cell
    grid_cell_width = 1.0 / 5
    grid_cell_height = 1.0 / 5

    # Create grid lines (horizontal and vertical) for the 5x5 grid pattern
    x_grid = np.linspace(0, 1, 6)
    y_grid = np.linspace(0, 1, 6)

    # Create data for the grid lines
    grid_lines = []
    for x_val in x_grid:
        grid_lines.append(go.Scatter3d(
            x=[x_val] * 6,
            y=y_grid,
            z=np.zeros(6),
            mode='lines',
            line=dict(color='black'),
            showlegend=False,
            hoverinfo='none'  # Set hoverinfo to 'none' to disable hover descriptions
        ))
    for y_val in y_grid:
        grid_lines.append(go.Scatter3d(
            x=x_grid,
            y=[y_val] * 6,
            z=np.zeros(6),
            mode='lines',
            line=dict(color='black'),
            showlegend=False,
            hoverinfo='none'  # Set hoverinfo to 'none' to disable hover descriptions
        ))
        

    # Read the CSV data into a DataFrame
    data = pd.read_json(s)

    # Filter the data to select Fire Alarm assets on floor 1
    floor_data = data[data['Floor'] == floor]
    sorted_data = floor_data.sort_values(by=['Asset Type', 'Room'])
    sorted_data['Status'] = ((pd.to_datetime(ddate, format='%m/%d/%Y') - pd.to_datetime(sorted_data['Last Serviced Date'], format='%d/%m/%Y')).dt.days / 30).astype(int).apply(lambda x: 'red' if x > 12 else ('blue' if 5 <= x <= 12 else 'green'))


    # Calculate the dimensions of each grid cell
    grid_cell_width = 1.0 / 5
    grid_cell_height = 1.0 / 5

    legend_symbols = []  # To store the symbols for the legend
    custom_legend_names = []  # To store custom legend names


    ################################################################
    ################################################################
    ################################################################
    ################################################################
    room_z_coordinates = {}
    room_y_coordinates = {}
    dateCheck = {}
    asset_marker_symbols = {'Electrical Panel' : 'circle', 'Elevator' : 'square', 'Fire Alarm': 'circle-open', 'HVAC': 'diamond-open', 'Plumbing System' : 'cross'}

    i = 0.0

    # Create scatter3d traces for all asset types in the grid
    asset_traces = []

    for index, row in sorted_data.iterrows():
        asset_type = row['Asset Type']
        room_number = row['Room']
        status = row['Status']
        
        if (asset_type, room_number) not in room_z_coordinates:
            room_z_coordinates[(asset_type, room_number)] = -0.2  # Initialize Z-coordinate for the asset type and room
            room_y_coordinates[(asset_type, room_number)] = i
            i += 0.05
        

        marker_symbol = asset_marker_symbols.get(asset_type)
        
        # Calculate the X and Y coordinates as before
        if 101 <= room_number <= 105:
            col_index = (room_number - 101) % 5
            row_index = (room_number - 101) // 5
            x_coordinate = (col_index + 0.5) * grid_cell_width
            y_coordinate = ((4 - row_index) + (0.5 - room_y_coordinates[(asset_type, room_number)])) * grid_cell_height  # Invert the Y-coordinate
        
        if 106 <= room_number <= 110:
            col_index = (room_number - 101) % 5 
            row_index = (room_number - 101) // 5
            x_coordinate = (col_index + 0.5) * grid_cell_width
            y_coordinate = ((4 - row_index) - (3 - room_y_coordinates[(asset_type, room_number)])) * grid_cell_height
            
        room_z_coordinates[(asset_type, room_number)] += 0.3  # Increase the Z-coordinate for the next asset in the same room
        
        
        marker = go.Scatter3d(
            x=[x_coordinate],
            y=[y_coordinate],
            z=[room_z_coordinates[(asset_type, room_number)]],
            mode='markers',
            marker=dict(
                size=12,
                symbol = marker_symbol,
                color = status,
            ),
            showlegend=False,
            text = f'{asset_type} in Room {room_number}',  # Create a single string for the name
            hovertemplate=f'{asset_type} in Room {room_number} <br> Last Serviced: {row["Last Serviced Date"]}<extra></extra>',

        )
        
    
        asset_traces.append(marker)
        
        legend_symbols.append(go.Scatter3d(
            x=[],
            y=[],
            z=[],
            mode='markers',
            marker=dict(
                size=12,
                symbol=marker_symbol,
                color=status,
            ),
            name=asset_type,
            showlegend=True,
        ))
        ##
        
        custom_legend_name = f'{asset_type} (Custom Name)'  # You can modify this to your desired custom name
        custom_legend_names.append(custom_legend_name)
        

    ################################################################
    ################################################################
    ################################################################
    ################################################################



    # Create the figure with both the plane, grid lines, and Fire Alarm markers
    fig = go.Figure(data = [trace_plane] + grid_lines + asset_traces )


    # Create data for the plane (flat on the Z-axis)
    x = [0, 0.2, 0.4, 0.6, 0.8, 1]
    x_values = [0, 0.2, 0.4, 0.6, 0.8, 1]
    x_labels = ["Label 1", "Label 2", "Label 3", "Label 4", "Label 5", "Label 6"] 
    y = [0, 0.2, 0.4, 0.6, 0.8, 1]
    z = [[1] * 6 for _ in range(6)]  # Example data for the plane, all Z-values are set to 0

    # Create a 3D surface trace for the plane with a black outline
    trace_plane = go.Surface(
        x=x,
        y=y,
        z=z,
        colorscale='Viridis',
        hoverinfo='none',
        showscale=False,
    )

    # Calculate the dimensions of each grid cell
    grid_cell_width = 1.0 / 5
    grid_cell_height = 1.0 / 5

    # Create grid lines (horizontal and vertical) for the 5x5 grid pattern
    x_grid = np.linspace(0, 1, 6)
    y_grid = np.linspace(0, 1, 6)

    # Create data for the grid lines
    grid_lines = []
    for x_val in x_grid:
        grid_lines.append(go.Scatter3d(
            x=[x_val] * 6,
            y=y_grid,
            z=[1] * 6,
            mode='lines',
            line=dict(color='black'),
            showlegend=False,
            hoverinfo='none'  # Set hoverinfo to 'none' to disable hover descriptions
        ))
    for y_val in y_grid:
        grid_lines.append(go.Scatter3d(
            x=x_grid,
            y=[y_val] * 6,
            z=[1] * 6,
            mode='lines',
            line=dict(color='black'),
            showlegend=False,
            hoverinfo='none'  # Set hoverinfo to 'none' to disable hover descriptions
        ))
        

    # Filter the data to select Fire Alarm assets on floor 1
    floor_data = data[data['Floor'] == floor + 1]
    sorted_data = floor_data.sort_values(by=['Asset Type', 'Room'])
    sorted_data['Status'] = ((pd.to_datetime(ddate, format='%m/%d/%Y') - pd.to_datetime(sorted_data['Last Serviced Date'], format='%d/%m/%Y')).dt.days / 30).astype(int).apply(lambda x: 'red' if x > 12 else ('blue' if 5 <= x <= 12 else 'green'))


    # Calculate the dimensions of each grid cell
    grid_cell_width = 1.0 / 5
    grid_cell_height = 1.0 / 5

    legend_symbols = []  # To store the symbols for the legend
    custom_legend_names = []  # To store custom legend names


    ################################################################
    ################################################################
    ################################################################
    ################################################################
    room_z_coordinates = {}
    room_y_coordinates = {}
    dateCheck = {}
    asset_marker_symbols = {'Electrical Panel' : 'circle', 'Elevator' : 'square', 'Fire Alarm': 'circle-open', 'HVAC': 'diamond-open', 'Plumbing System' : 'cross'}

    i = 0.0

    # Create scatter3d traces for all asset types in the grid
    asset_traces = []

    for index, row in sorted_data.iterrows():
        asset_type = row['Asset Type']
        room_number = row['Room']
        status = row['Status']
        
        if (asset_type, room_number) not in room_z_coordinates:
            room_z_coordinates[(asset_type, room_number)] = 0.8  # Initialize Z-coordinate for the asset type and room
            room_y_coordinates[(asset_type, room_number)] = i
            i += 0.05
        

        marker_symbol = asset_marker_symbols.get(asset_type)
        
        # Calculate the X and Y coordinates as before
        if 101 <= room_number <= 105:
            col_index = (room_number - 101) % 5
            row_index = (room_number - 101) // 5
            x_coordinate = (col_index + 0.5) * grid_cell_width
            y_coordinate = ((4 - row_index) + (0.5 - room_y_coordinates[(asset_type, room_number)])) * grid_cell_height  # Invert the Y-coordinate
        
        if 106 <= room_number <= 110:
            col_index = (room_number - 101) % 5 
            row_index = (room_number - 101) // 5
            x_coordinate = (col_index + 0.5) * grid_cell_width
            y_coordinate = ((4 - row_index) - (3 - room_y_coordinates[(asset_type, room_number)])) * grid_cell_height
            
        room_z_coordinates[(asset_type, room_number)] += 0.3  # Increase the Z-coordinate for the next asset in the same room
        
        
        marker = go.Scatter3d(
            x=[x_coordinate],
            y=[y_coordinate],
            z=[room_z_coordinates[(asset_type, room_number)]],
            mode='markers',
            marker=dict(
                size=12,
                symbol = marker_symbol,
                color = status,
            ),
            showlegend=False,
            text = f'{asset_type} in Room {room_number}',  # Create a single string for the name
            hovertemplate=f'{asset_type} in Room {room_number} <br> Last Serviced: {row["Last Serviced Date"]}<extra></extra>',

        )
        
    
        asset_traces.append(marker)
        
        legend_symbols.append(go.Scatter3d(
            x=[],
            y=[],
            z=[],
            mode='markers',
            marker=dict(
                size=12,
                symbol=marker_symbol,
                color=status,
            ),
            name=asset_type,
            showlegend=True,
        ))
        ##
        
        custom_legend_name = f'{asset_type} (Custom Name)'  # You can modify this to your desired custom name
        custom_legend_names.append(custom_legend_name)
        

    fig2 = go.Figure(data = [trace_plane] + grid_lines + asset_traces )

    for trace in fig2.data:
        fig.add_trace(trace)

    # Set layout properties
    fig.update_layout(
        scene=dict(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            zaxis=dict(range=[0, 2], showgrid=False, showticklabels=False),
        ),
    )

    fig.update_layout(modebar_remove=  ['displaylogo', 'zoom3d', 'pan3d', 'orbitRotation', 'tableRotation', 'handleDrag3d', 'resetCameraDefault3d', 'resetCameraLastSave3d', 'hoverClosest3d'])





    fig.update_traces(
        hoverlabel=dict(
            font=dict(
                size=16  # Adjust the font size to your desired value
            ),
            namelength=-1  # This will allow the hover labels to stretch out horizontally
        )
    )

    fig.show()

    # Save the plot as an HTML file and open it in the browser
    fig.write_html('plane.html', auto_open=False)
    blob = bucket.blob('plane.html')
    blob.upload_from_filename(r"plane.html")


main(1, "12/17/2023")
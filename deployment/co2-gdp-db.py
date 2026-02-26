import os
import requests
import tempfile
import zipfile
import streamlit as st
import numpy as np
import pandas as pd
import geopandas as gpd
import plotly.express as px
import plotly.graph_objects as go

# Page config
st.set_page_config(
    page_title="CO2 GDP Dashboard",
    page_icon="🌍",
    layout="wide"
)

url_co2gdp_data = 'https://drive.switch.ch/index.php/s/cxW0xrmQXdGL1VJ/download'
url_geo_data = 'https://drive.switch.ch/index.php/s/bfb1TrwoIrXGAfM/download'

# Custom CSS
st.markdown("""
<style>
    h1.main-header {
        color: #3366cc;
        text-align: left;
        font-size: 2.5em;
    }
    h2.section-header {
        color: #3366cc;
        font-size: 1.8em;
        margin-top: 1em;
    }
    h3.subsection-header {
        font-size: 1.2em;
        color: #3366cc;
        margin-top: 0.5em;
    }
    p.description-header {
            font-size: 1.2em;
            font-weight: bold;
            color: #333333;
            margin-top: 0.5em;
            margin-bottom: 0.5em;}
    .metric-container {
        background-color: #f8f8f8;
        padding: 10px;
        border-radius: 5px;
        border-left: 4px solid #000000;
    }
</style>
""", unsafe_allow_html=True)

# Title
st.markdown("<h1 class='main-header'>Sample Dashboard on the CO2 Emissions Dataset</h1>", unsafe_allow_html=True)

# download the data
@st.cache_data
def load_data():
    try:
        return pd.read_csv(url_co2gdp_data) #, sep=';'
    except Exception as e:
        st.error(f"Error retrieving dataset: {e}")
        # Create a sample dataframe for demonstration if file is not found
        sample_df = pd.DataFrame({
            'country': ['United States', 'China', 'India', 'Germany', 'Brazil'],
            'region': ['North America', 'Asia', 'Asia', 'Europe', 'South America'],
            'year': [2000, 2000, 2000, 2000, 2000],
            'co2': [20.2, 2.7, 0.9, 10.1, 1.9],
            'gdp': [36330, 959, 452, 23635, 3739]
        })
        return sample_df  

df = load_data()

# Try to load geo data
@st.cache_data
def load_geo_data():
    try:
        # Create a temporary directory to store the downloaded and extracted files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download the zip file
            response = requests.get(url_geo_data)
            
            if response.status_code != 200:
                raise Exception(f"Failed to download: Status code {response.status_code}")
            
            # Save the zip file to the temporary directory
            zip_path = os.path.join(temp_dir, "geo_data.zip")
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            # Extract the zip file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Find the .shp file in the extracted contents
            shapefile_path = None
            for root, dirs, files in os.walk(temp_dir):
                for file in files:
                    if file.endswith(".shp"):
                        shapefile_path = os.path.join(root, file)
                        break
                if shapefile_path:
                    break
            
            if not shapefile_path:
                raise Exception("No .shp file found in the downloaded zip.")
            
            # Load the shapefile with GeoPandas
            world = gpd.read_file(shapefile_path)
            
            # Rename the country column if needed
            if 'NAME' in world.columns:
                world = world.rename(columns={'NAME': 'country'})
            elif 'name' in world.columns:
                world = world.rename(columns={'name': 'country'})
            
            return world
            
    except Exception as e:
        st.error(f"Error retrieving geographic data: {e}")
        st.warning("Geographic data not found. Choropleth maps will not be available.")
        return None


world_geo = load_geo_data()
has_geo_data = world_geo is not None

# --------------------------------------
# Dataset Overview Section
# --------------------------------------
st.markdown("<h2 class='section-header'>Dataset Overview</h2>", unsafe_allow_html=True)

# Column information
column_types = pd.DataFrame({
    'Column': df.columns,
    'Data Type': [str(df[col].dtype) for col in df.columns]
})
st.dataframe(column_types, width='stretch', hide_index=True)

# Basic info about the dataset
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Number of Rows", f"{len(df):,}")
with col2:
    year_min, year_max = df['year'].min(), df['year'].max()
    st.metric("Year Range", f"{year_min} - {year_max}")
with col3:
    st.metric("Number of Countries", f"{df['country'].nunique():,}")

# --------------------------------------
# Univariate Analysis: CO2
# --------------------------------------
st.markdown("<h2 class='section-header'>Univariate Analysis: CO2</h2>", unsafe_allow_html=True)

# CO2 distribution
col1, col2 = st.columns([1, 2])

with col1:
    # CO2 Boxplot

    fig = px.box(df, y="co2")

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )   
    fig.update_traces(boxpoints='suspectedoutliers') # Only show points that might be outliers
    st.plotly_chart(fig, width='stretch')

with col2:
    # GDP Histogram
    fig = px.histogram(df, x="co2")
    
    st.plotly_chart(fig, width='stretch')

# CO2 Extremes
co2_min_idx = df['co2'].idxmin()
co2_max_idx = df['co2'].idxmax()
co2_extremes = df.loc[[co2_min_idx, co2_max_idx]].copy()
co2_extremes['type'] = ['Minimum CO2', 'Maximum CO2']

st.markdown("<h3 class='subsection-header'>CO2 Extremes</h3>", unsafe_allow_html=True)
st.dataframe(co2_extremes[['type', 'country', 'region', 'year', 'co2', 'gdp']], width='stretch',hide_index=True)


# --------------------------------------
# Univariate Analysis: GDP
# --------------------------------------
st.markdown("<h2 class='section-header'>Univariate Analysis: GDP</h2>", unsafe_allow_html=True)

# GDP distribution
col1, col2 = st.columns([1, 2])

with col1:
    # GDP Boxplot

    fig = px.box(df, y="gdp")

    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=16,
            font_family="Rockwell"
        )
    )   
    
    st.plotly_chart(fig, width='stretch')

with col2:
    # GDP Histogram
    fig = px.histogram(df, x="gdp")
    
    st.plotly_chart(fig, width='stretch')

# GDP Extremes
gdp_min_idx = df['gdp'].idxmin()
gdp_max_idx = df['gdp'].idxmax()
gdp_extremes = df.loc[[gdp_min_idx, gdp_max_idx]].copy()
gdp_extremes['type'] = ['Minimum GDP', 'Maximum GDP']

st.markdown("<h3 class='subsection-header'>GDP Extremes</h3>", unsafe_allow_html=True)
st.dataframe(gdp_extremes[['type', 'country', 'region', 'year', 'gdp', 'co2']], width='stretch', hide_index=True)


# --------------------------------------
# Development Section
# --------------------------------------
st.markdown("<h2 class='section-header'>Development of CO2 and GDP over Time by Country</h2>", unsafe_allow_html=True)

# Get all unique countries
all_countries = sorted(df['country'].unique().tolist())
years = sorted(df['year'].unique().tolist())
min_year, max_year = min(years), max(years)

selected_countries = st.multiselect(
        "Select Countries to Highlight:",
        options=all_countries,
        default=[]
)

# Function to generate line plot data
def prepare_line_data():
    # Dictionary to store data for each country
    country_data = {}
    
    # Generate 10 distinct colors for highlighting
    colors = px.colors.qualitative.D3[:10]
    
    # Process each country
    for country in all_countries:
        country_df = df[df['country'] == country].sort_values('year')
        
        # If data exists for this country
        if len(country_df) > 0:
            # Get a color if this is a selected country
            color = None
            if country in selected_countries:
                color_idx = selected_countries.index(country) % len(colors)
                color = colors[color_idx]
            
            country_data[country] = {
                'years': country_df['year'].tolist(),
                'co2': country_df['co2'].tolist(),
                'gdp': country_df['gdp'].tolist(),
                'color': color,
                'highlight': country in selected_countries
            }
    
    return country_data

# Function to generate slope graph data
def prepare_slope_data(start_year, end_year):
    slope_data = {'co2': [], 'gdp': []}
    
    # Generate 10 distinct colors for highlighting
    colors = px.colors.qualitative.D3[:10]
    
    # Process each country
    for country in all_countries:
        # Get data for start and end years
        start_data = df[(df['country'] == country) & (df['year'] == start_year)]
        end_data = df[(df['country'] == country) & (df['year'] == end_year)]
        
        # If data exists for both years
        if len(start_data) > 0 and len(end_data) > 0:
            # Get values for CO2
            co2_start = start_data['co2'].values[0]
            co2_end = end_data['co2'].values[0]
            
            # Get values for GDP
            gdp_start = start_data['gdp'].values[0]
            gdp_end = end_data['gdp'].values[0]
            
            # Check if values are valid for log scale
            if co2_start > 0 and co2_end > 0 and not np.isnan(co2_start) and not np.isnan(co2_end):
                # Get a color if this is a selected country
                color = 'gray'
                if country in selected_countries:
                    color_idx = selected_countries.index(country) % len(colors)
                    color = colors[color_idx]
                
                slope_data['co2'].append({
                    'country': country,
                    'start_val': co2_start,
                    'end_val': co2_end,
                    'pct_change': ((co2_end - co2_start) / co2_start) * 100 if co2_start > 0 else 0,
                    'abs_change': co2_end - co2_start,
                    'color': color,
                    'highlight': country in selected_countries
                })
            
            # Check if values are valid for log scale
            if gdp_start > 0 and gdp_end > 0 and not np.isnan(gdp_start) and not np.isnan(gdp_end):
                # Get a color if this is a selected country
                color = 'gray'
                if country in selected_countries:
                    color_idx = selected_countries.index(country) % len(colors)
                    color = colors[color_idx]
                
                slope_data['gdp'].append({
                    'country': country,
                    'start_val': gdp_start,
                    'end_val': gdp_end,
                    'pct_change': ((gdp_end - gdp_start) / gdp_start) * 100 if gdp_start > 0 else 0,
                    'abs_change': gdp_end - gdp_start,
                    'color': color,
                    'highlight': country in selected_countries
                })
    
    return slope_data

# Function to find extremes in slope data
def find_extremes(slope_data):
    if not slope_data:
        return None, None
    
    # Sort by percentage change
    sorted_data = sorted(slope_data, key=lambda x: x['pct_change'])
    
    if len(sorted_data) > 0:
        largest_decrease = sorted_data[0]
        largest_increase = sorted_data[-1]
        return largest_decrease, largest_increase
    
    return None, None

# Generate data
line_data = prepare_line_data()

# --------------------------------------
# Line Charts for CO2 and GDP over time
# --------------------------------------
# Create time series charts for CO2 and GDP

# CO2 over time
fig_co2_time = go.Figure()

# Add grey lines for all countries
for country, data in line_data.items():
    if not data['highlight']:
        fig_co2_time.add_trace(go.Scatter(
            x=data['years'],
            y=data['co2'],
            mode='lines',
            name=country,
            line=dict(color='gray', width=1),
            opacity=0.1,
            showlegend=False
        ))
    
# Add colored lines for selected countries with labels at the end
for country, data in line_data.items():
    if data['highlight']:
        # Add label at the end of the line
        last_idx = len(data['years']) - 1
        text = [None] * len(data['years'])
        text[last_idx] = country
        
        fig_co2_time.add_trace(go.Scatter(
            x=data['years'],
            y=data['co2'],
            mode='lines+markers+text',
            name=country,
            text=text,
            textposition='middle right',
            textfont=dict(color=data['color']),
            line=dict(color=data['color'], width=3),
            marker=dict(color=data['color'], size=6)
        ))

# Set x-axis range to start from the first year in the dataset
fig_co2_time.update_layout(
    # title="CO2 Emissions Over Time",
    xaxis_title="Year",
    yaxis_title="CO2 Emissions (metric tons per capita)",
    showlegend=False,
    height=500,
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(range=[min_year-0.2, max_year + 5])  # Add some padding to the right for labels
)

st.plotly_chart(fig_co2_time, width='stretch')

# GDP over time
fig_gdp_time = go.Figure()

# Add grey lines for all countries
for country, data in line_data.items():
    if not data['highlight']:
        fig_gdp_time.add_trace(go.Scatter(
            x=data['years'],
            y=data['gdp'],
            mode='lines',
            name=country,
            line=dict(color='gray', width=1),
            opacity=0.1,
            showlegend=False
        ))

# Add colored lines for selected countries with labels at the end
for country, data in line_data.items():
    if data['highlight']:
        # Add label at the end of the line
        last_idx = len(data['years']) - 1
        text = [None] * len(data['years'])
        text[last_idx] = country
        
        fig_gdp_time.add_trace(go.Scatter(
            x=data['years'],
            y=data['gdp'],
            mode='lines+markers+text',
            name=country,
            text=text,
            textposition='middle right',
            textfont=dict(color=data['color']),
            line=dict(color=data['color'], width=3),
            marker=dict(color=data['color'], size=6)
        ))

# Set x-axis range to start from the first year in the dataset
fig_gdp_time.update_layout(
    # title="GDP Over Time",
    xaxis_title="Year",
    yaxis_title="GDP (USD per capita)",
    showlegend=False,
    height=500,
    margin=dict(l=40, r=40, t=50, b=40),
    xaxis=dict(range=[min_year-0.2, max_year + 5])  # Add some padding to the right for labels
)

st.plotly_chart(fig_gdp_time, width='stretch')

# --------------------------------------
# Slopegraphs
# --------------------------------------

col_sliders_1, col_sliders_2 = st.columns(2)
with col_sliders_1:
    start_year = st.slider(
        "Start Year",
        min_value=min_year,
        max_value=max_year-1,
        value=min_year
    )
with col_sliders_2:
    end_year = st.slider(
        "End Year",
        min_value=min_year+1,
        max_value=max_year,
        value=max_year
    )

# Make sure end year > start year
if end_year < start_year:
    bla = end_year
    end_year = start_year 
    start_year = bla

slope_data = prepare_slope_data(start_year, end_year)

col1, col2 = st.columns(2)

with col1:
    # CO2 Slopegraph
    fig_co2_slope = go.Figure()
    
    # Add grey lines for non-selected countries
    for item in slope_data['co2']:
        if not item['highlight']:
            fig_co2_slope.add_trace(go.Scatter(
                x=[0, 1],
                y=[item['start_val'], item['end_val']],
                mode='lines',
                name=item['country'],
                line=dict(color='gray', width=1),
                opacity=0.1,
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add colored lines for selected countries
    for item in slope_data['co2']:
        if item['highlight']:
            fig_co2_slope.add_trace(go.Scatter(
                x=[0, 1],
                y=[item['start_val'], item['end_val']],
                mode='lines+markers+text',
                name=item['country'],
                line=dict(color=item['color'], width=3),
                marker=dict(color=item['color'], size=10),
                text=[item['country'], item['country']],
                textposition=['middle left', 'middle right'],
                hovertemplate=f"{item['country']}<br>" +
                              f"Start: {item['start_val']:.2f}<br>" +
                              f"End: {item['end_val']:.2f}<br>" +
                              f"Change: {item['abs_change']:.2f} ({item['pct_change']:.1f}%)"
            ))
    
    fig_co2_slope.update_layout(
        title=f"CO2 Emissions Change from {start_year} to {end_year}",
        yaxis_type="log",
        yaxis_title="CO2 Emissions (metric tons per capita)",
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=[str(start_year), str(end_year)],
            range=[-0.2, 1.2]
        ),
        height=500,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=False
    )
    
    st.plotly_chart(fig_co2_slope, width='stretch')
    
    # Show largest changes
    co2_decrease, co2_increase = find_extremes(slope_data['co2'])
    
    if co2_decrease and co2_increase:
        st.markdown(f"""
        <div class='metric-container'>
        <p class='description-header'>Largest CO2 Increase from {start_year} to {end_year}:<p>
        <p><b>{co2_increase['country']}</b>: {co2_increase['start_val']:.2f} to {co2_increase['end_val']:.2f} metric tons per capita<br>
        Change: {'+' if co2_increase['abs_change'] > 0 else ''}{co2_increase['abs_change']:.2f} ({'+' if co2_increase['pct_change'] > 0 else ''}{co2_increase['pct_change']:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class='metric-container'>
        <p class='description-header'>Largest CO2 Decrease from {start_year} to {end_year}:<p>
        <p><b>{co2_decrease['country']}</b>: {co2_decrease['start_val']:.2f} to {co2_decrease['end_val']:.2f} metric tons per capita<br>
        Change: {'+' if co2_decrease['abs_change'] > 0 else ''}{co2_decrease['abs_change']:.2f} ({'+' if co2_decrease['pct_change'] > 0 else ''}{co2_decrease['pct_change']:.1f}%)</p>
        </div>
        """, unsafe_allow_html=True)
            

with col2:
    # GDP Slopegraph
    fig_gdp_slope = go.Figure()
    
    # Add grey lines for non-selected countries
    for item in slope_data['gdp']:
        if not item['highlight']:
            fig_gdp_slope.add_trace(go.Scatter(
                x=[0, 1],
                y=[item['start_val'], item['end_val']],
                mode='lines',
                name=item['country'],
                line=dict(color='gray', width=1),
                opacity=0.1,
                showlegend=False,
                hoverinfo='skip'
            ))
    
    # Add colored lines for selected countries
    for item in slope_data['gdp']:
        if item['highlight']:
            fig_gdp_slope.add_trace(go.Scatter(
                x=[0, 1],
                y=[item['start_val'], item['end_val']],
                mode='lines+markers+text',
                name=item['country'],
                line=dict(color=item['color'], width=3),
                marker=dict(color=item['color'], size=10),
                text=[item['country'], item['country']],
                textposition=['middle left', 'middle right'],
                hovertemplate=f"{item['country']}<br>" +
                              f"Start: {item['start_val']:.2f}<br>" +
                              f"End: {item['end_val']:.2f}<br>" +
                              f"Change: {item['abs_change']:.2f} ({item['pct_change']:.1f}%)"
            ))
    
    fig_gdp_slope.update_layout(
        title=f"GDP Change from {start_year} to {end_year}",
        yaxis_type="log",
        yaxis_title="GDP (USD per capita)",
        xaxis=dict(
            tickmode='array',
            tickvals=[0, 1],
            ticktext=[str(start_year), str(end_year)],
            range=[-0.2, 1.2]
        ),
        height=500,
        margin=dict(l=40, r=40, t=50, b=40),
        showlegend=False
    )
    
    st.plotly_chart(fig_gdp_slope, width='stretch')
    
    # Show largest changes
    gdp_decrease, gdp_increase = find_extremes(slope_data['gdp'])
    
    if gdp_decrease and gdp_increase:

        st.markdown(f"""
            <div class='metric-container'>
            <p class='description-header'>Largest GDP Increase from {start_year} to {end_year}:<p>
            <p><b>{gdp_increase['country']}</b>: {gdp_increase['start_val']:.2f} to {gdp_increase['end_val']:.2f} USD<br>
            Change: {'+' if gdp_increase['abs_change'] > 0 else ''}{gdp_increase['abs_change']:.2f} ({'+' if gdp_increase['pct_change'] > 0 else ''}{gdp_increase['pct_change']:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class='metric-container'>
            <p class='description-header'>Largest GDP Decrease from {start_year} to {end_year}:<p>
            <p><b>{gdp_decrease['country']}</b>: {gdp_decrease['start_val']:.2f} to {gdp_decrease['end_val']:.2f} USD<br>
            Change: {'+' if gdp_decrease['abs_change'] > 0 else ''}{gdp_decrease['abs_change']:.2f} ({'+' if gdp_decrease['pct_change'] > 0 else ''}{gdp_decrease['pct_change']:.1f}%)</p>
            </div>
            """, unsafe_allow_html=True)
            

# --------------------------------------
# By Year Section
# --------------------------------------
st.markdown("<h2 class='section-header'>CO2 Emissions and GDP by Year</h2>", unsafe_allow_html=True)

# Year selection
selected_year = st.slider(
    "Select Year",
    min_value=min_year,
    max_value=max_year,
    value=min_year
)


# Filter data for the selected year
year_data = df[df['year'] == selected_year]

# --------------------------------------
# Scatter Plot
# --------------------------------------
st.subheader(f"GDP vs CO2 Emissions by Country in {selected_year}")

# Get the color sequence from plotly express for consistency
region_colors = {}
for i, region in enumerate(sorted(df['region'].unique())):
    region_colors[region] = px.colors.qualitative.Plotly[i % len(px.colors.qualitative.Plotly)]

# Create scatter plot
fig_scatter = px.scatter(
    year_data,
    x="gdp",
    y="co2",
    color="region",
    hover_name="country",
    log_y=True,
    size=[15] * len(year_data),  # Set uniform size for all points (increased)
    size_max=15,  # Increase maximum size
    height=600,
    color_discrete_map=region_colors,  # Use consistent colors
    labels={"co2": "CO2 Emissions (metric tons per capita)", 
            "gdp": "GDP (USD per capita)",
            "region": "Region"}
)

fig_scatter.update_layout(
    legend=dict(
        title="Region",
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="center",
        x=0.5
    )
)

st.plotly_chart(fig_scatter, width='stretch')

# --------------------------------------
# Choropleth Map (if geo data available)
# --------------------------------------
# Metric selection for choropleth
metric_options = ["CO2 Emissions", "GDP"]
selected_metric_idx = 0  # Default to CO2
if has_geo_data:
    col1, col2 = st.columns([1, 3])
    with col1:
        selected_metric_idx = st.radio(
            "Select Choropleth Metric:",
            options=range(len(metric_options)),
            format_func=lambda x: metric_options[x]
        )

if has_geo_data:
    # Prepare data
    selected_metric = "co2" if selected_metric_idx == 0 else "gdp"
    metric_name = metric_options[selected_metric_idx]
    
    # Merge GeoJSON with data
    gdf = world_geo.copy()
    metric_values = {}
    
    for idx, row in year_data.iterrows():
        # Get value based on selected metric
        value = row[selected_metric]
        metric_values[row['country']] = max(value, 0.01)  # Ensure positive value for log scale
    
    # Merge data with GeoJSON
    gdf['value'] = gdf['country'].map(metric_values).fillna(0)
    
    # Apply log transformation for better visualization of small values
    gdf['log_value'] = np.log10(gdf['value'].clip(lower=0.01))  # Clip to avoid log(0)
    
    # Get color scale range
    min_log_val = np.log10(0.01)
    max_log_val = np.log10(max(year_data[selected_metric].max(), 0.02))
    
    # Choropleth with Plotly
    fig_choropleth = px.choropleth(
        gdf,
        geojson=gdf.geometry,
        locations=gdf.index,
        color='log_value',  # Use log-transformed values
        hover_name='country',
        color_continuous_scale="Reds", 
        range_color=(min_log_val, max_log_val),
        labels={'log_value': metric_name},
        # title=f"{metric_name} by Country in {selected_year} (Log Scale)"
    )
    
    # Custom hover template to show original values, not log values
    fig_choropleth.update_traces(
        hovertemplate='<b>%{hovertext}</b><br>' +
                     f'{metric_name}: ' + '%{customdata:.2f}<extra></extra>',
        customdata=gdf['value']
    )
    
    fig_choropleth.update_layout(
        height=600,
        margin={"r":0,"t":30,"l":0,"b":0},
        coloraxis_colorbar=dict(
            title=f"{metric_name} (Log Scale)",
            # Create tick values in log space but display as original values
            tickvals=[np.log10(val) for val in [0.01, 0.1, 1, 10, 100]],
            ticktext=["0.01", "0.1", "1", "10", "100"],
            len=0.5
        )
    )

    fig_choropleth.update_geos(
        showcoastlines=True,
        coastlinecolor="Black",
        showland=True,
        landcolor="white",
        showocean=True,
        oceancolor="lightblue",
        projection_type="equirectangular",
        fitbounds="locations",  # Fit to data locations
        visible=True,
        showcountries=True,
        countrycolor="gray",
        showframe=False,  # Remove frame
        framewidth=0  # Ensure no frame width
    )
    
    st.plotly_chart(fig_choropleth, width='stretch')


# --------------------------------------
# Regional Bar Charts
# --------------------------------------
st.subheader(f"Regional Averages in {selected_year}")

# Calculate regional averages
region_data = {}
for region in df['region'].unique():
    region_rows = year_data[year_data['region'] == region]
    if len(region_rows) > 0:
        region_data[region] = {
            'co2': region_rows['co2'].mean(),
            'gdp': region_rows['gdp'].mean()
        }
    else:
        region_data[region] = {
            'co2': 0,
            'gdp': 0
        }

# Convert to DataFrame for plotting
region_df = pd.DataFrame([
    {'region': region, 'metric': 'co2', 'value': data['co2']} 
    for region, data in region_data.items()
] + [
    {'region': region, 'metric': 'gdp', 'value': data['gdp']} 
    for region, data in region_data.items()
])

# Create separate dataframes for CO2 and GDP, sorted by descending values
region_co2_df = region_df[region_df['metric'] == 'co2'].sort_values(
    by='value', ascending=True)
region_gdp_df = region_df[region_df['metric'] == 'gdp'].sort_values(
    by='value', ascending=True)

# Get the order of regions for both metrics (for consistent y-axis)
co2_sorted_regions = region_co2_df['region'].tolist()
gdp_sorted_regions = region_gdp_df['region'].tolist()

col1, col2 = st.columns(2)

with col1:
    # CO2 bar chart with consistent colors from scatter plot
    fig_co2_region = px.bar(
        region_co2_df,
        x='value',
        y='region',
        orientation='h',
        labels={'value': 'CO2 Emissions (metric tons per capita)', 'region': 'Region'},
        title=f"Average CO2 Emissions by Region in {selected_year}",
        color='region',
        color_discrete_map=region_colors,  # Use same colors as scatter plot
        height=400
    )
    
    fig_co2_region.update_layout(
        showlegend=False,
        xaxis_title="CO2 Emissions (Average in metric tons per capita)",
        yaxis_title="",
        yaxis={'categoryorder': 'array', 'categoryarray': co2_sorted_regions}  # Order by descending CO2 value
    )
    
    st.plotly_chart(fig_co2_region, width='stretch')

with col2:
    # GDP bar chart with consistent colors from scatter plot
    fig_gdp_region = px.bar(
        region_gdp_df,
        x='value',
        y='region',
        orientation='h',
        labels={'value': 'GDP (USD per capita)', 'region': 'Region'},
        title=f"Average GDP by Region in {selected_year}",
        color='region',
        color_discrete_map=region_colors,  # Use same colors as scatter plot
        height=400
    )
    
    fig_gdp_region.update_layout(
        showlegend=False,
        xaxis_title="GDP (Average in USD per capita)",
        yaxis_title="",
        yaxis={'categoryorder': 'array', 'categoryarray': gdp_sorted_regions}  # Order by descending GDP value
    )
    
    st.plotly_chart(fig_gdp_region, width='stretch')


# --------------------------------------
# Additional Analysis Section
# --------------------------------------
st.markdown("<h2 class='section-header'>Correlation Over Time</h2>", unsafe_allow_html=True)

# Calculate correlation by year
correlation_data = []
for year in years:
    year_df = df[df['year'] == year]
    if len(year_df) > 10:  # Only calculate if we have enough data points
        corr = year_df['co2'].corr(year_df['gdp'])
        correlation_data.append({'year': year, 'correlation': corr})

correlation_df = pd.DataFrame(correlation_data)

# Plot correlation over time
fig_corr = px.line(
    correlation_df,
    x='year',
    y='correlation',
    labels={'correlation': 'Pearson Correlation', 'year': 'Year'},
    title="Correlation between CO2 Emissions and GDP Over Time",
    markers=True
)

fig_corr.update_layout(
    xaxis_title="Year",
    yaxis_title="Correlation Coefficient",
    yaxis=dict(
        range=[-0.1, 1.1],
        tickvals=[0, 0.2, 0.4, 0.6, 0.8, 1.0]
    )
)

st.plotly_chart(fig_corr, width='stretch')

# Add explanation
st.markdown("""
This chart shows how the correlation between CO2 emissions and GDP has changed over time. 
A correlation coefficient close to 1 indicates a strong positive relationship, suggesting that 
countries with higher GDP tend to have higher CO2 emissions per capita.
""")

# --------------------------------------
# Footer
# --------------------------------------
st.markdown("""
---
<p style="text-align: center;">CO2 Emissions and GDP Dashboard | Created with Streamlit</p>
""", unsafe_allow_html=True)
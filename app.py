"""
Hudson Valley Acupuncture Market Analysis Dashboard
====================================================
Interactive dashboard for exploring market opportunities in the Hudson Valley region.
"""

import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium import plugins
from streamlit_folium import st_folium
import plotly.express as px
import plotly.graph_objects as go
import json
from pathlib import Path
import base64

# Page configuration
st.set_page_config(
    page_title="Hudson Valley Acupuncture Market Analysis",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1E3A5F;
        margin-bottom: 0;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #666;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .tier-1 { background-color: #2E7D32; color: white; padding: 4px 12px; border-radius: 20px; }
    .tier-2 { background-color: #1976D2; color: white; padding: 4px 12px; border-radius: 20px; }
    .tier-3 { background-color: #F57C00; color: white; padding: 4px 12px; border-radius: 20px; }
    .tier-4 { background-color: #757575; color: white; padding: 4px 12px; border-radius: 20px; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f0f2f6;
        border-radius: 4px 4px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# Data Loading Functions
# -------------------------------------------------------------------

@st.cache_data
def load_geojson(filepath):
    """Load GeoJSON file and return as GeoDataFrame."""
    gdf = gpd.read_file(filepath)
    return gdf

@st.cache_data
def load_all_data():
    """Load all data files."""
    data_dir = Path(__file__).parent / "data"
    
    municipalities = load_geojson(data_dir / "municipalities.geojson")
    counties = load_geojson(data_dir / "counties.geojson")
    cities = load_geojson(data_dir / "cities.geojson")
    villages = load_geojson(data_dir / "villages.geojson")
    
    return municipalities, counties, cities, villages

def get_tier_color(tier):
    """Return color for market tier."""
    colors = {
        "Tier 1 - Prime": "#2E7D32",      # Green
        "Tier 2 - Strong": "#1976D2",      # Blue
        "Tier 3 - Moderate": "#F57C00",    # Orange
        "Tier 4 - Low": "#757575"          # Gray
    }
    return colors.get(tier, "#757575")

def get_opportunity_color(score):
    """Return color based on opportunity score."""
    if score >= 70:
        return "#2E7D32"  # Green
    elif score >= 50:
        return "#1976D2"  # Blue
    elif score >= 30:
        return "#F57C00"  # Orange
    else:
        return "#757575"  # Gray

# -------------------------------------------------------------------
# Map Creation Functions
# -------------------------------------------------------------------

def create_interactive_map(municipalities_gdf, counties_gdf, selected_counties, selected_tiers, selected_types, color_by):
    """Create an interactive Folium map with layers."""
    
    # Filter data
    filtered = municipalities_gdf.copy()
    
    if selected_counties:
        filtered = filtered[filtered['COUNTY'].isin(selected_counties)]
    if selected_tiers:
        filtered = filtered[filtered['MARKET_TIER'].isin(selected_tiers)]
    if selected_types:
        filtered = filtered[filtered['TYPE'].str.lower().isin([t.lower() for t in selected_types])]
    
    # Calculate map center
    if len(filtered) > 0:
        bounds = filtered.total_bounds  # [minx, miny, maxx, maxy]
        center_lat = (bounds[1] + bounds[3]) / 2
        center_lon = (bounds[0] + bounds[2]) / 2
    else:
        center_lat, center_lon = 41.5, -73.9
    
    # Create base map
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=8,
        tiles=None
    )
    
    # Add tile layers
    folium.TileLayer(
        tiles='cartodbpositron',
        name='Light Basemap',
        control=True
    ).add_to(m)
    
    folium.TileLayer(
        tiles='cartodbdark_matter',
        name='Dark Basemap',
        control=True
    ).add_to(m)
    
    # Add county boundaries (subtle)
    county_style = {
        'fillColor': 'transparent',
        'color': '#333',
        'weight': 2,
        'fillOpacity': 0,
        'dashArray': '5, 5'
    }
    
    folium.GeoJson(
        counties_gdf,
        name='County Boundaries',
        style_function=lambda x: county_style,
        tooltip=folium.GeoJsonTooltip(
            fields=['NAME'],
            aliases=['County:'],
            style='font-size: 12px;'
        )
    ).add_to(m)
    
    # Add municipalities with styling based on selected metric
    def style_function(feature):
        props = feature['properties']
        
        if color_by == "Market Tier":
            fill_color = get_tier_color(props.get('MARKET_TIER', ''))
        else:  # Opportunity Score
            fill_color = get_opportunity_color(props.get('OPPORTUNITY_SCORE', 0))
        
        return {
            'fillColor': fill_color,
            'color': '#333',
            'weight': 1,
            'fillOpacity': 0.7
        }
    
    def highlight_function(feature):
        return {
            'fillColor': '#FFD700',
            'color': '#000',
            'weight': 3,
            'fillOpacity': 0.9
        }
    
    # Create popup content
    def create_popup(row):
        tier_class = row['MARKET_TIER'].lower().replace(' ', '-').replace('-', '-')
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 280px;">
            <h4 style="margin: 0 0 10px 0; color: #1E3A5F; border-bottom: 2px solid #667eea;">
                {row['NAME']}
            </h4>
            <table style="width: 100%; font-size: 13px;">
                <tr>
                    <td style="padding: 4px 0;"><strong>Type:</strong></td>
                    <td style="padding: 4px 0;">{row['TYPE'].title()}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>County:</strong></td>
                    <td style="padding: 4px 0;">{row['COUNTY']}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Population:</strong></td>
                    <td style="padding: 4px 0;">{row['POPULATION']:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Median Income:</strong></td>
                    <td style="padding: 4px 0;">${row['MEDIAN_INCOME']:,.0f}</td>
                </tr>
                <tr style="background-color: #f5f5f5;">
                    <td style="padding: 6px 0;"><strong>Opportunity Score:</strong></td>
                    <td style="padding: 6px 0; font-size: 16px; font-weight: bold; color: {get_opportunity_color(row['OPPORTUNITY_SCORE'])};">
                        {row['OPPORTUNITY_SCORE']:.1f}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Opportunity Rank:</strong></td>
                    <td style="padding: 4px 0;">#{int(row['OPPORTUNITY_RANK'])}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Market Index:</strong></td>
                    <td style="padding: 4px 0;">{row['ACUP_INDEX']:.1f}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Market Size:</strong></td>
                    <td style="padding: 4px 0;">{row['MARKET_SIZE']:,.0f}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>Market Tier:</strong></td>
                    <td style="padding: 4px 0;">
                        <span style="background-color: {get_tier_color(row['MARKET_TIER'])}; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px;">
                            {row['MARKET_TIER']}
                        </span>
                    </td>
                </tr>
                <tr>
                    <td style="padding: 4px 0;"><strong>LifeMode:</strong></td>
                    <td style="padding: 4px 0;">{row['LIFEMODE']}</td>
                </tr>
            </table>
        </div>
        """
        return popup_html
    
    # Add filtered municipalities
    if len(filtered) > 0:
        for idx, row in filtered.iterrows():
            popup = folium.Popup(create_popup(row), max_width=300)
            
            folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=lambda x, r=row: {
                    'fillColor': get_tier_color(r['MARKET_TIER']) if color_by == "Market Tier" else get_opportunity_color(r['OPPORTUNITY_SCORE']),
                    'color': '#333',
                    'weight': 1,
                    'fillOpacity': 0.7
                },
                highlight_function=highlight_function,
                popup=popup,
                tooltip=f"{row['NAME']} - Score: {row['OPPORTUNITY_SCORE']:.1f}"
            ).add_to(m)
    
    # Add layer control
    folium.LayerControl().add_to(m)
    
    # Add legend
    legend_html = """
    <div style="position: fixed; bottom: 50px; left: 50px; z-index: 1000;
                background-color: white; padding: 15px; border-radius: 8px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.3); font-family: Arial, sans-serif;">
        <h4 style="margin: 0 0 10px 0; font-size: 14px; color: #333;">Market Tiers</h4>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background: #2E7D32; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border-radius: 3px;"></span>
            <span style="font-size: 12px; color: #333;">Tier 1 - Prime (70+)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background: #1976D2; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border-radius: 3px;"></span>
            <span style="font-size: 12px; color: #333;">Tier 2 - Strong (50-69)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background: #F57C00; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border-radius: 3px;"></span>
            <span style="font-size: 12px; color: #333;">Tier 3 - Moderate (30-49)</span>
        </div>
        <div style="display: flex; align-items: center; margin: 5px 0;">
            <span style="background: #757575; width: 20px; height: 20px; display: inline-block; margin-right: 8px; border-radius: 3px;"></span>
            <span style="font-size: 12px; color: #333;">Tier 4 - Low (&lt;30)</span>
        </div>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    
    return m, filtered

# -------------------------------------------------------------------
# Chart Functions
# -------------------------------------------------------------------

def create_tier_distribution_chart(df):
    """Create a donut chart showing tier distribution."""
    tier_counts = df['MARKET_TIER'].value_counts().reset_index()
    tier_counts.columns = ['Tier', 'Count']
    
    colors = ['#2E7D32', '#1976D2', '#F57C00', '#757575']
    
    fig = px.pie(
        tier_counts, 
        values='Count', 
        names='Tier',
        hole=0.4,
        color='Tier',
        color_discrete_map={
            'Tier 1 - Prime': '#2E7D32',
            'Tier 2 - Strong': '#1976D2',
            'Tier 3 - Moderate': '#F57C00',
            'Tier 4 - Low': '#757575'
        }
    )
    fig.update_layout(
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2),
        margin=dict(t=20, b=20, l=20, r=20),
        height=300
    )
    return fig

def create_county_comparison_chart(df):
    """Create bar chart comparing counties by market size."""
    county_data = df.groupby('COUNTY').agg({
        'MARKET_SIZE': 'sum',
        'POPULATION': 'sum',
        'OPPORTUNITY_SCORE': 'mean'
    }).reset_index()
    county_data = county_data.sort_values('MARKET_SIZE', ascending=True)
    
    fig = px.bar(
        county_data,
        y='COUNTY',
        x='MARKET_SIZE',
        orientation='h',
        color='OPPORTUNITY_SCORE',
        color_continuous_scale='Viridis',
        labels={'MARKET_SIZE': 'Total Market Size', 'COUNTY': 'County', 'OPPORTUNITY_SCORE': 'Avg Score'}
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
        coloraxis_colorbar=dict(title="Avg<br>Score")
    )
    return fig

def create_scatter_plot(df):
    """Create scatter plot of Population vs Opportunity Score."""
    fig = px.scatter(
        df,
        x='POPULATION',
        y='OPPORTUNITY_SCORE',
        size='MARKET_SIZE',
        color='MARKET_TIER',
        hover_name='NAME',
        hover_data=['COUNTY', 'MEDIAN_INCOME', 'ACUP_INDEX'],
        color_discrete_map={
            'Tier 1 - Prime': '#2E7D32',
            'Tier 2 - Strong': '#1976D2',
            'Tier 3 - Moderate': '#F57C00',
            'Tier 4 - Low': '#757575'
        },
        labels={
            'POPULATION': 'Population',
            'OPPORTUNITY_SCORE': 'Opportunity Score',
            'MARKET_SIZE': 'Market Size'
        }
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3)
    )
    fig.update_xaxes(type="log", title="Population (log scale)")
    return fig

def create_top_opportunities_chart(df, n=15):
    """Create horizontal bar chart of top opportunities."""
    top_n = df.nsmallest(n, 'OPPORTUNITY_RANK')
    top_n = top_n.sort_values('OPPORTUNITY_SCORE', ascending=True)
    
    fig = px.bar(
        top_n,
        y='NAME',
        x='OPPORTUNITY_SCORE',
        orientation='h',
        color='MARKET_TIER',
        color_discrete_map={
            'Tier 1 - Prime': '#2E7D32',
            'Tier 2 - Strong': '#1976D2',
            'Tier 3 - Moderate': '#F57C00',
            'Tier 4 - Low': '#757575'
        },
        hover_data=['COUNTY', 'POPULATION', 'MEDIAN_INCOME'],
        labels={'OPPORTUNITY_SCORE': 'Opportunity Score', 'NAME': 'Municipality'}
    )
    fig.update_layout(
        margin=dict(t=20, b=20, l=20, r=20),
        height=500,
        showlegend=False
    )
    return fig

# -------------------------------------------------------------------
# Main App
# -------------------------------------------------------------------

def main():
    # Load data
    municipalities, counties, cities, villages = load_all_data()
    
    # Header
    st.title("🎯 Hudson Valley Acupuncture Market Analysis")
    st.caption("Interactive Dashboard • NYC to Albany Corridor • 10 Counties • 113 Municipalities")
    st.markdown("---")
    
    # Sidebar filters
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/acupuncture.png", width=80)
        st.markdown("## 🔍 Filters")
        
        # County filter
        all_counties = sorted(municipalities['COUNTY'].unique().tolist())
        selected_counties = st.multiselect(
            "Select Counties",
            options=all_counties,
            default=[],
            help="Leave empty to show all counties"
        )
        
        # Tier filter
        all_tiers = ["Tier 1 - Prime", "Tier 2 - Strong", "Tier 3 - Moderate", "Tier 4 - Low"]
        selected_tiers = st.multiselect(
            "Select Market Tiers",
            options=all_tiers,
            default=[],
            help="Leave empty to show all tiers"
        )
        
        # Type filter
        selected_types = st.multiselect(
            "Select Municipality Type",
            options=["City", "Village"],
            default=[],
            help="Leave empty to show both"
        )
        
        st.markdown("---")
        
        # Map settings
        st.markdown("## 🗺️ Map Settings")
        color_by = st.radio(
            "Color by:",
            options=["Market Tier", "Opportunity Score"],
            index=0
        )
        
        st.markdown("---")
        
        # Quick stats
        st.markdown("## 📊 Quick Stats")
        st.metric("Total Municipalities", len(municipalities))
        st.metric("Total Population", f"{municipalities['POPULATION'].sum():,.0f}")
        st.metric("Avg Opportunity Score", f"{municipalities['OPPORTUNITY_SCORE'].mean():.1f}")
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Interactive Map", 
        "📊 Analytics", 
        "📋 Data Explorer",
        "📈 Top Opportunities",
        "📄 Full Report"
    ])
    
    # -------------------------------------------------------------------
    # TAB 1: Interactive Map
    # -------------------------------------------------------------------
    with tab1:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create and display map
            m, filtered_data = create_interactive_map(
                municipalities, counties, 
                selected_counties, selected_tiers, selected_types, color_by
            )
            
            st_folium(m, width=None, height=600, returned_objects=[])
        
        with col2:
            st.markdown("### 📍 Filtered Results")
            st.metric("Showing", f"{len(filtered_data)} municipalities")
            
            if len(filtered_data) > 0:
                st.metric("Combined Population", f"{filtered_data['POPULATION'].sum():,.0f}")
                st.metric("Avg Score", f"{filtered_data['OPPORTUNITY_SCORE'].mean():.1f}")
                
                st.markdown("---")
                st.markdown("### 🏆 Top 5 in Selection")
                top5 = filtered_data.nsmallest(5, 'OPPORTUNITY_RANK')[['NAME', 'OPPORTUNITY_SCORE', 'MARKET_TIER']]
                for _, row in top5.iterrows():
                    tier_color = get_tier_color(row['MARKET_TIER'])
                    st.markdown(f"""
                    <div style="padding: 8px; margin: 4px 0; background: #f8f9fa; border-radius: 6px; border-left: 4px solid {tier_color};">
                        <strong style="color: #333;">{row['NAME']}</strong><br>
                        <span style="color: {tier_color}; font-weight: bold;">{row['OPPORTUNITY_SCORE']:.1f}</span>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 💡 How to Use")
            st.markdown("""
            - **Click** on any municipality for details
            - **Hover** for quick score preview
            - Use **filters** in sidebar to narrow results
            - Toggle **basemap** with layer control
            """)
    
    # -------------------------------------------------------------------
    # TAB 2: Analytics
    # -------------------------------------------------------------------
    with tab2:
        st.markdown("## Market Analysis Overview")
        
        # Key metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            tier1_count = len(municipalities[municipalities['MARKET_TIER'] == 'Tier 1 - Prime'])
            tier1_pop = municipalities[municipalities['MARKET_TIER'] == 'Tier 1 - Prime']['POPULATION'].sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.5rem;">{tier1_count}</h2>
                <p style="margin: 5px 0 0 0;">Tier 1 - Prime Markets</p>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{tier1_pop:,.0f} residents</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            tier2_count = len(municipalities[municipalities['MARKET_TIER'] == 'Tier 2 - Strong'])
            tier2_pop = municipalities[municipalities['MARKET_TIER'] == 'Tier 2 - Strong']['POPULATION'].sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1976D2 0%, #42A5F5 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.5rem;">{tier2_count}</h2>
                <p style="margin: 5px 0 0 0;">Tier 2 - Strong Markets</p>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{tier2_pop:,.0f} residents</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            tier3_count = len(municipalities[municipalities['MARKET_TIER'] == 'Tier 3 - Moderate'])
            tier3_pop = municipalities[municipalities['MARKET_TIER'] == 'Tier 3 - Moderate']['POPULATION'].sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #F57C00 0%, #FFB74D 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.5rem;">{tier3_count}</h2>
                <p style="margin: 5px 0 0 0;">Tier 3 - Moderate Markets</p>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{tier3_pop:,.0f} residents</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col4:
            tier4_count = len(municipalities[municipalities['MARKET_TIER'] == 'Tier 4 - Low'])
            tier4_pop = municipalities[municipalities['MARKET_TIER'] == 'Tier 4 - Low']['POPULATION'].sum()
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #757575 0%, #9E9E9E 100%); padding: 20px; border-radius: 10px; color: white; text-align: center;">
                <h2 style="margin: 0; font-size: 2.5rem;">{tier4_count}</h2>
                <p style="margin: 5px 0 0 0;">Tier 4 - Low Markets</p>
                <p style="margin: 0; font-size: 0.9rem; opacity: 0.9;">{tier4_pop:,.0f} residents</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Charts row 1
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Market Tier Distribution")
            fig = create_tier_distribution_chart(municipalities)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### County Market Size Comparison")
            fig = create_county_comparison_chart(municipalities)
            st.plotly_chart(fig, use_container_width=True)
        
        # Charts row 2
        st.markdown("### Population vs Opportunity Score")
        st.markdown("*Bubble size represents Market Size. Hover for details.*")
        fig = create_scatter_plot(municipalities)
        st.plotly_chart(fig, use_container_width=True)
    
    # -------------------------------------------------------------------
    # TAB 3: Data Explorer
    # -------------------------------------------------------------------
    with tab3:
        st.markdown("## 📋 Full Data Explorer")
        st.markdown("Sort by clicking column headers. Use filters in sidebar to narrow results.")
        
        # Apply filters
        filtered_df = municipalities.copy()
        if selected_counties:
            filtered_df = filtered_df[filtered_df['COUNTY'].isin(selected_counties)]
        if selected_tiers:
            filtered_df = filtered_df[filtered_df['MARKET_TIER'].isin(selected_tiers)]
        if selected_types:
            filtered_df = filtered_df[filtered_df['TYPE'].str.lower().isin([t.lower() for t in selected_types])]
        
        # Prepare display dataframe
        display_df = filtered_df[[
            'OPPORTUNITY_RANK', 'NAME', 'TYPE', 'COUNTY', 'POPULATION', 
            'MEDIAN_INCOME', 'ACUP_INDEX', 'OPPORTUNITY_SCORE', 'MARKET_TIER', 'LIFEMODE'
        ]].copy()
        
        display_df.columns = [
            'Rank', 'Name', 'Type', 'County', 'Population', 
            'Median Income', 'Market Index', 'Opportunity Score', 'Tier', 'LifeMode'
        ]
        
        display_df = display_df.sort_values('Rank')
        
        # Format columns
        display_df['Population'] = display_df['Population'].apply(lambda x: f"{x:,.0f}")
        display_df['Median Income'] = display_df['Median Income'].apply(lambda x: f"${x:,.0f}")
        display_df['Market Index'] = display_df['Market Index'].apply(lambda x: f"{x:.1f}")
        display_df['Opportunity Score'] = display_df['Opportunity Score'].apply(lambda x: f"{x:.1f}")
        display_df['Rank'] = display_df['Rank'].apply(lambda x: f"#{int(x)}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            height=600,
            hide_index=True
        )
        
        # Download button
        csv = filtered_df.drop(columns='geometry').to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name="hudson_valley_acupuncture_analysis.csv",
            mime="text/csv"
        )
    
    # -------------------------------------------------------------------
    # TAB 4: Top Opportunities
    # -------------------------------------------------------------------
    with tab4:
        st.markdown("## 🏆 Top Market Opportunities")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            n_top = st.slider("Number of top opportunities to show:", 10, 30, 20)
            fig = create_top_opportunities_chart(municipalities, n=n_top)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("### Key Insights")
            
            # Top pick
            top1 = municipalities[municipalities['OPPORTUNITY_RANK'] == 1].iloc[0]
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #2E7D32 0%, #4CAF50 100%); padding: 20px; border-radius: 10px; color: white; margin-bottom: 15px;">
                <h3 style="margin: 0;">🥇 #1 Opportunity</h3>
                <h2 style="margin: 10px 0 5px 0;">{top1['NAME']}</h2>
                <p style="margin: 0;">Score: <strong>{top1['OPPORTUNITY_SCORE']:.1f}</strong></p>
                <p style="margin: 0;">Population: {top1['POPULATION']:,.0f}</p>
                <p style="margin: 0;">Income: ${top1['MEDIAN_INCOME']:,.0f}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            #### Why Yonkers?
            Despite ranking 64th by Market Index alone, Yonkers emerges as #1 due to its massive population base of 211,513 residents.
            
            **Strategic Insight:** A single well-positioned practice could serve the largest city in Westchester County.
            
            ---
            
            #### Tier Strategy
            
            **Tier 1 (Yonkers):** Primary market, consider multiple locations
            
            **Tier 2 (Albany, Nassau):** Secondary markets, strong potential
            
            **Tier 3:** Regional cluster strategy - group nearby municipalities
            """)
    
    # -------------------------------------------------------------------
    # TAB 5: Full Report
    # -------------------------------------------------------------------
    with tab5:
        st.markdown("## 📄 Full Market Analysis Report")
        
        # Try to display PDF
        pdf_path = Path(__file__).parent / "data" / "Hudson_Valley_Acupuncture_Market_Analysis_Report_docx.pdf"
        
        if pdf_path.exists():
            with open(pdf_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                base64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # PDF viewer
                pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="800" type="application/pdf"></iframe>'
                st.markdown(pdf_display, unsafe_allow_html=True)
                
                # Download button
                st.download_button(
                    label="📥 Download Full Report (PDF)",
                    data=pdf_bytes,
                    file_name="Hudson_Valley_Acupuncture_Market_Analysis.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("PDF report not found. Please ensure the report is in the data folder.")
            
            # Show summary instead
            st.markdown("""
            ### Executive Summary
            
            This analysis identifies optimal locations for acupuncture services in the Hudson Valley region, 
            combining demographic data, consumer expenditure patterns, and psychographic segmentation.
            
            **Key Findings:**
            - **Yonkers** emerges as #1 with Opportunity Score of 75.3
            - **Westchester County** leads with Market Size of 50,644
            - **113 municipalities** analyzed across 10 counties
            - **Tier 1 & 2 markets** represent 313,354 residents
            
            **Methodology:**
            - LifeMode psychographic groups (30%)
            - Educational attainment (25%)
            - Female population aged 35-64 (25%)
            - Household income $75K+ (20%)
            """)

if __name__ == "__main__":
    main()

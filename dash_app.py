import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import os
import sys
import urllib.parse
import plotly.graph_objects as go

# Load environment variables FIRST
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import services
from services.property_service import property_service
from services.email_service import email_service
from src.services.genie_service import genie_service

# US City coordinates for mapping
CITY_COORDINATES = {
    'Denver, CO': {'lat': 39.7392, 'lon': -104.9903},
    'Austin, TX': {'lat': 30.2672, 'lon': -97.7431},
    'Seattle, WA': {'lat': 47.6062, 'lon': -122.3321},
    'Portland, OR': {'lat': 45.5152, 'lon': -122.6784},
    'San Francisco, CA': {'lat': 37.7749, 'lon': -122.4194},
    'Los Angeles, CA': {'lat': 34.0522, 'lon': -118.2437},
    'San Diego, CA': {'lat': 32.7157, 'lon': -117.1611},
    'Phoenix, AZ': {'lat': 33.4484, 'lon': -112.0740},
    'Las Vegas, NV': {'lat': 36.1699, 'lon': -115.1398},
    'Salt Lake City, UT': {'lat': 40.7608, 'lon': -111.8910},
    'Boise, ID': {'lat': 43.6150, 'lon': -116.2023},
    'Miami, FL': {'lat': 25.7617, 'lon': -80.1918},
    'Orlando, FL': {'lat': 28.5383, 'lon': -81.3792},
    'Tampa, FL': {'lat': 27.9506, 'lon': -82.4572},
    'Atlanta, GA': {'lat': 33.7490, 'lon': -84.3880},
    'Nashville, TN': {'lat': 36.1627, 'lon': -86.7816},
    'Dallas, TX': {'lat': 32.7767, 'lon': -96.7970},
    'Houston, TX': {'lat': 29.7604, 'lon': -95.3698},
    'Chicago, IL': {'lat': 41.8781, 'lon': -87.6298},
    'Minneapolis, MN': {'lat': 44.9778, 'lon': -93.2650},
    'Boston, MA': {'lat': 42.3601, 'lon': -71.0589},
    'New York, NY': {'lat': 40.7128, 'lon': -74.0060},
    'Philadelphia, PA': {'lat': 39.9526, 'lon': -75.1652},
    'Washington, DC': {'lat': 38.9072, 'lon': -77.0369},
    'Charlotte, NC': {'lat': 35.2271, 'lon': -80.8431},
    'Raleigh, NC': {'lat': 35.7796, 'lon': -78.6382},
    'New Orleans, LA': {'lat': 29.9511, 'lon': -90.0715},
    'Kansas City, MO': {'lat': 39.0997, 'lon': -94.5786},
    'St. Louis, MO': {'lat': 38.6270, 'lon': -90.1994},
    'Detroit, MI': {'lat': 42.3314, 'lon': -83.0458},
    'Cleveland, OH': {'lat': 41.4993, 'lon': -81.6944},
    'Columbus, OH': {'lat': 39.9612, 'lon': -82.9988},
    'Pittsburgh, PA': {'lat': 40.4406, 'lon': -79.9959},
    'Indianapolis, IN': {'lat': 39.7684, 'lon': -86.1581},
    'Milwaukee, WI': {'lat': 43.0389, 'lon': -87.9065},
    'Albany, NY': {'lat': 42.6526, 'lon': -73.7562},
}

def get_city_coordinates(city, state):
    """Get lat/lon coordinates for a city, state combination"""
    location_key = f"{city}, {state}"
    if location_key in CITY_COORDINATES:
        return CITY_COORDINATES[location_key]
    # Default to center of US if not found
    return {'lat': 39.8283, 'lon': -98.5795}

# Initialize Dash app with Bootstrap theme and Bootstrap Icons
app = dash.Dash(__name__, 
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css"
    ],
    suppress_callback_exceptions=True  # Allow dynamic IDs in callbacks
)
app.title = "Lakehouse Inn - Voice of Customer"

# Custom CSS
custom_style = {
    'primary': '#dc3545',
    'secondary': '#6c757d',
    'background': '#f8f9fa',
    'card': '#ffffff',
    'text': '#212529',
    'text_secondary': '#6c757d',
    'critical': '#dc3545',
    'warning': '#ffc107',
    'good': '#28a745',
    'excellent': '#17a2b8',
}

# Custom inline styles for better appearance
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background-color: #f8f9fa;
            }
            .card {
                border: none;
                box-shadow: 0 2px 4px rgba(0,0,0,0.08);
                transition: transform 0.2s, box-shadow 0.2s;
            }
            .card:hover {
                transform: translateY(-2px);
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            }
            .hover-shadow:hover {
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
                transform: translateY(-2px);
            }
            .accordion-button {
                padding: 0.75rem 1rem !important;
                font-size: 0.95rem !important;
            }
            .accordion-button:not(.collapsed) {
                background-color: #f8f9fa !important;
                color: #212529 !important;
            }
            .accordion-body {
                padding: 0.75rem 1rem !important;
            }
            .accordion-item {
                border: 1px solid #dee2e6 !important;
                margin-bottom: 0.25rem !important;
            }
            .dash-table-container {
                max-width: 100%;
                overflow-x: auto;
            }
            .Select-control {
                border-radius: 0.25rem !important;
            }
            /* Ensure dropdowns can expand properly */
            .Select-menu-outer {
                z-index: 9999 !important;
                max-height: 300px !important;
                position: absolute !important;
                background: white !important;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important;
            }
            .Select-menu {
                max-height: 280px !important;
                overflow-y: auto !important;
                background: white !important;
            }
            /* Dash dropdown improvements */
            .dash-dropdown {
                z-index: 1000 !important;
                position: relative !important;
                min-height: 38px !important;
            }
            .dash-dropdown .Select-menu-outer {
                z-index: 9999 !important;
            }
            /* Prevent dropdown flashing */
            .Select-control {
                transition: none !important;
            }
            .Select-menu-outer {
                transition: none !important;
            }
            /* Ensure parent containers don't clip dropdowns */
            .card {
                overflow: visible !important;
            }
            .card-body {
                overflow: visible !important;
            }
            /* Container overflow settings */
            .container, .container-fluid {
                overflow: visible !important;
            }
            /* Row overflow settings */
            .row {
                overflow: visible !important;
            }
            /* Tab content overflow */
            .tab-content {
                overflow: visible !important;
            }
            .tab-pane {
                overflow: visible !important;
            }
            h1 {
                font-weight: 600;
                color: #212529;
            }
            h3, h4 {
                font-weight: 600;
                color: #495057;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ========================================
# LAYOUT COMPONENTS
# ========================================

def create_header(persona="Role Selection"):
    # Show persona switch buttons only when a persona is active
    show_switcher = persona not in ["Role Selection"]
    
    switcher_buttons = html.Div([
        dbc.ButtonGroup([
            dbc.Button(
                [html.I(className="bi bi-building me-2"), "HQ View"],
                id='btn-switch-hq',
                color="danger" if persona == "Headquarters" else "outline-danger",
                size="sm",
                className="me-1"
            ),
            dbc.Button(
                [html.I(className="bi bi-person-badge me-2"), "PM View"],
                id='btn-switch-pm',
                color="danger" if persona == "Property Manager" else "outline-danger",
                size="sm"
            ),
        ], className="me-3"),
    ], style={'display': 'block' if show_switcher else 'none'})
    
    return dbc.Navbar(
        dbc.Container([
            html.Div([
                html.Span("Lakehouse Inn", style={
                    'fontSize': '1.5rem', 
                    'fontWeight': '700',
                    'color': '#dc3545'
                }),
                html.Span(" Voice of Customer", style={
                    'fontSize': '1.5rem', 
                    'fontWeight': '300',
                    'color': '#495057'
                }),
            ]),
            html.Div([
                switcher_buttons,
                dbc.Badge(
                    persona, 
                    color="danger", 
                    className="px-3 py-2",
                    style={'fontSize': '0.875rem', 'fontWeight': '500'},
                    id='persona-badge'
                )
            ], className="ms-auto d-flex align-items-center")
        ], fluid=True, style={'maxWidth': '1400px'}),
        color="white",
        dark=False,
        sticky="top",
        style={'boxShadow': '0 2px 4px rgba(0,0,0,0.08)'},
        className="mb-0"
    )

def create_role_selection():
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("Select Your Role", 
                       className="text-center mb-3",
                       style={'fontSize': '2.5rem', 'fontWeight': '700'}),
                html.P("Choose your persona to get started", 
                       className="text-center mb-5",
                       style={'fontSize': '1.125rem', 'color': '#6c757d'}),
            ], className="mt-5 pt-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div("🏢", style={'fontSize': '3rem'}, className="mb-3"),
                                html.H3("Headquarters", 
                                       className="card-title text-center mb-3",
                                       style={'fontWeight': '600', 'fontSize': '1.5rem'}),
                                html.P("View all properties, identify issues, and take action across the portfolio.", 
                                      className="text-center mb-4",
                                      style={'color': '#6c757d', 'lineHeight': '1.6'}),
                                dbc.Button("Enter as HQ", 
                                          id='btn-select-hq', 
                                          color="danger", 
                                          size="lg",
                                          className="w-100",
                                          style={'fontWeight': '500', 'padding': '0.75rem'})
                            ], className="text-center", style={'padding': '1.5rem'})
                        ], style={'padding': '0'})
                    ], className="h-100", style={'border': 'none', 'borderRadius': '12px'})
                ], md=5),
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div("🏨", style={'fontSize': '3rem'}, className="mb-3"),
                                html.H3("Property Manager", 
                                       className="card-title text-center mb-3",
                                       style={'fontWeight': '600', 'fontSize': '1.5rem'}),
                                html.P("Monitor your property's performance and address guest feedback.",
                                      className="text-center mb-4",
                                      style={'color': '#6c757d', 'lineHeight': '1.6'}),
                                dbc.Button("Enter as PM", 
                                          id='btn-select-pm', 
                                          color="danger", 
                                          size="lg",
                                          className="w-100",
                                          style={'fontWeight': '500', 'padding': '0.75rem'})
                            ], className="text-center", style={'padding': '1.5rem'})
                        ], style={'padding': '0'})
                    ], className="h-100", style={'border': 'none', 'borderRadius': '12px'})
                ], md=5),
            ], className="g-4 justify-content-center"),
        ], style={'maxWidth': '1200px'}),
    ], style={'minHeight': '75vh', 'display': 'flex', 'alignItems': 'center'})

def create_hq_properties():
    # Display the placeholder content that will be populated by callbacks
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("All Properties", className="mb-2", style={'fontWeight': '700'}),
                html.Div(id='hq-properties-subtitle', className="mb-4"),
            ], className="my-4 py-3"),
        ], style={'maxWidth': '1400px'}),
        
        # Timeframe Selector for Stats
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("Stats Timeframe:", style={'fontWeight': '600', 'marginRight': '1rem', 'fontSize': '0.95rem'}),
                        ], width="auto", className="d-flex align-items-center"),
                        dbc.Col([
                            dbc.RadioItems(
                                id='hq-stats-timeframe-selector',
                                options=[
                                    {'label': 'Last 7 Days', 'value': 7},
                                    {'label': 'Last 14 Days', 'value': 14},
                                    {'label': 'Last 21 Days', 'value': 21},
                                    {'label': 'All Historical', 'value': 'all'}
                                ],
                                value='all',  # Default to All Historical
                                inline=True,
                                style={'fontSize': '0.9rem'}
                            ),
                        ], className="d-flex align-items-center"),
                        dbc.Col([
                            html.Div(id='hq-stats-latest-date', className="text-end"),
                        ], className="d-flex align-items-center justify-content-end"),
                    ], className="align-items-center"),
                ], style={'padding': '0.75rem 1.25rem'})
            ], style={'border': 'none', 'borderRadius': '8px', 'backgroundColor': '#f8f9fa'})
        ], style={'maxWidth': '1400px'}, className="mb-3"),
        
        # Executive KPIs Section
        dcc.Loading(
            id="loading-kpis",
            type="default",
            children=html.Div(id='hq-executive-kpis', className="mb-5")
        ),
        
        # HQ Overview Dashboard Section
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Issues Overview", className="mb-4", style={'fontWeight': '600'}),
                    dcc.Loading(
                        id="loading-hq-overview-dashboard",
                        type="default",
                        children=html.Div(id='hq-overview-dashboard-iframe')
                    )
                ], style={'padding': '1.5rem'})
            ], style={'border': 'none', 'borderRadius': '12px'}, className="mb-5")
        ], style={'maxWidth': '1400px'}),
        
        # Regional Performance Map Section
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H4("🗺️ Regional Performance Map", className="mb-3", style={'fontWeight': '600'}),
                    html.P("Click on any location to jump to that property below", 
                          className="text-muted mb-3",
                          style={'fontSize': '0.95rem'}),
                    dcc.Loading(
                        id="loading-map",
                        type="default",
                        children=dcc.Graph(id='properties-map', config={'displayModeBar': False}, 
                                         style={'height': '500px'})
                    ),
                ], style={'padding': '1.5rem'})
            ], style={'border': 'none', 'borderRadius': '12px'}, className="mb-5")
        ], style={'maxWidth': '1400px'}),
        
        # Flagged Properties - Grouped View
        dbc.Container([
            html.Div([
                html.H3([
                    html.Span("🚨", style={'marginRight': '0.5rem'}),
                    "Properties Requiring Attention"
                ], className="mb-0 d-inline-block", style={'fontWeight': '600', 'fontSize': '1.75rem'}),
                html.I(
                    className="bi bi-info-circle ms-2",
                    id={'type': 'open-severity-modal', 'view': 'hq-properties'},
                    style={
                        'fontSize': '1.25rem',
                        'color': '#0d6efd',
                        'cursor': 'pointer',
                        'verticalAlign': 'middle'
                    },
                    title="Click to view severity threshold logic",
                    n_clicks=0
                ),
            ], className="mb-4", style={'display': 'flex', 'alignItems': 'center'}),
            dcc.Loading(
                id="loading-flagged-properties",
                type="default",
                children=html.Div(id='flagged-properties-grouped')
            )
        ], style={'maxWidth': '1400px'}, className="mb-5"),
        
        # All Properties - Compact Summary
        dbc.Container([
            dcc.Loading(
                id="loading-all-properties",
                type="default",
                children=html.Div(id='all-properties-summary')
            )
        ], style={'maxWidth': '1400px'}, className="mb-5"),
        
        # Hidden location store for scroll targeting
        dcc.Store(id='scroll-to-property'),
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh'})

def create_hq_dashboard():
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("Property Health Dashboard", className="mb-2", style={'fontWeight': '700'}),
                html.P("Validate issues and review corresponding data", 
                      className="mb-4",
                      style={'fontSize': '1.125rem', 'color': '#6c757d'}),
            ], className="my-4"),
            
            # Property selector dropdown
            dbc.Card([
                dbc.CardBody([
                    html.Label("Select Property:", 
                              className="mb-2",
                              style={'fontWeight': '600', 'fontSize': '1rem'}),
                    dcc.Dropdown(
                        id='hq-property-select',
                        placeholder="Select a property...",
                        className="mb-2",
                        style={'fontSize': '1rem'},
                        optionHeight=35,
                        maxHeight=300
                    ),
                ], style={'padding': '1.5rem', 'overflow': 'visible'})
            ], className="mb-4", style={'border': 'none', 'borderRadius': '12px', 'position': 'relative', 'zIndex': '100'}),
        ], style={'maxWidth': '1400px'}),
        
        # Property details (stays visible)
        dbc.Container([
            dcc.Loading(
                id="loading-property-details",
                type="default",
                children=html.Div(id='hq-selected-property-details-container')
            ),
        ], style={'maxWidth': '1400px'}, className="mb-4"),
        
        # TABS SECTION
        dbc.Container([
            dbc.Tabs([
                # Tab 1: Property Ovewrview
                dbc.Tab(
                    html.Div([
                        html.Div(id='hq-filtered-dashboard-iframe', className="mt-3"),
                    ], style={'padding': '1.5rem 0'}),
                    label="Property Overview",
                    tab_id="analytics-tab",
                ),
                
                # Tab 2: Aspect Analysis + Review Deep Dive
                dbc.Tab(
                    html.Div([
                        # Aspect Analysis Table
                        dcc.Loading(
                            id="loading-aspect-analysis",
                            type="default",
                            children=html.Div(id='hq-aspect-analysis-table', className="mb-4")
                        ),
                        
                        # Reviews Deep Dive Section
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("📊 Reviews Deep Dive", className="mb-3", style={'fontWeight': '600'}),
                                html.P("Select an aspect to analyze detailed review insights", 
                                      className="text-muted mb-3",
                                      style={'fontSize': '0.95rem'}),
                                html.Div([
                                    dcc.Dropdown(
                                        id='hq-aspect-selector',
                                        placeholder="Select an aspect to analyze...",
                                        className="mb-3",
                                        style={'fontSize': '1rem'},
                                        optionHeight=35,
                                        maxHeight=250
                                    ),
                                ], style={'position': 'relative', 'zIndex': '50', 'marginBottom': '1rem'}),
                            ], style={'padding': '1.5rem', 'overflow': 'visible'})
                        ], className="mb-5", style={'border': 'none', 'borderRadius': '12px', 'position': 'relative'}),
                        # Deep Dive Content (Issue Summary, Recommendations, etc.)
                        dcc.Loading(
                            id="loading-reviews-deep-dive",
                            type="default",
                            children=html.Div(id='hq-reviews-deep-dive-content')
                        ),
                        
                        # Individual Reviews Browser (separate from deep dive content)
                        html.Div([
                            html.Div(id='hq-review-browser-controls'),  # Controls (timeframe, filter)
                            dcc.Loading(
                                id="loading-hq-individual-reviews",
                                type="default",
                                children=html.Div(id='hq-individual-reviews-list')
                            )
                        ], id='hq-individual-reviews-section', style={'marginTop': '2rem'}),
                    ], style={'padding': '1.5rem 0'}),
                    label="Aspect Analysis + Review Deep Dive",
                    tab_id="aspect-tab",
                ),
                
                # Tab 3: Generate Email
                dbc.Tab(
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("Generate Email", className="mb-3", style={'fontWeight': '600'}),
                                html.P("Generate a detailed email for the property manager", 
                                      className="text-muted mb-3",
                                      style={'fontSize': '0.95rem'}),
                                dbc.Button(
                                    "Generate Email",
                                    id='hq-generate-email-btn',
                                    color="primary",
                                    className="mb-3",
                                    style={'borderRadius': '8px', 'padding': '0.75rem 1.5rem'}
                                ),
                                html.Div(id='hq-email-draft'),
                            ], style={'padding': '1.5rem'})
                        ], style={'border': 'none', 'borderRadius': '12px'}),
                    ], style={'padding': '1.5rem 0'}),
                    label="Generate Email",
                    tab_id="email-tab",
                ),
            ], id="hq-dashboard-tabs", active_tab="analytics-tab"),
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        # Ask Genie - Floating section (always visible)
        dbc.Container([
            # Conversation history storage
            dcc.Store(id='hq-genie-conversation-history', data=[]),
            dcc.Store(id='hq-genie-conversation-id', data=None),
            
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4("Ask Genie", className="mb-0", style={'fontWeight': '600'}),
                        dbc.Button(
                            [html.I(className="bi bi-arrow-clockwise me-2"), "New Conversation"],
                            id='btn-clear-genie-hq',
                            color="secondary",
                            size="sm",
                            outline=True,
                            style={'borderRadius': '6px', 'fontWeight': '500'},
                            title="Clear conversation history and start fresh"
                        ),
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '1rem'}),
                    
                    # Conversation history display
                    html.Div(id='hq-genie-conversation-display', className="mb-3", style={
                        'maxHeight': '400px',
                        'overflowY': 'auto',
                        'padding': '0.5rem',
                        'borderRadius': '8px',
                    }),
                    
                    # Input area
                    dbc.InputGroup([
                        dbc.Input(
                            id='hq-genie-input',
                            placeholder="Ask a question about this property...",
                            type="text",
                            style={'borderRadius': '8px 0 0 8px', 'padding': '0.75rem'}
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-send-fill me-1"), "Ask"],
                            id='btn-ask-genie-hq',
                            color="primary",
                            style={'borderRadius': '0 8px 8px 0', 'padding': '0.75rem 1.5rem'}
                        ),
                    ], className="mb-0"),
                    dcc.Loading(
                        id="loading-hq-genie",
                        type="default",
                        children=html.Div(id='hq-genie-results-container', style={'display': 'none'})
                    ),
                ], style={'padding': '1.5rem'})
            ], style={'border': 'none', 'borderRadius': '12px', 'backgroundColor': '#f8f9fa'})
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        # Back to Properties button
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button("Back to Properties", id='btn-back-to-properties', color="secondary", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto"),
            ], className="mb-4"),
        ], style={'maxWidth': '1400px'}),
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'paddingBottom': '3rem'})

def create_hq_email():
    return html.Div([
        dbc.Container([
            html.Div([
                html.H1("Draft Email to Property Manager", className="mb-2", style={'fontWeight': '700'}),
                html.P("Review and send the pre-populated email", 
                      className="mb-4",
                      style={'fontSize': '1.125rem', 'color': '#6c757d'}),
            ], className="my-4"),
        ], style={'maxWidth': '1400px'}),
        dbc.Container([
            html.Div(id='email-draft'),
        ], style={'maxWidth': '1400px'}, className="mb-4"),
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button("Back to Dashboard", id='btn-back-to-dashboard', color="secondary", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto"),
                dbc.Col([
                    dbc.Button("Send Email", id='btn-send-email', color="danger", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto", className="ms-auto"),
            ], className="mb-4"),
        ], style={'maxWidth': '1400px'}),
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'paddingBottom': '3rem'})

def create_pm_dashboard():
    return html.Div([
        # Property selection buttons at the top
        dbc.Container([
            html.Div([
                html.Div([
                    html.H1("My Property Dashboard", className="mb-3", style={'fontWeight': '700', 'display': 'inline-block', 'marginRight': '2rem'}),
                    html.Div([
                        html.Span("Select Property:", className="me-3", style={'fontWeight': '600', 'fontSize': '1rem', 'color': '#495057'}),
                        dbc.ButtonGroup([
                            dbc.Button(
                                [html.I(className="bi bi-building me-2"), "Austin, TX"],
                                id={'type': 'pm-property-btn', 'location': 'Austin, TX'},
                                color="primary",
                                outline=True,
                                className="me-2",
                                style={'borderRadius': '8px', 'padding': '0.5rem 1.5rem', 'fontWeight': '500'}
                            ),
                            dbc.Button(
                                [html.I(className="bi bi-building me-2"), "Boston, MA"],
                                id={'type': 'pm-property-btn', 'location': 'Boston, MA'},
                                color="primary",
                                outline=True,
                                style={'borderRadius': '8px', 'padding': '0.5rem 1.5rem', 'fontWeight': '500'}
                            ),
                        ]),
                    ], style={'display': 'inline-block'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'flexWrap': 'wrap'}),
                html.P("Monitor your property's performance and guest satisfaction", 
                      className="mb-0 mt-3",
                      style={'fontSize': '1.125rem', 'color': '#6c757d'}),
            ], className="my-4 py-3"),
        ], fluid=True, style={'maxWidth': '1400px', 'borderBottom': '1px solid #e0e0e0', 'paddingBottom': '1rem', 'marginBottom': '2rem'}),
        
        # Hidden store for selected property (default to Austin, TX)
        dcc.Store(id='pm-selected-property-store', data='austin-tx'),
        
        # Property details (stays visible)
        dbc.Container([
            dcc.Loading(
                id="loading-pm-property-details",
                type="default",
                children=html.Div(id='pm-selected-property-details-container')
            ),
        ], style={'maxWidth': '1400px'}, className="mb-4"),
        
        # TABS SECTION (similar to HQ but only 2 tabs)
        dbc.Container([
            dbc.Tabs([
                # Tab 1: Property Ovewrview
                dbc.Tab(
                    html.Div([
                        html.Div(id='pm-filtered-dashboard-iframe', className="mt-3"),
                    ], style={'padding': '1.5rem 0'}),
                    label="Property Ovewrview",
                    tab_id="pm-analytics-tab",
                ),
                
                # Tab 2: Aspect Analysis + Review Deep Dive
                dbc.Tab(
                    html.Div([
                        # Aspect Analysis Table
                        dcc.Loading(
                            id="loading-pm-aspect-analysis",
                            type="default",
                            children=html.Div(id='pm-aspect-analysis-table', className="mb-4")
                        ),
                        
                        # Reviews Deep Dive Section
                        dbc.Card([
                            dbc.CardBody([
                                html.H4("📊 Reviews Deep Dive", className="mb-3", style={'fontWeight': '600'}),
                                html.P("Select an aspect to analyze detailed review insights", 
                                      className="text-muted mb-3",
                                      style={'fontSize': '0.95rem'}),
                                html.Div([
                                    dcc.Dropdown(
                                        id='pm-aspect-selector',
                                        placeholder="Select an aspect to analyze...",
                                        className="mb-3",
                                        style={'fontSize': '1rem'},
                                        optionHeight=35,
                                        maxHeight=250
                                    ),
                                ], style={'position': 'relative', 'zIndex': '50', 'marginBottom': '1rem'}),
                            ], style={'padding': '1.5rem', 'overflow': 'visible'})
                        ], className="mb-5", style={'border': 'none', 'borderRadius': '12px', 'position': 'relative'}),
                        # Deep Dive Content (Issue Summary, Recommendations, etc.)
                        dcc.Loading(
                            id="loading-pm-reviews-deep-dive",
                            type="default",
                            children=html.Div(id='pm-reviews-deep-dive-content')
                        ),
                        
                        # Individual Reviews Browser (separate from deep dive content)
                        html.Div([
                            html.Div(id='pm-review-browser-controls'),  # Controls (timeframe, filter)
                            dcc.Loading(
                                id="loading-pm-individual-reviews",
                                type="default",
                                children=html.Div(id='pm-individual-reviews-list')
                            )
                        ], id='pm-individual-reviews-section', style={'marginTop': '2rem'}),
                    ], style={'padding': '1.5rem 0'}),
                    label="Aspect Analysis + Review Deep Dive",
                    tab_id="pm-aspect-tab",
                ),
            ], id="pm-dashboard-tabs", active_tab="pm-analytics-tab"),
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        # Ask Genie - Floating section (always visible)
        dbc.Container([
            # Conversation history storage
            dcc.Store(id='pm-genie-conversation-history', data=[]),
            dcc.Store(id='pm-genie-conversation-id', data=None),
            
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.H4("Ask Genie", className="mb-0", style={'fontWeight': '600'}),
                        dbc.Button(
                            [html.I(className="bi bi-arrow-clockwise me-2"), "New Conversation"],
                            id='btn-clear-genie-pm',
                            color="secondary",
                            size="sm",
                            outline=True,
                            style={'borderRadius': '6px', 'fontWeight': '500'},
                            title="Clear conversation history and start fresh"
                        ),
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'center', 'marginBottom': '1rem'}),
                    
                    # Conversation history display
                    html.Div(id='pm-genie-conversation-display', className="mb-3", style={
                        'maxHeight': '400px',
                        'overflowY': 'auto',
                        'padding': '0.5rem',
                        'borderRadius': '8px',
                    }),
                    
                    # Input area
                    dbc.InputGroup([
                        dbc.Input(
                            id='pm-genie-input',
                            placeholder="Ask a question about your property...",
                            type="text",
                            style={'borderRadius': '8px 0 0 8px', 'padding': '0.75rem'}
                        ),
                        dbc.Button(
                            [html.I(className="bi bi-send-fill me-1"), "Ask"],
                            id='btn-ask-genie-pm',
                            color="primary",
                            style={'borderRadius': '0 8px 8px 0', 'padding': '0.75rem 1.5rem'}
                        ),
                    ], className="mb-0"),
                    dcc.Loading(
                        id="loading-pm-genie",
                        type="default",
                        children=html.Div(id='pm-genie-results', style={'display': 'none'})
                    ),
                ], style={'padding': '1.5rem'})
            ], style={'border': 'none', 'borderRadius': '12px', 'backgroundColor': '#f8f9fa'})
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        # Back to Role Selection button
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button("Back to Role Selection", id='btn-back-to-roles', color="secondary", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto"),
            ], className="mb-4"),
        ], style={'maxWidth': '1400px'}),
    ], style={'backgroundColor': '#f8f9fa', 'minHeight': '100vh', 'paddingBottom': '3rem'})

# Main app layout - All IDs must exist here for callbacks to work
app.layout = html.Div([
    dcc.Store(id='current-screen', data='role-selection'),
    dcc.Store(id='current-persona', data='Role Selection'),
    dcc.Store(id='selected-property-id', data=None),
    dcc.Store(id='email-data', data=None),
    
    # Header (initialized with Role Selection persona)
    html.Div(id='header', children=create_header('Role Selection')),
    
    # Main content screens (only one visible at a time)
    html.Div([
        html.Div(id='role-selection-content', children=create_role_selection()),
        html.Div(id='hq-properties-content', children=create_hq_properties(), style={'display': 'none'}),
        html.Div(id='hq-dashboard-content', children=create_hq_dashboard(), style={'display': 'none'}),
        html.Div(id='hq-email-content', children=create_hq_email(), style={'display': 'none'}),
        html.Div(id='pm-dashboard-content', children=create_pm_dashboard(), style={'display': 'none'}),
    ], className="py-4"),
    
    # Global placeholder divs for callback outputs (exist in initial layout)
    # These are referenced by multiple screens and updated by callbacks
    html.Div([
        html.Div(id='selected-property-details'),
        html.Div(id='pm-property-details'),
    ], style={'display': 'none'}),
    
    # Modal for "no reviews" message
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("No Reviews Available")),
        dbc.ModalBody([
            html.P("This property has no review data in the current timeframe."),
            html.P("There is no detailed information to display at this time."),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-no-reviews-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="no-reviews-modal", is_open=False),
    
    # Modal for severity threshold explanation
    dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("Severity Threshold Logic")),
        dbc.ModalBody([
            html.P("Status is determined by comparing recent 7-day performance against a 21-day baseline:", 
                  style={'marginBottom': '1rem'}),
            html.Div([
                html.H6("Thresholds:", style={'fontWeight': '600', 'marginBottom': '0.75rem'}),
                html.Ul([
                    html.Li([
                        html.Strong("Critical: "), 
                        "neg_7d ≥ 0.80 ",
                        html.Strong("OR "),
                        "delta_pp ≥ 15.0"
                    ], style={'marginBottom': '0.5rem'}),
                    html.Li([
                        html.Strong("Warning: "), 
                        "neg_7d ≥ 0.60 ",
                        html.Strong("OR "),
                        "delta_pp ≥ 10.0"
                    ], style={'marginBottom': '0.5rem'}),
                    html.Li([
                        html.Strong("Minimum volume: "), 
                        "Only triggered if volume_7d ≥ 7"
                    ]),
                ], style={'paddingLeft': '1.5rem'}),
            ], style={'marginBottom': '1rem'}),
            html.Div([
                html.H6("Definitions:", style={'fontWeight': '600', 'marginBottom': '0.75rem'}),
                html.Ul([
                    html.Li([
                        html.Strong("neg_7d: "), 
                        "Negative review percentage in last 7 days"
                    ], style={'marginBottom': '0.5rem'}),
                    html.Li([
                        html.Strong("delta_pp: "), 
                        "Change in negative share (percentage points) vs 21-day baseline"
                    ], style={'marginBottom': '0.5rem'}),
                    html.Li([
                        html.Strong("volume_7d: "), 
                        "Total number of reviews in last 7 days"
                    ]),
                ], style={'paddingLeft': '1.5rem'}),
            ]),
        ]),
        dbc.ModalFooter(
            dbc.Button("Close", id="close-severity-modal", className="ms-auto", n_clicks=0)
        ),
    ], id="severity-threshold-modal", is_open=False),
])

# ========================================
# CALLBACKS
# ========================================

# Helper function to extract role and property for service principal authentication
def get_auth_context(persona, pm_property=None, hq_property=None):
    """
    Extract role and property for service principal authentication
    
    Args:
        persona: Current persona ('Headquarters' or 'Property Manager' or 'Role Selection')
        pm_property: PM selected property (e.g., 'austin-tx' or 'boston-ma')
        hq_property: HQ selected property (optional, for future use)
    
    Returns:
        Tuple of (role, property) where:
        - role: 'hq' or 'pm'
        - property: 'austin-tx', 'boston-ma', or None
    """
    if not persona or persona == 'Role Selection':
        return ('hq', None)  # Default to HQ
    
    if persona == 'Headquarters':
        return ('hq', None)
    elif persona == 'Property Manager':
        return ('pm', pm_property)
    else:
        return ('hq', None)  # Fallback

# Screen navigation and header update
@app.callback(
    [Output('role-selection-content', 'style'),
     Output('hq-properties-content', 'style'),
     Output('hq-dashboard-content', 'style'),
     Output('hq-email-content', 'style'),
     Output('pm-dashboard-content', 'style'),
     Output('header', 'children'),
     Output('current-persona', 'data')],
    [Input('current-screen', 'data')],
    [State('current-persona', 'data')]
)
def navigate_screens(current_screen, current_persona):
    print(f"📱 navigate_screens called with screen: {current_screen}, persona: {current_persona}")
    
    # Default visibility
    role_style = {'display': 'none'}
    hq_prop_style = {'display': 'none'}
    hq_dash_style = {'display': 'none'}
    hq_email_style = {'display': 'none'}
    pm_dash_style = {'display': 'none'}
    
    # Set persona based on screen if not set
    if not current_persona:
        current_persona = 'Role Selection'
    
    # Navigation logic based on current screen
    if current_screen == 'hq-properties':
        current_persona = 'Headquarters'
        hq_prop_style = {'display': 'block'}
        print("✅ Showing HQ Properties")
    elif current_screen == 'hq-dashboard':
        current_persona = 'Headquarters'
        hq_dash_style = {'display': 'block'}
        print("✅ Showing HQ Dashboard")
    elif current_screen == 'hq-email':
        current_persona = 'Headquarters'
        hq_email_style = {'display': 'block'}
        print("✅ Showing HQ Email")
    elif current_screen == 'pm-dashboard':
        current_persona = 'Property Manager'
        pm_dash_style = {'display': 'block'}
        print("✅ Showing PM Dashboard")
    else:  # role-selection or default
        current_persona = 'Role Selection'
        role_style = {'display': 'block'}
        print("✅ Showing Role Selection")
    
    return (
        role_style,
        hq_prop_style,
        hq_dash_style,
        hq_email_style,
        pm_dash_style,
        create_header(current_persona),
        current_persona
    )

# Button click handlers to update screen
@app.callback(
    Output('current-screen', 'data', allow_duplicate=True),
    [Input('btn-select-hq', 'n_clicks'),
     Input('btn-select-pm', 'n_clicks'),
     Input('btn-back-to-properties', 'n_clicks'),
     Input('btn-back-to-roles', 'n_clicks'),
     Input('btn-switch-hq', 'n_clicks'),
     Input('btn-switch-pm', 'n_clicks')],
    prevent_initial_call='initial_duplicate'  # Only prevent on initial duplicate, not on component creation
)
def handle_button_clicks(hq, pm, back_prop, back_roles, switch_hq, switch_pm):
    ctx = callback_context
    print(f"🎯 handle_button_clicks triggered!")
    print(f"   Triggered by: {ctx.triggered}")
    
    if not ctx.triggered:
        print(f"   ⏭️  No trigger, returning no_update")
        return dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_value = ctx.triggered[0]['value']
    print(f"   Button: {button_id}")
    print(f"   Value: {triggered_value}")
    
    # Only proceed if button was actually clicked (value is not None and >= 1)
    if triggered_value is None or triggered_value < 1:
        print(f"   ⏭️  No actual click detected (value={triggered_value}), returning no_update")
        return dash.no_update
    
    if button_id == 'btn-select-hq':
        print(f"   ➡️  Navigating to: hq-properties")
        return 'hq-properties'
    elif button_id == 'btn-select-pm':
        print(f"   ➡️  Navigating to: pm-dashboard")
        return 'pm-dashboard'
    elif button_id == 'btn-back-to-properties':
        print(f"   ➡️  Navigating to: hq-properties")
        return 'hq-properties'
    elif button_id == 'btn-back-to-roles':
        print(f"   ➡️  Navigating to: role-selection")
        return 'role-selection'
    elif button_id == 'btn-switch-hq':
        print(f"   ➡️  Navigating to: hq-properties")
        return 'hq-properties'
    elif button_id == 'btn-switch-pm':
        print(f"   ➡️  Navigating to: pm-dashboard")
        return 'pm-dashboard'
    
    print(f"   ⏭️  No matching button, returning no_update")
    return dash.no_update

# Load HQ Properties Subtitle with counts
@app.callback(
    Output('hq-properties-subtitle', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')]
)
def load_hq_properties_subtitle(screen, timeframe):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        # Get stats with timeframe
        stats = property_service.get_diagnostics_kpis(days=days)
        flagged = property_service.get_flagged_properties(days=days)
        
        # Count unique flagged properties
        flagged_count = len(set(prop['property_id'] for prop in flagged))
        total_locations = stats.get('total_properties', 0)
        
        return html.P([
            html.Span(f"{flagged_count} Properties Flagged", 
                     style={'fontWeight': '600', 'color': '#dc3545'}),
            html.Span(" | ", style={'margin': '0 0.5rem', 'color': '#6c757d'}),
            html.Span(f"{total_locations} Total Locations", 
                     style={'color': '#6c757d'})
        ], style={'fontSize': '1.125rem'})
    except Exception as e:
        print(f"❌ Error loading subtitle: {str(e)}")
        return html.P("Review flagged properties and take action", 
                     className="text-muted",
                     style={'fontSize': '1.125rem'})

# Load HQ Overview Dashboard iframe with date filter
@app.callback(
    Output('hq-overview-dashboard-iframe', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def load_hq_overview_dashboard(screen, timeframe):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        from datetime import datetime, timedelta
        from urllib.parse import quote
        
        # Set auth context
        property_service.set_auth_context(role='hq', property=None)
        
        # Calculate date range based on timeframe
        if timeframe == 'all':
            # For "All Historical", don't add date filter
            base_url = os.getenv('DATABRICKS_OVERVIEW_DASHBOARD_URL', "https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/embed/dashboardsv3/01f0b6901b281266b22ae454018a5b82?o=604717363374831")
            filtered_url = base_url
        else:
            # Get latest review date from data
            days = None if timeframe == 'all' else timeframe
            review_stats = property_service.get_summary_stats_from_reviews(days=days)
            latest_date_str = review_stats.get('latest_review_date', None)
            
            if latest_date_str:
                # Parse the latest review date (format: YYYY-MM-DD or similar)
                try:
                    end_date = datetime.strptime(latest_date_str, '%Y-%m-%d')
                except:
                    # Try alternative format if needed
                    try:
                        end_date = datetime.strptime(latest_date_str.split('T')[0], '%Y-%m-%d')
                    except:
                        # Fallback to current date if parsing fails
                        end_date = datetime.now()
            else:
                # Fallback to current date if no latest date available
                end_date = datetime.now()
            
            # Calculate start date by subtracting timeframe days from latest review date
            start_date = end_date - timedelta(days=int(timeframe))
            
            # Format dates for Databricks: YYYY-MM-DD
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            
            # Build the URL with date filter
            # Format: f_overview~6c1cd566={start_date}T00%3A00%3A00.000~{end_date}T23%3A59%3A59.999
            date_filter = f"{start_date_str}T00%3A00%3A00.000~{end_date_str}T23%3A59%3A59.999"
            
            base_url_overview = os.getenv('DATABRICKS_OVERVIEW_DASHBOARD_URL', "https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/embed/dashboardsv3/01f0b6901b281266b22ae454018a5b82?o=604717363374831")            
            filtered_url = f"{base_url_overview}&f_overview%7E6c1cd566={date_filter}"
            
            print(f"📅 Dashboard date range: {start_date_str} to {end_date_str} (Latest review: {latest_date_str})")
        
        return html.Iframe(
            src=filtered_url,
            style={
                'width': '100%',
                'height': '800px',
                'border': 'none',
                'borderRadius': '8px',
            }
        )
    except Exception as e:
        print(f"❌ Error loading overview dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading dashboard: {str(e)}", color="warning")

# Load executive KPIs for HQ
@app.callback(
    Output('hq-executive-kpis', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def load_executive_kpis(screen, timeframe):
    print(f"🔍 load_executive_kpis called: screen={screen}, timeframe={timeframe}")
    
    if screen != 'hq-properties':
        print(f"   ⏭️  Skipping KPIs - screen is '{screen}'")
        return html.Div()
    
    print(f"   ✅ Screen is 'hq-properties', loading KPIs...")
    
    try:
        # HQ Properties overview always uses HQ role with all properties
        property_service.set_auth_context(role='hq', property=None)
        
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        print(f"🔄 Loading executive KPIs for HQ Properties (role=hq, property=None, days={days})")
        kpis = property_service.get_diagnostics_kpis(days=days)
        print(f"✅ Loaded KPIs: {kpis} for {days} days")
        
        # Determine timeframe label for display
        if days is None:
            timeframe_label = "All Historical"
        elif days == 7:
            timeframe_label = "Last 7 Days"
        elif days == 14:
            timeframe_label = "Last 14 Days"
        elif days == 21:
            timeframe_label = "Last 21 Days"
        else:
            timeframe_label = f"Last {days} Days"
        
        # Calculate trend indicators
        def get_trend_indicator(change_value):
            if change_value > 0:
                return html.Span([
                    html.I(className="bi bi-arrow-up", style={'marginRight': '0.25rem'}),
                    f"+{change_value}%"
                ], style={'color': '#28a745', 'fontSize': '0.875rem', 'fontWeight': '500'})
            elif change_value < 0:
                return html.Span([
                    html.I(className="bi bi-arrow-down", style={'marginRight': '0.25rem'}),
                    f"{change_value}%"
                ], style={'color': '#dc3545', 'fontSize': '0.875rem', 'fontWeight': '500'})
            else:
                return html.Span("—", style={'color': '#6c757d', 'fontSize': '0.875rem'})
        
        return dbc.Container([
            dbc.Row([
                # Reviews Processed
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-file-earmark-text", 
                                          style={'fontSize': '1.5rem', 'color': '#17a2b8', 'marginBottom': '0.5rem'}),
                                ]),
                                html.H3(str(kpis['reviews_processed']), 
                                       className="mb-1",
                                       style={'fontWeight': '700', 'fontSize': '2.5rem', 'color': '#212529'}),
                                html.P("Reviews Processed", 
                                      className="mb-2 text-muted",
                                      style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                                html.Span(timeframe_label, style={'color': '#6c757d', 'fontSize': '0.875rem'})
                            ])
                        ], style={'padding': '1.5rem'})
                    ], style={'border': 'none', 'borderRadius': '12px', 'height': '100%'})
                ], md=6, lg=3, className="mb-4"),
                
                # Overall Satisfaction (Combined - showing positive metric)
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-emoji-smile", 
                                          style={'fontSize': '1.5rem', 'color': '#28a745', 'marginBottom': '0.5rem'}),
                                ]),
                                html.H3(f"{kpis['overall_satisfaction']}%", 
                                       className="mb-1",
                                       style={'fontWeight': '700', 'fontSize': '2.5rem', 'color': '#28a745'}),
                                html.P("Overall Satisfaction", 
                                      className="mb-2 text-muted",
                                      style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                                html.Span(f"{kpis['avg_negative_reviews']}% negative ({timeframe_label})", 
                                         style={'color': '#6c757d', 'fontSize': '0.875rem'})
                            ])
                        ], style={'padding': '1.5rem'})
                    ], style={'border': 'none', 'borderRadius': '12px', 'height': '100%'})
                ], md=6, lg=3, className="mb-4"),
                
                # Aspects Monitored
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-list-check", 
                                          style={'fontSize': '1.5rem', 'color': '#6c757d', 'marginBottom': '0.5rem'}),
                                ]),
                                html.H3([
                                    html.Span(str(kpis['aspects_with_issues']), 
                                             style={'color': '#dc3545', 'fontWeight': '700'}),
                                    html.Span(" / ", 
                                             style={'color': '#6c757d', 'fontWeight': '400'}),
                                    html.Span(str(kpis['total_aspects']), 
                                             style={'color': '#6c757d', 'fontWeight': '700'})
                                ], className="mb-1",
                                style={'fontSize': '2.5rem'}),
                                html.P("Aspects Monitored", 
                                      className="mb-0 text-muted",
                                      style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                            ])
                        ], style={'padding': '1.5rem'})
                    ], style={'border': 'none', 'borderRadius': '12px', 'height': '100%'})
                ], md=6, lg=3, className="mb-4"),
                
                # Locations Flagged (Combined)
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-exclamation-triangle", 
                                          style={'fontSize': '1.5rem', 'color': '#dc3545', 'marginBottom': '0.5rem'}),
                                ]),
                                html.H3([
                                    html.Span(str(kpis['properties_flagged']), 
                                             style={'color': '#dc3545', 'fontWeight': '700'}),
                                    html.Span(" / ", 
                                             style={'color': '#6c757d', 'fontWeight': '400'}),
                                    html.Span(str(kpis['total_properties']), 
                                             style={'color': '#6c757d', 'fontWeight': '700'})
                                ], className="mb-1",
                                style={'fontSize': '2.5rem'}),
                                html.P("Locations Flagged", 
                                      className="mb-2 text-muted",
                                      style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                                get_trend_indicator(kpis['trends'].get('flagged_properties_change', 0))
                            ])
                        ], style={'padding': '1.5rem'})
                    ], style={'border': 'none', 'borderRadius': '12px', 'height': '100%'})
                ], md=6, lg=3, className="mb-4"),
            ], className="g-3")
        ], style={'maxWidth': '1400px'})
        
        print(f"✅ Successfully created KPI HTML, returning to frontend")
        
    except Exception as e:
        print(f"❌ Error loading executive KPIs: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div("Error loading KPIs", style={'color': 'red', 'padding': '20px'})

# Update latest review date display
@app.callback(
    Output('hq-stats-latest-date', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def update_latest_date_display(screen, timeframe):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        # Set auth context
        property_service.set_auth_context(role='hq', property=None)
        
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        # Get review stats to fetch latest review date
        review_stats = property_service.get_summary_stats_from_reviews(days=days)
        latest_date = review_stats.get('latest_review_date', 'N/A')
        
        return html.Span([
            html.I(className="bi bi-calendar-event me-2", style={'fontSize': '0.85rem', 'color': '#6c757d'}),
            html.Span("Latest Review: ", style={'color': '#6c757d', 'fontSize': '0.85rem', 'fontWeight': '500'}),
            html.Span(latest_date, style={'color': '#495057', 'fontSize': '0.85rem', 'fontWeight': '600'})
        ])
    except Exception as e:
        print(f"⚠️ Error loading latest date: {str(e)}")
        return html.Div()

# Load properties map
@app.callback(
    Output('properties-map', 'figure'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def load_properties_map(screen, timeframe):
    print(f"\n{'='*60}")
    print(f"🗺️ LOAD_PROPERTIES_MAP CALLED")
    print(f"   screen: {screen}, timeframe: {timeframe}")
    print(f"{'='*60}\n")
    
    if screen != 'hq-properties':
        print(f"   ⏭️  Screen is '{screen}', returning empty figure")
        return go.Figure()
    
    try:
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        print(f"🔄 Loading properties map for screen: {screen}, days: {days}")
        properties = property_service.get_all_properties()
        print(f"   Got {len(properties)} properties")
        
        # Get flagged properties once with timeframe
        flagged = property_service.get_flagged_properties(days=days)
        flagged_ids = {f['property_id']: f for f in flagged}
        
        # Prepare map data
        map_data = []
        for prop in properties:
            # Use latitude/longitude from hotel_locations table
            lat = prop.get('latitude', 0)
            lon = prop.get('longitude', 0)
            
            # Skip if no valid coordinates
            if lat == 0 or lon == 0:
                continue
            
            # Determine status/color based on property health
            property_id = prop['property_id']
            
            if property_id in flagged_ids:
                # Property is flagged
                flagged_prop = flagged_ids[property_id]
                if flagged_prop['status'] == 'critical':
                    color = '#dc3545'  # Red
                    status = 'Critical'
                else:
                    color = '#ffc107'  # Yellow/Warning
                    status = 'Warning'
            else:
                # Property is healthy (no issues or no new reviews in timeframe)
                color = '#28a745'  # Green
                status = 'Healthy'
            
            map_data.append({
                'id': property_id,
                'name': prop['name'],
                'city': prop['city'],
                'state': prop['state'],
                'lat': lat,
                'lon': lon,
                'color': color,
                'status': status,
                'has_issues': prop.get('has_issues', False)
            })
        
        # Create figure
        fig = go.Figure()
        
        # Group by status for legend
        for status, color in [('Critical', '#dc3545'), ('Warning', '#ffc107'), ('Healthy', '#28a745')]:
            status_data = [d for d in map_data if d['status'] == status]
            if status_data:
                # Create helpful hover text
                hover_texts = []
                for d in status_data:
                    if d['has_issues']:
                        hover_text = f"<b>{d['name']}</b><br>Status: {d['status']}<br>Click to view details"
                    else:
                        hover_text = f"<b>{d['name']}</b><br>Status: {d['status']}<br>Click to view"
                    hover_texts.append(hover_text)
                
                # Make ALL properties clickable - pass metadata as JSON
                import json
                customdata = [json.dumps({
                    'property_id': d['id'],
                    'has_issues': d['has_issues'],
                    'has_reviews': d.get('has_reviews', True)  # Assume True if not explicitly False
                }) for d in status_data]
                
                fig.add_trace(go.Scattergeo(
                    lon=[d['lon'] for d in status_data],
                    lat=[d['lat'] for d in status_data],
                    mode='markers',
                    marker=dict(
                        size=12,
                        color=color,
                        line=dict(width=2, color='white'),
                        opacity=0.8
                    ),
                    name=status,
                    text=hover_texts,
                    customdata=customdata,
                    hovertemplate='%{text}<extra></extra>',
                ))
        
        # Update layout for US map
        fig.update_geos(
            scope='usa',
            projection_type='albers usa',
            showland=True,
            landcolor='rgb(243, 243, 243)',
            coastlinecolor='rgb(204, 204, 204)',
            showlakes=True,
            lakecolor='rgb(230, 240, 250)',
            showsubunits=True,
            subunitcolor='rgb(217, 217, 217)',
        )
        
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=500,
            showlegend=True,
            legend=dict(
                orientation='v',
                x=0.02,
                y=0.98,
                bgcolor='rgba(255, 255, 255, 0.9)',
                bordercolor='rgba(0, 0, 0, 0.2)',
                borderwidth=1
            ),
            hoverlabel=dict(
                bgcolor='white',
                font_size=13,
            )
        )
        
        print(f"✅ Loaded map with {len(map_data)} properties")
        return fig
        
    except Exception as e:
        print(f"❌ Error loading properties map: {str(e)}")
        import traceback
        traceback.print_exc()
        return go.Figure()

# Handle map clicks and navigate to HQ Health Dashboard
@app.callback(
    [Output('current-screen', 'data', allow_duplicate=True),
     Output('selected-property-id', 'data', allow_duplicate=True),
     Output('no-reviews-modal', 'is_open')],
    Input('properties-map', 'clickData'),
    prevent_initial_call=True
)
def handle_map_click(click_data):
    if not click_data:
        print("⚠️ Map clicked but no click_data")
        return dash.no_update, dash.no_update, dash.no_update
    
    try:
        # Extract property data from customdata (now a JSON string)
        customdata_str = click_data['points'][0].get('customdata')
        
        if not customdata_str:
            print("⚠️ Map clicked but no customdata")
            return dash.no_update, dash.no_update, dash.no_update
        
        import json
        property_data = json.loads(customdata_str)
        property_id = property_data['property_id']
        has_issues = property_data['has_issues']
        has_reviews = property_data.get('has_reviews', True)
        
        print(f"\n{'='*60}")
        print(f"🗺️ MAP CLICKED")
        print(f"   Property ID: {property_id}")
        print(f"   Has Issues: {has_issues}")
        print(f"   Has Reviews: {has_reviews}")
        
        # If healthy property with no reviews -> show modal
        if not has_issues and not has_reviews:
            print(f"   Action: Showing no-reviews modal")
            print(f"{'='*60}\n")
            return dash.no_update, dash.no_update, True
        
        # Otherwise -> navigate to dashboard
        print(f"   Action: Navigating to hq-dashboard")
        print(f"{'='*60}\n")
        return 'hq-dashboard', property_id, dash.no_update
        
    except Exception as e:
        print(f"❌ Error handling map click: {str(e)}")
        print(f"   click_data: {click_data}")
        import traceback
        traceback.print_exc()
        return dash.no_update, dash.no_update, dash.no_update

# Close no reviews modal
@app.callback(
    Output('no-reviews-modal', 'is_open', allow_duplicate=True),
    Input('close-no-reviews-modal', 'n_clicks'),
    State('no-reviews-modal', 'is_open'),
    prevent_initial_call=True
)
def close_no_reviews_modal(n_clicks, is_open):
    if n_clicks and is_open:
        return False
    return dash.no_update

# Handle severity threshold modal with pattern-matching
@app.callback(
    Output('severity-threshold-modal', 'is_open'),
    [Input({'type': 'open-severity-modal', 'view': dash.dependencies.ALL}, 'n_clicks'),
     Input('close-severity-modal', 'n_clicks')],
    State('severity-threshold-modal', 'is_open'),
    prevent_initial_call=True
)
def toggle_severity_modal(n_clicks_list, n_close, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_value = ctx.triggered[0]['value']  

    # Close button
    if triggered_id == 'close-severity-modal':
        return False
    
    # Any open button (pattern-matched)
    if 'open-severity-modal' in triggered_id:
        if triggered_value and triggered_value > 0:
            return True
        # return True
    
    return dash.no_update

# Load HQ property dropdown options
@app.callback(
    Output('hq-property-select', 'options'),
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_hq_property_options(screen):
    if screen != 'hq-dashboard':
        return dash.no_update
    
    try:
        properties = property_service.get_all_properties()
        
        # Separate properties with and without issues
        properties_with_issues = [p for p in properties if p.get('aspects')]
        properties_without_issues = [p for p in properties if not p.get('aspects')]
        
        # Sort each group alphabetically
        properties_with_issues.sort(key=lambda x: x['name'])
        properties_without_issues.sort(key=lambda x: x['name'])
        
        # Create options with visual differentiation
        options = []
        
        # Properties with issues first (with attention icon)
        for p in properties_with_issues:
            options.append({
                'label': f"📍 {p['name']}", 
                'value': p['property_id']
            })
        
        # Properties without issues at the bottom (with checkmark)
        for p in properties_without_issues:
            options.append({
                'label': f"✓ {p['name']} (No Issues)", 
                'value': p['property_id']
            })
        
        print(f"✅ Loaded {len(options)} properties for HQ dashboard dropdown")
        print(f"   📊 {len(properties_with_issues)} with issues, {len(properties_without_issues)} without issues")
        return options
    except Exception as e:
        print(f"⚠️  Error loading HQ dashboard properties: {str(e)}")
        return dash.no_update

# Sync HQ property dropdown with selected-property-id
@app.callback(
    Output('hq-property-select', 'value'),
    Input('selected-property-id', 'data'),
    State('current-screen', 'data'),
    prevent_initial_call=False
)
def sync_hq_property_dropdown(property_id, screen):
    if screen != 'hq-dashboard' or not property_id:
        return dash.no_update
    print(f"🔄 Syncing HQ dropdown to property: {property_id}")
    return property_id

# Update selected-property-id when HQ dropdown changes
@app.callback(
    Output('selected-property-id', 'data', allow_duplicate=True),
    Input('hq-property-select', 'value'),
    State('current-screen', 'data'),
    prevent_initial_call=True
)
def update_selected_property_from_hq_dropdown(property_id, screen):
    if screen != 'hq-dashboard' or not property_id:
        return dash.no_update
    print(f"📍 HQ dropdown changed to property: {property_id}")
    return property_id

# Load flagged properties grouped by region
@app.callback(
    Output('flagged-properties-grouped', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def load_flagged_properties_grouped(screen, timeframe):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        print(f"🔄 Loading grouped flagged properties for screen: {screen}, days: {days}")
        grouped_data = property_service.get_properties_by_region_and_severity(days=days)
        
        if not grouped_data:
            return dbc.Alert("✅ No properties flagged for attention.", color="success", className="mb-0")
        
        # Limit to top regions and add "Show More" option
        show_all_regions = len(grouped_data) <= 10
        regions_to_show = list(grouped_data.items())[:10] if not show_all_regions else list(grouped_data.items())
        
        accordion_items = []
        
        for region, properties in regions_to_show: 
            critical_count = len(properties['critical'])
            warning_count = len(properties['warning'])
            total_count = critical_count + warning_count
            
            # Create compact header with counts
            header_content = html.Div([
                html.Div([
                    html.Span(f"{region}", style={
                        'fontWeight': '600', 
                        'fontSize': '0.95rem',
                        'color': '#212529'
                    }),
                    html.Span([
                        dbc.Badge(f"{critical_count}", color="danger", className="ms-2 me-1",
                                style={'fontSize': '0.7rem', 'padding': '0.25rem 0.5rem', 'borderRadius': '4px'}) if critical_count > 0 else None,
                        html.Span("Critical", style={'fontSize': '0.75rem', 'color': '#6c757d', 'marginRight': '0.75rem'}) if critical_count > 0 else None,
                        dbc.Badge(f"{warning_count}", color="warning", className="me-1",
                                style={'fontSize': '0.7rem', 'padding': '0.25rem 0.5rem', 'borderRadius': '4px', 'color': '#000'}) if warning_count > 0 else None,
                        html.Span("Warning", style={'fontSize': '0.75rem', 'color': '#6c757d'}) if warning_count > 0 else None,
                    ], style={'display': 'inline-block', 'marginLeft': '0.5rem'}),
                ], style={'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'width': '100%'}),
            ])
            
            # Create property cards for this region
            region_properties = []
            
            # Add critical properties first
            for prop in properties['critical']:
                # Build inline aspects display
                aspects_chips = []
                for i, aspect in enumerate(prop['aspects']):
                    if i > 0:
                        aspects_chips.append(html.Span(" • ", style={'color': '#dee2e6', 'margin': '0 0.3rem'}))
                    aspects_chips.append(
                        html.Span([
                            html.Span(f"{aspect['aspect'].replace('_', ' ').title()}", 
                                     style={'fontWeight': '500', 'color': '#495057'}),
                            html.Span(f" {int(round(aspect['negative_percentage']*100))}%", 
                                     style={'color': '#dc3545', 'fontWeight': '600'})
                        ], style={'fontSize': '0.8rem'})
                    )
                
                region_properties.append(
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    # Left: Property name and badge
                                    html.Div([
                                        html.Span(prop['property'], style={
                                            'fontWeight': '600', 
                                            'fontSize': '0.95rem', 
                                            'color': '#212529'
                                        }),
                                        dbc.Badge("Critical", color="danger", className="ms-2",
                                                style={'fontSize': '0.65rem', 'padding': '0.25rem 0.5rem'})
                                    ], style={'minWidth': '180px', 'display': 'flex', 'alignItems': 'center'}),
                                    
                                    # Middle: All aspects inline
                                    html.Div(aspects_chips, style={
                                        'flex': '1',
                                        'display': 'flex',
                                        'flexWrap': 'wrap',
                                        'alignItems': 'center',
                                        'marginLeft': '1rem',
                                        'marginRight': '1rem'
                                    }),
                                    
                                    # Right: View button
                                    dbc.Button(
                                        "View", 
                                        color="danger", 
                                        size="sm",
                                        style={'fontWeight': '500', 'padding': '0.4rem 1rem', 'fontSize': '0.8rem'},
                                        id={'type': 'view-property-btn', 'index': prop['property_id']},
                                        n_clicks=0
                                    )
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'space-between',
                                    'gap': '1rem'
                                })
                            ], style={'padding': '0.75rem 1rem'})
                        ], style={
                            'border': '1px solid #dc3545',
                            'borderLeft': '4px solid #dc3545',
                            'borderRadius': '6px',
                            'backgroundColor': '#fff5f5',
                            'marginBottom': '0.5rem'
                        }, className="hover-shadow")
                    ], id=f"property-card-{prop['property_id']}", style={'scrollMarginTop': '100px'})
                )
            
            # Add warning properties
            for prop in properties['warning']:
                # Build inline aspects display
                aspects_chips = []
                for i, aspect in enumerate(prop['aspects']):
                    if i > 0:
                        aspects_chips.append(html.Span(" • ", style={'color': '#dee2e6', 'margin': '0 0.3rem'}))
                    aspects_chips.append(
                        html.Span([
                            html.Span(f"{aspect['aspect'].replace('_', ' ').title()}", 
                                     style={'fontWeight': '500', 'color': '#495057'}),
                            html.Span(f" {int(round(aspect['negative_percentage']*100))}%", 
                                     style={'color': '#f39c12', 'fontWeight': '600'})
                        ], style={'fontSize': '0.8rem'})
                    )
                
                region_properties.append(
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    # Left: Property name and badge
                                    html.Div([
                                        html.Span(prop['property'], style={
                                            'fontWeight': '600', 
                                            'fontSize': '0.95rem', 
                                            'color': '#212529'
                                        }),
                                        dbc.Badge("Warning", color="warning", className="ms-2",
                                                style={'fontSize': '0.65rem', 'padding': '0.25rem 0.5rem', 'color': '#000'})
                                    ], style={'minWidth': '180px', 'display': 'flex', 'alignItems': 'center'}),
                                    
                                    # Middle: All aspects inline
                                    html.Div(aspects_chips, style={
                                        'flex': '1',
                                        'display': 'flex',
                                        'flexWrap': 'wrap',
                                        'alignItems': 'center',
                                        'marginLeft': '1rem',
                                        'marginRight': '1rem'
                                    }),
                                    
                                    # Right: View button
                                    dbc.Button(
                                        "View", 
                                        color="warning", 
                                        size="sm",
                                        style={'fontWeight': '500', 'padding': '0.4rem 1rem', 'fontSize': '0.8rem', 'color': '#000'},
                                        id={'type': 'view-property-btn', 'index': prop['property_id']},
                                        n_clicks=0
                                    )
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'space-between',
                                    'gap': '1rem'
                                })
                            ], style={'padding': '0.75rem 1rem'})
                        ], style={
                            'border': '1px solid #ffc107',
                            'borderLeft': '4px solid #ffc107',
                            'borderRadius': '6px',
                            'backgroundColor': '#fffbf0',
                            'marginBottom': '0.5rem'
                        }, className="hover-shadow")
                    ], id=f"property-card-{prop['property_id']}", style={'scrollMarginTop': '100px'})
                )
            
            # Create accordion item with compact styling
            accordion_items.append(
                dbc.AccordionItem(
                    html.Div(region_properties, style={'marginTop': '0.5rem'}),
                    title=header_content,
                    item_id=f"region-{region}",
                    style={'marginBottom': '0.5rem'}
                )
            )
        
        # Add "Show More" button if there are more regions
        accordion_content = [
            dbc.Accordion(
                accordion_items,
                start_collapsed=False,  # Start expanded so map clicks can scroll to visible properties
                always_open=True,
                flush=True,
                style={'marginBottom': '1rem'}
            )
        ]
        
        if not show_all_regions:
            accordion_content.append(
                dbc.Button(
                    [html.I(className="bi bi-chevron-down me-2"), f"Show {len(grouped_data) - 10} More Regions"],
                    id="btn-show-more-regions",
                    color="secondary",
                    outline=True,
                    size="sm",
                    style={'fontWeight': '500', 'fontSize': '0.85rem'},
                    className="mt-2"
                )
            )
        
        return html.Div(accordion_content)
        
    except Exception as e:
        print(f"❌ Error loading grouped flagged properties: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading flagged properties: {str(e)}", color="danger")

# Load all properties summary with expand/collapse
@app.callback(
    Output('all-properties-summary', 'children'),
    [Input('current-screen', 'data'),
     Input('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=False
)
def load_all_properties_summary(screen, timeframe):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        print(f"🔄 Loading all properties summary for screen: {screen}, days: {days}")
        properties = property_service.get_all_properties()
        
        # Get flagged properties to exclude them with timeframe
        flagged = property_service.get_flagged_properties(days=days)
        flagged_property_ids = set(prop['property_id'] for prop in flagged)
        
        # Filter out flagged properties
        non_flagged_properties = [
            prop for prop in properties 
            if prop['property_id'] not in flagged_property_ids
        ]
        
        healthy_count = len(non_flagged_properties)
        
        print(f"✅ Loaded {len(properties)} total properties, {healthy_count} healthy")
        
        # Create summary card
        return dbc.Card([
            dbc.CardBody([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.H4("✅ All Properties", className="mb-2", style={'fontWeight': '600'}),
                            html.P([
                                html.Span(f"{healthy_count}", style={'fontSize': '2rem', 'fontWeight': '700', 'color': '#198754'}),
                                html.Span(" properties not requiring immediate attention", 
                                         style={'fontSize': '1rem', 'color': '#6c757d', 'marginLeft': '0.5rem'})
                            ], className="mb-3"),
                            html.P("These properties have no critical issues or warnings in the current timeframe.", 
                                  className="text-muted mb-3", style={'fontSize': '0.95rem'}),
                            dbc.Button(
                                [html.I(className="bi bi-chevron-down me-2"), "View All Healthy Properties"],
                                id="btn-toggle-all-properties",
                                color="success",
                                outline=True,
                                size="sm",
                                style={'fontWeight': '500'},
                                n_clicks=0
                            )
                        ])
                    ], md=12),
                ]),
                html.Hr(className="my-3"),
                dbc.Collapse(
                    html.Div(id='all-properties-expanded-list'),
                    id="collapse-all-properties",
                    is_open=False
                )
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
        
    except Exception as e:
        print(f"❌ Error loading all properties summary: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading all properties: {str(e)}", color="danger")

# Toggle all properties expanded list
@app.callback(
    [Output("collapse-all-properties", "is_open"),
     Output("btn-toggle-all-properties", "children")],
    [Input("btn-toggle-all-properties", "n_clicks")],
    [State("collapse-all-properties", "is_open")],
    prevent_initial_call=True
)
def toggle_all_properties(n_clicks, is_open):
    if n_clicks:
        new_state = not is_open
        button_text = [
            html.I(className=f"bi bi-chevron-{'up' if new_state else 'down'} me-2"),
            f"{'Hide' if new_state else 'View All'} Healthy Properties"
        ]
        return new_state, button_text
    return is_open, dash.no_update

# Load expanded properties list with accordion layout
@app.callback(
    Output('all-properties-expanded-list', 'children'),
    Input('collapse-all-properties', 'is_open'),
    [State('current-screen', 'data'),
     State('hq-stats-timeframe-selector', 'value')],
    prevent_initial_call=True
)
def load_expanded_properties_list(is_open, screen, timeframe):
    if not is_open or screen != 'hq-properties':
        return html.Div()
    
    try:
        # Convert 'all' to None for historical data
        days = None if timeframe == 'all' else timeframe
        
        # Get grouped healthy properties with timeframe
        grouped_properties = property_service.get_healthy_properties_grouped(days=days)
        healthy = grouped_properties['healthy']
        no_reviews = grouped_properties['no_reviews']
        
        print(f"✅ Loaded {len(healthy)} healthy properties, {len(no_reviews)} properties with no reviews")
        
        accordion_items = []
        
        # Healthy Properties Accordion
        if healthy:
            healthy_props = []
            for prop in healthy:
                healthy_props.append(
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    # Left: Property name + location
                                    html.Div([
                                        html.Span(prop['name'], style={
                                            'fontWeight': '600', 
                                            'fontSize': '0.95rem', 
                                            'color': '#212529'
                                        }),
                                        html.Span(f" • {prop['city']}, {prop['state']}", style={
                                            'fontSize': '0.85rem',
                                            'color': '#6c757d',
                                            'marginLeft': '0.5rem'
                                        })
                                    ], style={'flex': '1'}),
                                    
                                    # Right: View button
                                    dbc.Button(
                                        "View", 
                                        color="success", 
                                        size="sm",
                                        style={'fontWeight': '500', 'padding': '0.4rem 1rem', 'fontSize': '0.8rem'},
                                        id={'type': 'view-property-btn', 'index': prop['property_id']},
                                        n_clicks=0
                                    )
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'space-between',
                                    'gap': '1rem'
                                })
                            ], style={'padding': '0.75rem 1rem'})
                        ], style={
                            'border': '1px solid #28a745',
                            'borderLeft': '4px solid #28a745',
                            'borderRadius': '6px',
                            'backgroundColor': '#f0fff4',
                            'marginBottom': '0.5rem'
                        }, className="hover-shadow")
                    ], id=f"property-card-{prop['property_id']}", style={'scrollMarginTop': '100px'})
                )
            
            accordion_items.append(
                dbc.AccordionItem(
                    html.Div(healthy_props, style={'marginTop': '0.5rem'}),
                    title=html.Div([
                        html.Span("🌟 Healthy ", style={'fontWeight': '600'}),
                        html.Span(f"({len(healthy)} properties)", style={'color': '#6c757d'})
                    ]),
                    item_id="healthy-properties"
                )
            )
        
        # No Reviews Properties Accordion
        if no_reviews:
            no_reviews_props = []
            for prop in no_reviews:
                no_reviews_props.append(
                    html.Div([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    # Left: Property name + location
                                    html.Div([
                                        html.Span(prop['name'], style={
                                            'fontWeight': '600', 
                                            'fontSize': '0.95rem', 
                                            'color': '#212529'
                                        }),
                                        html.Span(f" • {prop['city']}, {prop['state']}", style={
                                            'fontSize': '0.85rem',
                                            'color': '#6c757d',
                                            'marginLeft': '0.5rem'
                                        })
                                    ], style={'flex': '1'}),
                                    
                                    # Right: View button
                                    dbc.Button(
                                        "View", 
                                        color="secondary", 
                                        size="sm",
                                        style={'fontWeight': '500', 'padding': '0.4rem 1rem', 'fontSize': '0.8rem'},
                                        id={'type': 'view-property-btn', 'index': prop['property_id']},
                                        n_clicks=0
                                    )
                                ], style={
                                    'display': 'flex',
                                    'alignItems': 'center',
                                    'justifyContent': 'space-between',
                                    'gap': '1rem'
                                })
                            ], style={'padding': '0.75rem 1rem'})
                        ], style={
                            'border': '1px solid #6c757d',
                            'borderLeft': '4px solid #6c757d',
                            'borderRadius': '6px',
                            'backgroundColor': '#f8f9fa',
                            'marginBottom': '0.5rem'
                        }, className="hover-shadow")
                    ], id=f"property-card-{prop['property_id']}", style={'scrollMarginTop': '100px'})
                )
            
            accordion_items.append(
                dbc.AccordionItem(
                    html.Div(no_reviews_props, style={'marginTop': '0.5rem'}),
                    title=html.Div([
                        html.Span("📭 No New Reviews ", style={'fontWeight': '600'}),
                        html.Span(f"({len(no_reviews)} properties)", style={'color': '#6c757d'})
                    ]),
                    item_id="no-reviews-properties"
                )
            )
        
        return dbc.Accordion(
            accordion_items,
            start_collapsed=False,
            always_open=True,
            flush=True,
            style={'marginTop': '1rem'}
        )
        
    except Exception as e:
        print(f"❌ Error loading expanded properties: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading properties: {str(e)}", color="danger")

# Note: Healthy property cards now use same view-property-btn pattern as flagged properties
# No separate table click handler needed - accordion cards have View buttons

# NOTE: Analytics charts callback removed - replaced with embedded Databricks dashboard
# The HQ Overview Dashboard (01f0b5d2c21513ac8ab86f43c6fd0dc3) is now embedded directly
# in the HQ Properties page, replacing the previous trend/aspect/regional charts

# OLD CALLBACK REMOVED (kept for reference):
# @app.callback(
#     [Output('trend-chart-container', 'children'),
#      Output('aspect-breakdown-chart', 'children'),
#      Output('regional-comparison-chart', 'children')],
#     Input('hq-executive-kpis', 'children'),
#     State('current-screen', 'data'),
#     prevent_initial_call=False
# )
# def load_analytics_charts(kpis_loaded, screen):
#     # Replaced with embedded Databricks dashboard
#     pass


# Handle property selection using pattern-matching
@app.callback(
    [Output('selected-property-id', 'data'),
     Output('current-screen', 'data', allow_duplicate=True)],
    Input({'type': 'view-property-btn', 'index': dash.dependencies.ALL}, 'n_clicks'),
    State('current-screen', 'data'),
    prevent_initial_call='initial_duplicate'  # Allow on initial load but track duplicates
)
def select_property(n_clicks_list, current_screen):
    print(f"\n{'='*80}")
    print(f"👆 SELECT_PROPERTY CALLBACK!")
    print(f"   current_screen: {current_screen}")
    print(f"   n_clicks_list length: {len(n_clicks_list) if n_clicks_list else 0}")
    
    # Check which button was clicked
    ctx = dash.callback_context
    
    if not ctx.triggered:
        print(f"   ❌ No trigger, returning no_update")
        print(f"{'='*80}\n")
        return dash.no_update, dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    triggered_value = ctx.triggered[0]['value']
    print(f"   triggered_id string: {triggered_id}")
    print(f"   triggered_value: {triggered_value}")
    
    if triggered_id == '' or triggered_id == '{}':
        print(f"   ❌ Empty trigger, returning no_update")
        print(f"{'='*80}\n")
        return dash.no_update, dash.no_update
    
    # Parse the property ID from the triggered component
    import json
    try:
        button_id = json.loads(triggered_id)
        
        # Verify it's a view-property-btn
        if button_id.get('type') != 'view-property-btn':
            print(f"   ⏭️  Not a view-property button, ignoring")
            print(f"{'='*80}\n")
            return dash.no_update, dash.no_update
        
        property_id = button_id['index']
        
        # Check if this is an actual click (triggered by user interaction)
        # After a button click, n_clicks should be >= 1
        # Note: triggered_value could be None if button just rendered, or 0 if initialized but not clicked
        if triggered_value is None:
            print(f"   ⚠️  triggered_value is None - button may have just been created")
            print(f"   ✅ Allowing navigation anyway (user clearly clicked)")
            # Don't return no_update - let it proceed
        elif triggered_value == 0:
            print(f"   ⏭️  No click detected (n_clicks=0), ignoring")
            print(f"{'='*80}\n")
            return dash.no_update, dash.no_update
        
        print(f"   ✅ Property selected: {property_id}")
        print(f"   🔄 Navigating to hq-dashboard...")
        print(f"   Returning: ({property_id}, 'hq-dashboard')")
        print(f"{'='*80}\n")
        
        return property_id, 'hq-dashboard'
    except Exception as e:
        print(f"   ❌ Error parsing trigger: {e}")
        print(f"   traceback: {e.__class__.__name__}")
        import traceback
        traceback.print_exc()
        print(f"{'='*80}\n")
        return dash.no_update, dash.no_update

# Load property details in HQ dashboard
@app.callback(
    Output('hq-selected-property-details-container', 'children'),
    [Input('selected-property-id', 'data'),
     Input('current-screen', 'data')]
)
def load_property_details(property_id, screen):
    print(f"🏨 load_property_details called: property_id={property_id}, screen={screen}")
    if screen != 'hq-dashboard' or not property_id:
        print(f"   ⏭️  Skipping property details")
        return html.Div()
    
    try:
        print(f"   🔄 Fetching property details for {property_id}...")
        details = property_service.get_property_details(property_id)
        if not details:
            print(f"   ⚠️  No Reviews Found For Property!")
            return dbc.Alert("No Reviews Found For Property.", color="warning")
        print(f"   ✅ Property details loaded!")
        
        return dbc.Card([
            dbc.CardBody([
                # Property Header with location badge
                dbc.Row([
                    dbc.Col([
                        html.H2(details['name'], className="mb-2", style={'fontWeight': '700', 'fontSize': '2rem'}),
                        html.Div([
                            html.I(className="bi bi-geo-alt-fill me-2", style={'color': '#dc3545'}),
                            html.Span(f"{details['city']}, {details['state']}", 
                                     style={'fontSize': '1.1rem', 'fontWeight': '500', 'color': '#495057'}),
                        ], className="mb-2"),
                        html.P([
                            html.Span(f"{details['reviews_count']} reviews", className="me-3"),
                            html.Span(f"Rating: {details['avg_rating']}/5.0", className="me-3"),
                        ], className="text-muted", style={'fontSize': '0.95rem'}),
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(
                            f"📍 {details['city']}, {details['state']}", 
                            color="danger",
                            className="p-3",
                            style={'fontSize': '1rem', 'fontWeight': '500'}
                        ),
                    ], md=4, className="text-end d-flex align-items-center justify-content-end"),
                ], className="mb-4"),
                
            ], style={'padding': '2rem'})
        ], style={'border': 'none', 'borderRadius': '12px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'})
    except Exception as e:
        return dbc.Alert(f"Error loading property details: {str(e)}", color="danger")

# Load aspect analysis table in Tab 2
@app.callback(
    Output('hq-aspect-analysis-table', 'children'),
    [Input('selected-property-id', 'data'),
     Input('current-screen', 'data')],
    prevent_initial_call=False
)
def load_aspect_analysis_table(property_id, screen):
    if screen != 'hq-dashboard' or not property_id:
        return html.Div()
    
    try:
        details = property_service.get_property_details(property_id)
        if not details or 'aspects' not in details:
            return html.Div()
        
        # Create aspects table
        aspects_data = []
        for aspect in details['aspects']:
            aspects_data.append({
                'Aspect': aspect['name'],
                'Negative Reviews': f"{round(aspect['percentage']*100, 1)}%",
                'Status': aspect['status'].upper()
            })
        
        if not aspects_data:
            return html.Div()
        
        # Create HTML table rows
        table_rows = []
        for aspect_item in aspects_data:
            status = aspect_item['Status']
            if 'CRITICAL' in status:
                row_style = {'backgroundColor': '#ffebee', 'color': custom_style['critical'], 'fontWeight': '500'}
            elif 'WARNING' in status:
                row_style = {'backgroundColor': '#fff9c4', 'color': custom_style['warning'], 'fontWeight': '500'}
            else:
                row_style = {}
            
            table_rows.append(
                html.Tr([
                    html.Td(aspect_item['Aspect'], style={'padding': '12px'}),
                    html.Td(aspect_item['Negative Reviews'], style={'padding': '12px', 'textAlign': 'center'}),
                    html.Td(dbc.Badge(status, color='danger' if 'CRITICAL' in status else 'warning' if 'WARNING' in status else 'success'), 
                           style={'padding': '12px', 'textAlign': 'center'}),
                ], style=row_style)
            )
        
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H4("📋 Aspect Analysis", className="mb-0 d-inline-block", style={'fontWeight': '600'}),
                    html.I(
                        className="bi bi-info-circle ms-2",
                        id={'type': 'open-severity-modal', 'view': 'hq-aspect'},
                        style={
                            'fontSize': '1.1rem',
                            'color': '#0d6efd',
                            'cursor': 'pointer',
                            'verticalAlign': 'middle'
                        },
                        title="Click to view severity threshold logic",
                        n_clicks=0
                    ),
                ], className="mb-3", style={'display': 'flex', 'alignItems': 'center'}),
                html.P([
                    "Overview of all aspects and their performance. ",
                    html.Strong("Negative Reviews %"), 
                    " shows the overall negative sentiment rate for this aspect."
                ], 
                      className="text-muted mb-3",
                      style={'fontSize': '0.95rem'}),
                dbc.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Aspect", style={'padding': '12px', 'fontSize': '1rem'}),
                            html.Th("Negative Reviews", style={'padding': '12px', 'fontSize': '1rem', 'textAlign': 'center'}),
                            html.Th("Status", style={'padding': '12px', 'fontSize': '1rem', 'textAlign': 'center'}),
                        ]),
                        style={'backgroundColor': custom_style['primary'], 'color': 'white', 'fontWeight': 'bold'}
                    ),
                    html.Tbody(table_rows)
                ], bordered=True, hover=True, responsive=True, striped=True,
                   style={'fontSize': '0.95rem'})
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
    except Exception as e:
        print(f"Error loading aspect analysis table: {str(e)}")
        return html.Div()

# Load filtered dashboard iframe based on selected property
@app.callback(
    Output('hq-filtered-dashboard-iframe', 'children'),
    [Input('selected-property-id', 'data'),
     Input('current-screen', 'data')]
)
def load_filtered_dashboard(property_id, screen):
    if screen != 'hq-dashboard' or not property_id:
        return html.Div()
    
    try:
        # Get property details to extract location
        details = property_service.get_property_details(property_id)
        if not details:
            return dbc.Alert("No Reviews Found For Property.", color="warning")
        
        # Construct location string
        location = f"{details['city']}, {details['state']}"
        
        # Original Property Dashboard URL (keep this one for property details)
        base_url_property = os.getenv('DATABRICKS_PROPERTY_DASHBOARD_URL')
        # "https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/embed/dashboardsv3/01f0ab936a8815ffbc5b0dd3d8ca0f9f"
        
        # Add location filter parameter
        from urllib.parse import quote
        encoded_location = quote(quote(location, safe=''), safe='')
        filtered_url = f"{base_url_property}&f_property_rating%7E57a7e64b={encoded_location}"

        print(f"🗺️ Loading dashboard filtered for location: {location}")
        print(f"📊 Dashboard URL: {filtered_url}")
        
        return html.Div([
            html.Div([
                html.I(className="bi bi-funnel me-2", style={'color': '#6c757d'}),
                html.Span(f"Filtered by: {location}", 
                         style={'color': '#6c757d', 'fontSize': '0.9rem', 'fontWeight': '500'})
            ], className="mb-3"),
            html.Iframe(
                src=filtered_url,
                style={
                    'width': '100%',
                    'height': '800px',
                    'border': 'none',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
                }
            ),
        ])
        
    except Exception as e:
        print(f"❌ Error loading filtered dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Error loading dashboard: {str(e)}", color="danger")

# Load aspect options for Reviews Deep Dive
@app.callback(
    Output('hq-aspect-selector', 'options'),
    [Input('selected-property-id', 'data'),
     Input('current-screen', 'data'),
     Input('hq-selected-property-details-container', 'children')],  # Trigger after property details load
    prevent_initial_call=False
)
def load_aspect_options(property_id, screen, _details):
    print(f"🔍 load_aspect_options called: property_id={property_id}, screen={screen}")
    if screen != 'hq-dashboard' or not property_id:
        print(f"   ⏭️  Skipping - screen is '{screen}' (need 'hq-dashboard') or property_id not set")
        return dash.no_update
    
    try:
        print(f"   🔄 Fetching aspects for {property_id}...")
        deep_dive_data = property_service.get_reviews_deep_dive(property_id)
        aspects = deep_dive_data.get('aspects', [])
        print(f"   ✅ Loaded {len(aspects)} aspects: {aspects}")
        options = [{'label': aspect, 'value': aspect} for aspect in aspects]
        print(f"   ✅ Returning {len(options)} options")
        return options
    except Exception as e:
        print(f"   ⚠️  Error loading aspects: {str(e)}")
        import traceback
        traceback.print_exc()
        return dash.no_update

# Load Reviews Deep Dive content
@app.callback(
    Output('hq-reviews-deep-dive-content', 'children'),
    [Input('hq-aspect-selector', 'value'),
     Input('selected-property-id', 'data'),
     Input('current-screen', 'data')],
    prevent_initial_call=False
)
def load_reviews_deep_dive(selected_aspect, property_id, screen):
    print(f"📊 load_reviews_deep_dive called: aspect={selected_aspect}, property_id={property_id}, screen={screen}")
    if screen != 'hq-dashboard' or not property_id or not selected_aspect:
        print(f"   ⏭️  Skipping - not all conditions met")
        return html.Div()
    
    try:
        # Get property details to fetch correct status (consistent with table)
        details = property_service.get_property_details(property_id)
        
        # Get deep dive data
        deep_dive_data = property_service.get_reviews_deep_dive(property_id, selected_aspect)
        deep_dive = deep_dive_data.get('deep_dive')
        
        if not deep_dive:
            return dbc.Alert("No data available for this aspect.", color="info")
        
        # Find the correct status from property details for this aspect (same as table)
        correct_status = None
        if details and 'aspects' in details:
            for aspect_info in details['aspects']:
                if aspect_info['name'] == selected_aspect:
                    correct_status = aspect_info['status']
                    break
        
        # Use correct_status from table instead of deep_dive['severity']
        severity = correct_status if correct_status else deep_dive['severity']
        severity_color = 'danger' if severity.lower() == 'critical' else ('warning' if severity.lower() == 'warning' else 'success')
        
        return dbc.Card([
            dbc.CardBody([
                # Header with metrics
                dbc.Row([
                    dbc.Col([
                        html.H5(deep_dive['aspect'], className="mb-2", style={'fontWeight': '600'}),
                        dbc.Badge(
                            severity, 
                            color=severity_color, 
                            className="me-2",
                            style={'fontSize': '0.875rem'}
                        ),
                        html.Br(),
                        html.Small(f"Issue opened: {deep_dive['date_opened']}", className="text-muted d-block"),
                        html.Small([
                            html.Strong("Reason: ", style={'color': '#495057'}),
                            html.Span(deep_dive.get('open_reason', 'Not specified'), style={'color': '#6c757d'})
                        ], className="text-muted d-block mt-1"),
                    ], md=8),
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3(f"{deep_dive['volume_percentage']}%", 
                                       className="mb-0",
                                       style={'fontWeight': '700', 'color': '#dc3545'}),
                                html.Small("Volume", className="text-muted"),
                            ], className="text-center mb-3"),
                            html.Div([
                                html.H4(f"{deep_dive['total_reviews']}", 
                                       className="mb-0",
                                       style={'fontWeight': '600'}),
                                html.Small("Total Reviews", className="text-muted d-block"),
                                html.Small("7-day window", className="text-muted d-block", style={'fontSize': '0.7rem'})
                            ], className="text-center"),
                        ])
                    ], md=4, className="text-center"),
                ], className="mb-4"),
                
                html.Hr(),
                
                # Issue Summary
                html.Div([
                    html.H6("📝 Issue Summary", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['issue_summary'], className="mb-4", style={'lineHeight': '1.6'}),
                ]),
                
                # Review Counts
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H3(deep_dive['negative_count'], 
                                           className="mb-1",
                                           style={'fontWeight': '700', 'color': '#dc3545'}),
                                    html.P("Negative Reviews", className="mb-0 text-muted", style={'fontSize': '0.9rem'}),
                                ], className="text-center")
                            ], style={'padding': '1rem'})
                        ], style={'border': '2px solid #dc3545', 'borderRadius': '8px', 'backgroundColor': '#fff5f5'}),
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H3(deep_dive['positive_count'], 
                                           className="mb-1",
                                           style={'fontWeight': '700', 'color': '#28a745'}),
                                    html.P("Positive Reviews", className="mb-0 text-muted", style={'fontSize': '0.9rem'}),
                                ], className="text-center")
                            ], style={'padding': '1rem'})
                        ], style={'border': '2px solid #28a745', 'borderRadius': '8px', 'backgroundColor': '#f1f9f3'}),
                    ], md=6),
                ], className="mb-4"),
                
                # Root Cause Analysis
                html.Div([
                    html.H6("🔍 Potential Root Cause", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['potential_root_cause'], 
                          className="mb-4",
                          style={'lineHeight': '1.6', 'backgroundColor': '#f8f9fa', 'padding': '1rem', 'borderRadius': '8px'}),
                ]),
                
                # Impact
                html.Div([
                    html.H6("📊 Impact", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['impact'], 
                          className="mb-4",
                          style={'lineHeight': '1.6', 'backgroundColor': '#fff3cd', 'padding': '1rem', 'borderRadius': '8px'}),
                ]),
                
                # Recommended Action
                html.Div([
                    html.H6("✅ Recommended Action", className="mb-2", style={'fontWeight': '600'}),
                    dbc.Alert(
                        deep_dive['recommended_action'],
                        color="success",
                        className="mb-0",
                        style={'lineHeight': '1.6', 'fontWeight': '500'}
                    ),
                ]),
                
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
        
    except Exception as e:
        return dbc.Alert(f"Error loading deep dive: {str(e)}", color="danger")

# Load Individual Reviews Browser Controls (separate from deep dive content)
@app.callback(
    Output('hq-review-browser-controls', 'children'),
    [Input('hq-aspect-selector', 'value'),
     Input('selected-property-id', 'data'),
     Input('current-screen', 'data')],
    prevent_initial_call=False
)
def load_hq_review_browser_controls(selected_aspect, property_id, screen):
    """Render the review browser controls (timeframe dropdown and filter buttons)"""
    if screen != 'hq-dashboard' or not property_id or not selected_aspect:
        return html.Div()
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("📝 Individual Reviews", className="mb-3", style={'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Label("Timeframe:", style={'fontWeight': '500', 'marginBottom': '0.5rem'}),
                    dcc.Dropdown(
                        id='hq-review-timeframe-selector',
                        options=[
                            {'label': 'Last 7 days', 'value': 7},
                            {'label': 'Last 14 days', 'value': 14},
                            {'label': 'Last 30 days', 'value': 30}
                        ],
                        value=14,  # Default to 14 days
                        clearable=False,
                        style={'width': '100%'},
                        optionHeight=35
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Show Reviews:", style={'fontWeight': '500', 'marginBottom': '0.5rem'}),
                    dbc.RadioItems(
                        id='hq-review-filter',
                        options=[
                            {'label': 'All Reviews', 'value': 'all'},
                            {'label': 'Negative Only', 'value': 'negative'},
                            {'label': 'Positive Only', 'value': 'positive'}
                        ],
                        value='all',  # Default to show all
                        inline=True,
                        style={'marginTop': '0.25rem'}
                    ),
                ], md=6),
            ], className="mb-3"),
        ], style={'padding': '1.5rem'})
    ], style={'border': 'none', 'borderRadius': '12px', 'backgroundColor': '#f8f9fa'})

# Helper function to render Genie messages
def render_genie_message(message, is_user=False):
    """Render a single message in chat-like UI"""
    if is_user:
        return html.Div([
            html.Div([
                html.Div([
                    html.I(className="bi bi-person-circle", style={'fontSize': '1.5rem', 'marginRight': '0.75rem'}),
                    html.Div([
                        html.Strong("You", style={'fontSize': '0.85rem', 'color': '#6c757d', 'display': 'block', 'marginBottom': '0.25rem'}),
                        html.P(message.get('query', ''), style={'margin': '0', 'fontSize': '0.95rem'})
                    ])
                ], style={'display': 'flex', 'alignItems': 'start'})
            ], style={
                'backgroundColor': '#e7f1ff',
                'padding': '1rem',
                'borderRadius': '12px',
                'marginBottom': '0.75rem',
                'border': '1px solid #b6d7ff'
            })
        ], style={'marginBottom': '1rem'})
    
    else:
        # Genie response
        components = []
        
        # Check if there's an error
        if message.get('error'):
            components.append(
                html.Div([
                    html.I(className="bi bi-exclamation-triangle-fill me-2", style={'color': '#dc3545'}),
                    html.Span(f"Error: {message['error']}", style={'fontSize': '0.95rem'})
                ], style={'color': '#dc3545', 'padding': '0.5rem', 'backgroundColor': '#f8d7da', 'borderRadius': '6px', 'border': '1px solid #f5c2c7'})
            )
        
        for idx, item in enumerate(message.get('results', [])):
            if item['type'] == 'text':
                components.append(
                    html.P(item['content'], style={'margin': '0 0 0.5rem 0', 'fontSize': '0.95rem', 'lineHeight': '1.6'})
                )
            
            elif item['type'] == 'table':
                query_text = item.get('query', 'No query available')
                description = item.get('description', 'Query Results')
                
                components.append(
                    html.Div([
                        html.Div([
                            html.I(className="bi bi-table me-2", style={'color': '#198754'}),
                            html.Strong(description, style={'fontSize': '0.95rem'}),
                        ], style={'marginBottom': '0.5rem'}),
                        
                        dbc.Accordion([
                            dbc.AccordionItem([
                                html.Pre(
                                    query_text,
                                    style={
                                        'backgroundColor': '#2d2d2d',
                                        'color': '#f8f8f2',
                                        'padding': '0.75rem',
                                        'borderRadius': '6px',
                                        'fontSize': '0.8rem',
                                        'overflowX': 'auto',
                                        'marginBottom': '0',
                                        'fontFamily': 'Monaco, Consolas, monospace'
                                    }
                                )
                            ], title="📝 SQL", item_id=f"msg-sql-{idx}")
                        ], start_collapsed=True, className="mb-2", style={'fontSize': '0.85rem'}),
                        
                        (lambda data, cols: 
                            html.Div([
                                html.Small(f"{len(data)} rows", style={'color': '#6c757d', 'display': 'block', 'marginBottom': '0.5rem'}),
                                (lambda:
                                    # Try to infer columns from first row if not provided
                                    (lambda inferred_cols:
                                        dash_table.DataTable(
                                            data=data,
                                            columns=[{'name': col, 'id': col} for col in inferred_cols],
                                            style_cell={
                                                'textAlign': 'left',
                                                'padding': '8px',
                                                'fontSize': '0.85rem',
                                                'fontFamily': 'inherit'
                                            },
                                            style_header={
                                                'backgroundColor': '#198754',
                                                'color': 'white',
                                                'fontWeight': 'bold',
                                                'fontSize': '0.85rem'
                                            },
                                            style_data={
                                                'border': '1px solid #dee2e6'
                                            },
                                            style_data_conditional=[
                                                {
                                                    'if': {'row_index': 'odd'},
                                                    'backgroundColor': '#f8f9fa'
                                                }
                                            ],
                                            page_size=5,
                                        ) if inferred_cols else (
                                            # If no proper table structure, show raw data
                                            html.Div([
                                                html.Strong("Result: ", style={'fontSize': '0.85rem', 'color': '#198754'}),
                                                html.Span(str(data[0]) if data and len(data) > 0 else "No data", style={'fontSize': '0.85rem', 'fontFamily': 'monospace'})
                                            ], style={'padding': '0.75rem', 'backgroundColor': '#f8f9fa', 'borderRadius': '6px', 'border': '1px solid #dee2e6'})
                                        )
                                    )(cols if cols else (list(data[0].keys()) if data and len(data) > 0 and isinstance(data[0], dict) and data[0] else []))
                                )()
                            ])
                        )(item.get('data', []), item.get('columns', []))
                    ], style={'marginBottom': '1rem', 'padding': '0.75rem', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px', 'border': '1px solid #dee2e6'})
                )
            
            elif item['type'] == 'query':
                query_text = item.get('query', 'No query available')
                description = item.get('description', 'Generated Query')
                components.append(
                    html.Div([
                        html.Small(description, style={'color': '#6c757d', 'display': 'block', 'marginBottom': '0.25rem'}),
                        html.Pre(
                            query_text,
                            style={
                                'backgroundColor': '#2d2d2d',
                                'color': '#f8f8f2',
                                'padding': '0.75rem',
                                'borderRadius': '6px',
                                'fontSize': '0.8rem',
                                'overflowX': 'auto',
                                'marginBottom': '0',
                                'fontFamily': 'Monaco, Consolas, monospace'
                            }
                        )
                    ], style={'marginBottom': '1rem'})
                )
        
        return html.Div([
            html.Div([
                html.Div([
                    html.I(className="bi bi-robot", style={'fontSize': '1.5rem', 'marginRight': '0.75rem', 'color': '#198754'}),
                    html.Div([
                        html.Strong("Genie", style={'fontSize': '0.85rem', 'color': '#6c757d', 'display': 'block', 'marginBottom': '0.5rem'}),
                        html.Div(components)
                    ], style={'flex': '1'})
                ], style={'display': 'flex', 'alignItems': 'start'})
            ], style={
                'backgroundColor': '#d1e7dd',
                'padding': '1rem',
                'borderRadius': '12px',
                'marginBottom': '0.75rem',
                'border': '1px solid #a3cfbb'
            })
        ], style={'marginBottom': '1rem'})


# Clear conversation (HQ) - triggered by button click
@app.callback(
    [Output('hq-genie-conversation-history', 'data'),
     Output('hq-genie-input', 'value'),
     Output('hq-genie-results-container', 'children', allow_duplicate=True)],
    [Input('btn-clear-genie-hq', 'n_clicks')],
    prevent_initial_call=True
)
def clear_genie_conversation_hq(n_clicks):
    print("🔄 Clearing HQ Genie conversation and starting fresh")
    genie_service.reset_conversation()
    # Clear everything: history, input, and results display
    return [], "", html.Div(style={'display': 'none'})


# Display conversation history (HQ)
@app.callback(
    Output('hq-genie-conversation-display', 'children'),
    [Input('hq-genie-conversation-history', 'data'),
     Input('selected-property-id', 'data')],
    [State('current-persona', 'data')],
    prevent_initial_call=False
)
def display_conversation_hq(history, hq_property, persona):
    # Set auth context for suggested questions (always update when property changes)
    role = 'hq'
    property_val = hq_property if hq_property else None
    try:
        genie_service.set_auth_context(role=role, property=property_val)
    except Exception as e:
        print(f"⚠️ Failed to set Genie auth context: {str(e)}")
    
    if not history:
        
        # Show suggested questions when empty
        try:
            suggested = genie_service.get_suggested_questions()
        except:
            suggested = [
                "How many issues are there?",
                "What are the top 5 aspects with the most issues?",
                "Show me issues by location"
            ]
        
        return html.Div([
            html.Div([
                html.I(className="bi bi-chat-text", style={
                    'fontSize': '3rem', 
                    'color': '#198754', 
                    'display': 'block', 
                    'textAlign': 'center', 
                    'marginBottom': '0.75rem'
                }),
                html.H5("Start a conversation with Genie", style={
                    'textAlign': 'center', 
                    'color': '#495057', 
                    'fontSize': '1.1rem',
                    'fontWeight': '500',
                    'margin': '0 0 1.5rem 0'
                }),
            ], style={'marginBottom': '2rem'}),
            
            html.Div([
                html.Div("💡 Try asking:", style={
                    'fontSize': '0.9rem', 
                    'fontWeight': '600', 
                    'color': '#495057', 
                    'marginBottom': '1rem', 
                    'textAlign': 'center'
                }),
                html.Div([
                    dbc.Button(
                        [html.I(className="bi bi-chat-square-text me-2"), q],
                        id={'type': 'hq-suggested-question', 'index': i},
                        color="primary",
                        size="sm",
                        outline=True,
                        className="me-2 mb-2",
                        style={
                            'borderRadius': '8px',
                            'fontSize': '0.9rem',
                            'padding': '0.6rem 1rem',
                            'borderWidth': '2px',
                            'fontWeight': '500',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
                            'transition': 'all 0.2s'
                        }
                    ) for i, q in enumerate(suggested)
                ], style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'center',
                    'gap': '0.5rem'
                })
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '1.5rem',
                'borderRadius': '12px',
                'border': '1px solid #e9ecef'
            })
        ], style={'padding': '1rem 0'})
    
    messages = []
    for idx, msg in enumerate(history):
        if msg.get('type') == 'user':
            messages.append(render_genie_message(msg, is_user=True))
        else:
            messages.append(render_genie_message(msg, is_user=False))
            # Add follow-up questions after Genie responses
            if msg.get('follow_up_questions'):
                messages.append(
                    html.Div([
                        html.Div("💬 Follow-up:", style={
                            'fontSize': '0.85rem',
                            'fontWeight': '600',
                            'color': '#198754',
                            'marginBottom': '0.75rem'
                        }),
                        html.Div([
                            dbc.Button(
                                [html.I(className="bi bi-arrow-return-right me-2"), q],
                                id={'type': 'hq-followup-question', 'index': f"{idx}-{i}"},
                                color="success",
                                size="sm",
                                outline=True,
                                className="me-2 mb-2",
                                style={
                                    'borderRadius': '8px',
                                    'fontSize': '0.85rem',
                                    'padding': '0.5rem 0.9rem',
                                    'borderWidth': '2px',
                                    'fontWeight': '500',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                                }
                            ) for i, q in enumerate(msg['follow_up_questions'])
                        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '0.5rem'})
                    ], style={
                        'marginBottom': '1.5rem',
                        'paddingLeft': '2.5rem',
                        'paddingRight': '1rem'
                    })
                )
    
    return html.Div(messages)


# Handle suggested/follow-up question clicks (HQ)
@app.callback(
    Output('hq-genie-input', 'value', allow_duplicate=True),
    [Input({'type': 'hq-suggested-question', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'hq-followup-question', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'hq-suggested-question', 'index': dash.dependencies.ALL}, 'children'),
     State({'type': 'hq-followup-question', 'index': dash.dependencies.ALL}, 'children')],
    prevent_initial_call=True
)
def populate_question_hq(suggested_clicks, followup_clicks, suggested_texts, followup_texts):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Helper function to extract text from button children
    def extract_text(children):
        if isinstance(children, str):
            return children
        elif isinstance(children, list):
            # Button children is [Icon, Text], get the text (last element)
            return children[-1] if children else ""
        return str(children)
    
    # Find which button was clicked
    triggered_id = ctx.triggered[0]['prop_id']
    
    if 'hq-suggested-question' in triggered_id:
        # Find index of clicked suggested question
        for i, clicks in enumerate(suggested_clicks):
            if clicks and clicks > 0:
                return extract_text(suggested_texts[i])
    elif 'hq-followup-question' in triggered_id:
        # Find index of clicked follow-up question
        for i, clicks in enumerate(followup_clicks):
            if clicks and clicks > 0:
                return extract_text(followup_texts[i])
    
    return dash.no_update


# Genie query handler (HQ) - Now with conversation history
@app.callback(
    [Output('hq-genie-conversation-history', 'data', allow_duplicate=True),
     Output('hq-genie-results-container', 'children'),
     Output('hq-genie-input', 'value', allow_duplicate=True)],
    [Input('btn-ask-genie-hq', 'n_clicks')],
    [State('hq-genie-input', 'value'),
     State('hq-genie-conversation-history', 'data'),
     State('current-persona', 'data'),
     State('selected-property-id', 'data')],
    prevent_initial_call=True
)
def ask_genie_hq(n_clicks, query, history, persona, hq_property):
    if not n_clicks or not query:
        return dash.no_update, html.Div(), dash.no_update
    
    # Set Genie auth context
    role = 'hq'
    property_val = hq_property if hq_property else None
    genie_service.set_auth_context(role=role, property=property_val)
    
    try:
        result = genie_service.continue_conversation(query)
        
        if 'error' in result:
            # Still show error in history
            new_history = history + [
                {'type': 'user', 'query': query},
                {'type': 'genie', 'error': result['error'], 'results': []}
            ]
            return new_history, html.Div(), ""
        
        if not result.get('results'):
            new_history = history + [
                {'type': 'user', 'query': query},
                {'type': 'genie', 'results': [{'type': 'text', 'content': 'No results found.'}]}
            ]
            return new_history, html.Div(), ""
        
        # Append user query and Genie response to history
        new_history = history + [
            {'type': 'user', 'query': query},
            {'type': 'genie', **result}
        ]
        
        # Clear input and return updated history
        return new_history, html.Div(), ""
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_history = history + [
            {'type': 'user', 'query': query},
            {'type': 'genie', 'error': str(e), 'results': []}
        ]
        return error_history, html.Div(), ""

# Clear conversation (PM) - triggered by button click
@app.callback(
    [Output('pm-genie-conversation-history', 'data'),
     Output('pm-genie-input', 'value'),
     Output('pm-genie-results', 'children', allow_duplicate=True)],
    [Input('btn-clear-genie-pm', 'n_clicks')],
    prevent_initial_call=True
)
def clear_genie_conversation_pm(n_clicks):
    print("🔄 Clearing PM Genie conversation and starting fresh")
    genie_service.reset_conversation()
    # Clear everything: history, input, and results display
    return [], "", html.Div(style={'display': 'none'})


# Clear both conversations when switching roles/personas
@app.callback(
    [Output('hq-genie-conversation-history', 'data', allow_duplicate=True),
     Output('pm-genie-conversation-history', 'data', allow_duplicate=True),
     Output('hq-genie-input', 'value', allow_duplicate=True),
     Output('pm-genie-input', 'value', allow_duplicate=True)],
    [Input('btn-switch-hq', 'n_clicks'),
     Input('btn-switch-pm', 'n_clicks'),
     Input('btn-back-to-roles', 'n_clicks')],
    prevent_initial_call=True
)
def clear_genie_on_role_switch(switch_hq, switch_pm, back_roles):
    """Clear Genie conversation history when user switches roles"""
    ctx = callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update, dash.no_update, dash.no_update
    
    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    print(f"🔄 Clearing Genie conversations due to role switch: {button_id}")
    
    # Reset the genie service conversation
    genie_service.reset_conversation()
    
    # Clear both HQ and PM conversation histories and inputs
    return [], [], "", ""


# Display conversation history (PM)
@app.callback(
    Output('pm-genie-conversation-display', 'children'),
    [Input('pm-genie-conversation-history', 'data'),
     Input('pm-selected-property-store', 'data')],
    [State('current-persona', 'data')],
    prevent_initial_call=False
)
def display_conversation_pm(history, pm_property, persona):
    # Set auth context for suggested questions (always update when property changes)
    role = 'pm'
    property_val = pm_property if pm_property else None
    try:
        genie_service.set_auth_context(role=role, property=property_val)
    except Exception as e:
        print(f"⚠️ Failed to set Genie auth context: {str(e)}")
    
    if not history:
        
        # Show suggested questions when empty
        try:
            suggested = genie_service.get_suggested_questions()
        except:
            suggested = [
                "How many issues are there?",
                "What are the top 5 aspects with the most issues?",
                "Show me issues by location"
            ]
        
        return html.Div([
            html.Div([
                html.I(className="bi bi-chat-text", style={
                    'fontSize': '3rem', 
                    'color': '#198754', 
                    'display': 'block', 
                    'textAlign': 'center', 
                    'marginBottom': '0.75rem'
                }),
                html.H5("Start a conversation with Genie", style={
                    'textAlign': 'center', 
                    'color': '#495057', 
                    'fontSize': '1.1rem',
                    'fontWeight': '500',
                    'margin': '0 0 1.5rem 0'
                }),
            ], style={'marginBottom': '2rem'}),
            
            html.Div([
                html.Div("💡 Try asking:", style={
                    'fontSize': '0.9rem', 
                    'fontWeight': '600', 
                    'color': '#495057', 
                    'marginBottom': '1rem', 
                    'textAlign': 'center'
                }),
                html.Div([
                    dbc.Button(
                        [html.I(className="bi bi-chat-square-text me-2"), q],
                        id={'type': 'pm-suggested-question', 'index': i},
                        color="primary",
                        size="sm",
                        outline=True,
                        className="me-2 mb-2",
                        style={
                            'borderRadius': '8px',
                            'fontSize': '0.9rem',
                            'padding': '0.6rem 1rem',
                            'borderWidth': '2px',
                            'fontWeight': '500',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.05)',
                            'transition': 'all 0.2s'
                        }
                    ) for i, q in enumerate(suggested)
                ], style={
                    'display': 'flex',
                    'flexWrap': 'wrap',
                    'justifyContent': 'center',
                    'gap': '0.5rem'
                })
            ], style={
                'backgroundColor': '#f8f9fa',
                'padding': '1.5rem',
                'borderRadius': '12px',
                'border': '1px solid #e9ecef'
            })
        ], style={'padding': '1rem 0'})
    
    messages = []
    for idx, msg in enumerate(history):
        if msg.get('type') == 'user':
            messages.append(render_genie_message(msg, is_user=True))
        else:
            messages.append(render_genie_message(msg, is_user=False))
            # Add follow-up questions after Genie responses
            if msg.get('follow_up_questions'):
                messages.append(
                    html.Div([
                        html.Div("💬 Follow-up:", style={
                            'fontSize': '0.85rem',
                            'fontWeight': '600',
                            'color': '#198754',
                            'marginBottom': '0.75rem'
                        }),
                        html.Div([
                            dbc.Button(
                                [html.I(className="bi bi-arrow-return-right me-2"), q],
                                id={'type': 'pm-followup-question', 'index': f"{idx}-{i}"},
                                color="success",
                                size="sm",
                                outline=True,
                                className="me-2 mb-2",
                                style={
                                    'borderRadius': '8px',
                                    'fontSize': '0.85rem',
                                    'padding': '0.5rem 0.9rem',
                                    'borderWidth': '2px',
                                    'fontWeight': '500',
                                    'boxShadow': '0 2px 4px rgba(0,0,0,0.05)'
                                }
                            ) for i, q in enumerate(msg['follow_up_questions'])
                        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '0.5rem'})
                    ], style={
                        'marginBottom': '1.5rem',
                        'paddingLeft': '2.5rem',
                        'paddingRight': '1rem'
                    })
                )
    
    return html.Div(messages)


# Handle suggested/follow-up question clicks (PM)
@app.callback(
    Output('pm-genie-input', 'value', allow_duplicate=True),
    [Input({'type': 'pm-suggested-question', 'index': dash.dependencies.ALL}, 'n_clicks'),
     Input({'type': 'pm-followup-question', 'index': dash.dependencies.ALL}, 'n_clicks')],
    [State({'type': 'pm-suggested-question', 'index': dash.dependencies.ALL}, 'children'),
     State({'type': 'pm-followup-question', 'index': dash.dependencies.ALL}, 'children')],
    prevent_initial_call=True
)
def populate_question_pm(suggested_clicks, followup_clicks, suggested_texts, followup_texts):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    # Helper function to extract text from button children
    def extract_text(children):
        if isinstance(children, str):
            return children
        elif isinstance(children, list):
            # Button children is [Icon, Text], get the text (last element)
            return children[-1] if children else ""
        return str(children)
    
    # Find which button was clicked
    triggered_id = ctx.triggered[0]['prop_id']
    
    if 'pm-suggested-question' in triggered_id:
        # Find index of clicked suggested question
        for i, clicks in enumerate(suggested_clicks):
            if clicks and clicks > 0:
                return extract_text(suggested_texts[i])
    elif 'pm-followup-question' in triggered_id:
        # Find index of clicked follow-up question
        for i, clicks in enumerate(followup_clicks):
            if clicks and clicks > 0:
                return extract_text(followup_texts[i])
    
    return dash.no_update


# Genie query handler (PM) - Now with conversation history
@app.callback(
    [Output('pm-genie-conversation-history', 'data', allow_duplicate=True),
     Output('pm-genie-results', 'children'),
     Output('pm-genie-input', 'value', allow_duplicate=True)],
    [Input('btn-ask-genie-pm', 'n_clicks')],
    [State('pm-genie-input', 'value'),
     State('pm-genie-conversation-history', 'data'),
     State('current-persona', 'data'),
     State('pm-selected-property-store', 'data')],
    prevent_initial_call=True
)
def ask_genie_pm(n_clicks, query, history, persona, pm_property):
    if not n_clicks or not query:
        return dash.no_update, html.Div(), dash.no_update
    
    # Set Genie auth context for PM
    role = 'pm'
    property_val = pm_property if pm_property else None
    genie_service.set_auth_context(role=role, property=property_val)
    
    try:
        result = genie_service.continue_conversation(query)
        
        if 'error' in result:
            # Still show error in history
            new_history = history + [
                {'type': 'user', 'query': query},
                {'type': 'genie', 'error': result['error'], 'results': []}
            ]
            return new_history, html.Div(), ""
        
        if not result.get('results'):
            new_history = history + [
                {'type': 'user', 'query': query},
                {'type': 'genie', 'results': [{'type': 'text', 'content': 'No results found.'}]}
            ]
            return new_history, html.Div(), ""
        
        # Append user query and Genie response to history
        new_history = history + [
            {'type': 'user', 'query': query},
            {'type': 'genie', **result}
        ]
        
        # Clear input and return updated history
        return new_history, html.Div(), ""
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        error_history = history + [
            {'type': 'user', 'query': query},
            {'type': 'genie', 'error': str(e), 'results': []}
        ]
        return error_history, html.Div(), ""

# Handle PM property button clicks and default selection
@app.callback(
    [Output('pm-selected-property-store', 'data'),
     Output({'type': 'pm-property-btn', 'location': 'Austin, TX'}, 'outline'),
     Output({'type': 'pm-property-btn', 'location': 'Boston, MA'}, 'outline')],
    [Input({'type': 'pm-property-btn', 'location': dash.dependencies.ALL}, 'n_clicks'),
     Input('current-screen', 'data')],
    prevent_initial_call=False
)
def handle_pm_property_selection(n_clicks_list, screen):
    if screen != 'pm-dashboard':
        return dash.no_update, dash.no_update, dash.no_update
    
    ctx = dash.callback_context
    
    # Check what triggered the callback
    if not ctx.triggered:
        # Initial load - default to Austin
        print("📍 PM Dashboard: Initial load - Defaulting to Austin, TX")
        return 'austin-tx', False, True  # Austin selected (outline=False means filled)
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # If triggered by screen change (entering PM view), default to Austin
    if triggered_id == 'current-screen':
        print("📍 PM Dashboard: Entering PM view - Defaulting to Austin, TX")
        return 'austin-tx', False, True  # Austin selected
    
    # If triggered by button click
    if 'pm-property-btn' in triggered_id:
        # Extract location from triggered button
        if 'Austin' in triggered_id:
            print("📍 PM Dashboard: Austin, TX selected by user")
            return 'austin-tx', False, True  # Austin selected
        elif 'Boston' in triggered_id:
            print("📍 PM Dashboard: Boston, MA selected by user")
            return 'boston-ma', True, False  # Boston selected
    
    # Fallback to Austin
    print("📍 PM Dashboard: Fallback to Austin, TX")
    return 'austin-tx', False, True

# Load PM property details (header card)
@app.callback(
    Output('pm-selected-property-details-container', 'children'),
    Input('pm-selected-property-store', 'data'),
    prevent_initial_call=False
)
def load_pm_property_details(property_id):
    if not property_id:
        return html.Div()
    
    try:
        details = property_service.get_property_details(property_id)
        if not details:
            return dbc.Alert("No Reviews Found For Property.", color="warning")
        
        return dbc.Card([
            dbc.CardBody([
                # Property Header with location badge
                dbc.Row([
                    dbc.Col([
                        html.H2(details['name'], className="mb-2", style={'fontWeight': '700', 'fontSize': '2rem'}),
                        html.Div([
                            html.I(className="bi bi-geo-alt-fill me-2", style={'color': '#17a2b8'}),
                            html.Span(f"{details['city']}, {details['state']}", 
                                     style={'fontSize': '1.1rem', 'fontWeight': '500', 'color': '#495057'}),
                        ], className="mb-2"),
                        html.P([
                            html.Span(f"{details['reviews_count']} reviews", className="me-3"),
                            html.Span(f"Rating: {details['avg_rating']}/5.0", className="me-3"),
                        ], className="text-muted", style={'fontSize': '0.95rem'}),
                        # Service Principal indicator
                        html.Div([
                            html.I(className="bi bi-shield-lock-fill me-2", style={'color': '#28a745', 'fontSize': '0.85rem'}),
                            html.Span(
                                f"Using Service Principal for {details['city']}, {details['state']}", 
                                style={'fontSize': '0.85rem', 'color': '#6c757d', 'fontStyle': 'italic'}
                            ),
                        ], className="mt-2"),
                    ], md=8),
                    dbc.Col([
                        dbc.Badge(
                            f"📍 {details['city']}, {details['state']}", 
                            color="info",
                            className="p-3",
                            style={'fontSize': '1rem', 'fontWeight': '500'}
                        ),
                    ], md=4, className="text-end d-flex align-items-center justify-content-end"),
                ], className="mb-2"),
            ], style={'padding': '2rem'})
        ], style={'border': 'none', 'borderRadius': '12px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'})
    except Exception as e:
        return dbc.Alert(f"Error loading property details: {str(e)}", color="danger")

# Load filtered dashboard iframe for PM
@app.callback(
    Output('pm-filtered-dashboard-iframe', 'children'),
    Input('pm-selected-property-store', 'data'),
    prevent_initial_call=False
)
def load_pm_filtered_dashboard(property_id):
    if not property_id:
        return html.Div()
    
    try:
        # Get property details to extract location
        details = property_service.get_property_details(property_id)
        if not details:
            return dbc.Alert("No Reviews Found For Property", color="warning")
        
        # Construct full location string (city, state)
        location = f"{details['city']}, {details['state']}"
        
        # URL encode the location string (double encoding needed for Databricks filters)
        from urllib.parse import quote
        encoded_location = quote(quote(location, safe=''), safe='')
        
        # Base dashboard URL for embedding
        base_url = os.getenv('DATABRICKS_PROPERTY_DASHBOARD_URL', "https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/embed/dashboardsv3/01f0ab936a8815ffbc5b0dd3d8ca0f9f")
        filtered_url = f"{base_url}&f_property_rating%7E57a7e64b={encoded_location}"
        
        print(f"🗺️ Loading PM dashboard filtered for location: {location}")
        print(f"📊 Dashboard URL: {filtered_url}")
        
        return html.Iframe(
            src=filtered_url,
            style={
                'width': '100%',
                'height': '800px',
                'border': 'none',
                'borderRadius': '8px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)'
            }
        )
    except Exception as e:
        print(f"❌ Error loading PM dashboard: {str(e)}")
        return dbc.Alert(f"Error loading dashboard: {str(e)}", color="danger")

# Load aspect analysis table for PM (Tab 2)
@app.callback(
    Output('pm-aspect-analysis-table', 'children'),
    Input('pm-selected-property-store', 'data'),
    prevent_initial_call=False
)
def load_pm_aspect_analysis_table(property_id):
    if not property_id:
        return html.Div()
    
    try:
        details = property_service.get_property_details(property_id)
        if not details or 'aspects' not in details:
            return html.Div()
        
        # Create aspects data
        aspects_data = []
        for aspect in details['aspects']:
            aspects_data.append({
                'Aspect': aspect['name'],
                'Negative Reviews': f"{round(aspect['percentage']*100, 1)}%",
                'Status': aspect['status'].upper()
            })
        
        if not aspects_data:
            return html.Div()
        
        # Create HTML table rows
        table_rows = []
        for aspect_item in aspects_data:
            status = aspect_item['Status']
            if 'CRITICAL' in status:
                row_style = {'backgroundColor': '#ffebee', 'color': custom_style['critical'], 'fontWeight': '500'}
            elif 'WARNING' in status:
                row_style = {'backgroundColor': '#fff9c4', 'color': custom_style['warning'], 'fontWeight': '500'}
            else:
                row_style = {}
            
            table_rows.append(
                html.Tr([
                    html.Td(aspect_item['Aspect'], style={'padding': '12px'}),
                    html.Td(aspect_item['Negative Reviews'], style={'padding': '12px', 'textAlign': 'center'}),
                    html.Td(dbc.Badge(status, color='danger' if 'CRITICAL' in status else 'warning' if 'WARNING' in status else 'success'), 
                           style={'padding': '12px', 'textAlign': 'center'}),
                ], style=row_style)
            )
        
        return dbc.Card([
            dbc.CardBody([
                html.Div([
                    html.H4("📋 Aspect Analysis", className="mb-0 d-inline-block", style={'fontWeight': '600'}),
                    html.I(
                        className="bi bi-info-circle ms-2",
                        id={'type': 'open-severity-modal', 'view': 'pm-aspect'},
                        style={
                            'fontSize': '1.1rem',
                            'color': '#0d6efd',
                            'cursor': 'pointer',
                            'verticalAlign': 'middle'
                        },
                        title="Click to view severity threshold logic",
                        n_clicks=0
                    ),
                ], className="mb-3", style={'display': 'flex', 'alignItems': 'center'}),
                html.P([
                    "Overview of all aspects and their performance for your property. ",
                    html.Strong("Negative Reviews %"), 
                    " shows the overall negative sentiment rate for this aspect."
                ], 
                      className="text-muted mb-3",
                      style={'fontSize': '0.95rem'}),
                dbc.Table([
                    html.Thead(
                        html.Tr([
                            html.Th("Aspect", style={'padding': '12px', 'fontSize': '1rem'}),
                            html.Th("Negative Reviews", style={'padding': '12px', 'fontSize': '1rem', 'textAlign': 'center'}),
                            html.Th("Status", style={'padding': '12px', 'fontSize': '1rem', 'textAlign': 'center'}),
                        ]),
                        style={'backgroundColor': custom_style['primary'], 'color': 'white', 'fontWeight': 'bold'}
                    ),
                    html.Tbody(table_rows)
                ], bordered=True, hover=True, responsive=True, striped=True,
                   style={'fontSize': '0.95rem'})
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
    except Exception as e:
        print(f"Error loading PM aspect analysis table: {str(e)}")
        return html.Div()

# Load aspect options for PM Reviews Deep Dive
@app.callback(
    Output('pm-aspect-selector', 'options'),
    Input('pm-selected-property-store', 'data')
)
def load_pm_aspect_options(property_id):
    if not property_id:
        return dash.no_update
    
    try:
        deep_dive_data = property_service.get_reviews_deep_dive(property_id)
        aspects = deep_dive_data.get('aspects', [])
        return [{'label': aspect, 'value': aspect} for aspect in aspects]
    except Exception as e:
        print(f"⚠️  Error loading PM aspects: {str(e)}")
        return dash.no_update

# Load PM Reviews Deep Dive content
@app.callback(
    Output('pm-reviews-deep-dive-content', 'children'),
    [Input('pm-aspect-selector', 'value'),
     Input('pm-selected-property-store', 'data')]
)
def load_pm_reviews_deep_dive(selected_aspect, property_id):
    if not property_id or not selected_aspect:
        return html.Div()
    
    try:
        # Get property details to fetch correct status (consistent with table)
        details = property_service.get_property_details(property_id)
        
        # Get deep dive data
        deep_dive_data = property_service.get_reviews_deep_dive(property_id, selected_aspect)
        deep_dive = deep_dive_data.get('deep_dive')
        
        if not deep_dive:
            return dbc.Alert("No data available for this aspect.", color="info")
        
        # Find the correct status from property details for this aspect (same as table)
        correct_status = None
        if details and 'aspects' in details:
            for aspect_info in details['aspects']:
                if aspect_info['name'] == selected_aspect:
                    correct_status = aspect_info['status']
                    break
        
        # Use correct_status from table instead of deep_dive['severity']
        severity = correct_status if correct_status else deep_dive['severity']
        severity_color = 'danger' if severity.lower() == 'critical' else ('warning' if severity.lower() == 'warning' else 'success')
        
        return dbc.Card([
            dbc.CardBody([
                # Header with metrics
                dbc.Row([
                    dbc.Col([
                        html.H5(deep_dive['aspect'], className="mb-2", style={'fontWeight': '600'}),
                        dbc.Badge(
                            severity, 
                            color=severity_color, 
                            className="me-2",
                            style={'fontSize': '0.875rem'}
                        ),
                        html.Br(),
                        html.Small(f"Issue opened: {deep_dive['date_opened']}", className="text-muted d-block"),
                        html.Small([
                            html.Strong("Reason: ", style={'color': '#495057'}),
                            html.Span(deep_dive.get('open_reason', 'Not specified'), style={'color': '#6c757d'})
                        ], className="text-muted d-block mt-1"),
                    ], md=8),
                    dbc.Col([
                        html.Div([
                            html.Div([
                                html.H3(f"{deep_dive['volume_percentage']}%", 
                                       className="mb-0",
                                       style={'fontWeight': '700', 'color': '#dc3545'}),
                                html.Small("Volume", className="text-muted"),
                            ], className="text-center mb-3"),
                            html.Div([
                                html.H4(f"{deep_dive['total_reviews']}", 
                                       className="mb-0",
                                       style={'fontWeight': '600'}),
                                html.Small("Total Reviews", className="text-muted d-block"),
                                html.Small("7-day window", className="text-muted d-block", style={'fontSize': '0.7rem'}),
                            ], className="text-center"),
                        ])
                    ], md=4, className="text-center"),
                ], className="mb-4"),
                
                html.Hr(),
                
                # Issue Summary
                html.Div([
                    html.H6("📝 Issue Summary", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['issue_summary'], className="mb-4", style={'lineHeight': '1.6'}),
                ]),
                
                # Review Counts
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H3(deep_dive['negative_count'], 
                                           className="mb-1",
                                           style={'fontWeight': '700', 'color': '#dc3545'}),
                                    html.P("Negative Reviews", className="mb-0 text-muted", style={'fontSize': '0.9rem'}),
                                ], className="text-center")
                            ], style={'padding': '1rem'})
                        ], style={'border': '2px solid #dc3545', 'borderRadius': '8px', 'backgroundColor': '#fff5f5'}),
                    ], md=6),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.Div([
                                    html.H3(deep_dive['positive_count'], 
                                           className="mb-1",
                                           style={'fontWeight': '700', 'color': '#28a745'}),
                                    html.P("Positive Reviews", className="mb-0 text-muted", style={'fontSize': '0.9rem'}),
                                ], className="text-center")
                            ], style={'padding': '1rem'})
                        ], style={'border': '2px solid #28a745', 'borderRadius': '8px', 'backgroundColor': '#f1f9f3'}),
                    ], md=6),
                ], className="mb-4"),
                
                # Root Cause Analysis
                html.Div([
                    html.H6("🔍 Potential Root Cause", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['potential_root_cause'], 
                          className="mb-4",
                          style={'lineHeight': '1.6', 'backgroundColor': '#f8f9fa', 'padding': '1rem', 'borderRadius': '8px'}),
                ]),
                
                # Impact
                html.Div([
                    html.H6("📊 Impact", className="mb-2", style={'fontWeight': '600'}),
                    html.P(deep_dive['impact'], 
                          className="mb-4",
                          style={'lineHeight': '1.6', 'backgroundColor': '#fff3cd', 'padding': '1rem', 'borderRadius': '8px'}),
                ]),
                
                # Recommended Action
                html.Div([
                    html.H6("✅ Recommended Action", className="mb-2", style={'fontWeight': '600'}),
                    dbc.Alert(
                        deep_dive['recommended_action'],
                        color="success",
                        className="mb-0",
                        style={'lineHeight': '1.6', 'fontWeight': '500'}
                    ),
                ]),
                
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
        
    except Exception as e:
        return dbc.Alert(f"Error loading deep dive: {str(e)}", color="danger")

# Load Individual Reviews Browser Controls for PM (separate from deep dive content)
@app.callback(
    Output('pm-review-browser-controls', 'children'),
    [Input('pm-aspect-selector', 'value'),
     Input('pm-selected-property-store', 'data')],
    prevent_initial_call=False
)
def load_pm_review_browser_controls(selected_aspect, property_id):
    """Render the review browser controls (timeframe dropdown and filter buttons) for PM"""
    if not property_id or not selected_aspect:
        return html.Div()
    
    return dbc.Card([
        dbc.CardBody([
            html.H6("📝 Individual Reviews", className="mb-3", style={'fontWeight': '600'}),
            dbc.Row([
                dbc.Col([
                    html.Label("Timeframe:", style={'fontWeight': '500', 'marginBottom': '0.5rem'}),
                    dcc.Dropdown(
                        id='pm-review-timeframe-selector',
                        options=[
                            {'label': 'Last 7 days', 'value': 7},
                            {'label': 'Last 14 days', 'value': 14},
                            {'label': 'Last 30 days', 'value': 30}
                        ],
                        value=30,  # Default to 30 days for PM
                        clearable=False,
                        style={'width': '100%'},
                        optionHeight=35
                    ),
                ], md=3),
                dbc.Col([
                    html.Label("Show Reviews:", style={'fontWeight': '500', 'marginBottom': '0.5rem'}),
                    dbc.RadioItems(
                        id='pm-review-filter',
                        options=[
                            {'label': 'All Reviews', 'value': 'all'},
                            {'label': 'Negative Only', 'value': 'negative'},
                            {'label': 'Positive Only', 'value': 'positive'}
                        ],
                        value='all',  # Default to show all
                        inline=True,
                        style={'marginTop': '0.25rem'}
                    ),
                ], md=6),
            ], className="mb-3"),
        ], style={'padding': '1.5rem'})
    ], style={'border': 'none', 'borderRadius': '12px', 'backgroundColor': '#f8f9fa'})

# Generate email
@app.callback(
    [Output('email-draft', 'children'),
     Output('email-data', 'data')],
    Input('current-screen', 'data'),
    State('selected-property-id', 'data')
)
def generate_email(screen, property_id):
    if screen != 'hq-email' or not property_id:
        return html.Div(), None
    
    try:
        property_data = property_service.get_property_details(property_id)
        if not property_data:
            return dbc.Alert("No Reviews Found For Property.", color="warning"), None
        
        email_result = email_service.generate_property_email(property_data)
        
        if 'error' in email_result:
            return dbc.Alert(f"Error: {email_result['error']}", color="danger"), None
        
        return [
            dbc.Card([
                dbc.CardBody([
                    html.H4(f"To: {email_result['property_name']} Property Manager", className="mb-3"),
                    html.Hr(),
                    html.Pre(email_result['email_content'], style={'whiteSpace': 'pre-wrap', 'fontFamily': 'inherit'})
                ])
            ])
        ], email_result
    except Exception as e:
        return dbc.Alert(f"Error generating email: {str(e)}", color="danger"), None

# Generate email for HQ Dashboard Tab 3
@app.callback(
    Output('hq-email-draft', 'children'),
    Input('hq-generate-email-btn', 'n_clicks'),
    State('selected-property-id', 'data'),
    prevent_initial_call=True
)
def generate_hq_email_tab(n_clicks, property_id):
    if not n_clicks or not property_id:
        return html.Div()
    
    try:
        property_data = property_service.get_property_details(property_id)
        if not property_data:
            return dbc.Alert("No Reviews Found For Property.", color="warning")
        
        email_result = email_service.generate_property_email(property_data)
        
        if 'error' in email_result:
            return dbc.Alert(f"Error: {email_result['error']}", color="danger")
        
        return dbc.Card([
            dbc.CardBody([
                html.H5(f"To: {email_result['property_name']} Property Manager", className="mb-3", style={'fontWeight': '600'}),
                html.Hr(),
                html.Pre(email_result['email_content'], 
                        style={'whiteSpace': 'pre-wrap', 
                               'fontFamily': 'inherit',
                               'backgroundColor': '#f8f9fa',
                               'padding': '1rem',
                               'borderRadius': '8px',
                               'border': '1px solid #dee2e6'}),
                html.Hr(className="my-4"),
                dbc.Button("Copy to Clipboard", 
                          id='btn-copy-email',
                          color="secondary",
                          className="me-2",
                          style={'borderRadius': '8px'}),
                dbc.Button("Send Email", 
                          id='btn-send-hq-email',
                          color="primary",
                          style={'borderRadius': '8px'}),
            ])
        ], style={'marginTop': '1rem'})
    except Exception as e:
        return dbc.Alert(f"Error generating email: {str(e)}", color="danger")

# Send email from HQ Dashboard Tab 3
@app.callback(
    Output('hq-email-draft', 'children', allow_duplicate=True),
    Input('btn-send-hq-email', 'n_clicks'),
    prevent_initial_call=True
)
def send_hq_email_tab(n_clicks):
    if not n_clicks:
        return dash.no_update
    
    return dbc.Alert("✅ Email sent successfully!", color="success", className="mt-3")

# Send email (legacy from old hq-email screen)
@app.callback(
    Output('email-draft', 'children', allow_duplicate=True),
    Input('btn-send-email', 'n_clicks'),
    State('email-data', 'data'),
    prevent_initial_call=True
)
def send_email(n_clicks, email_data):
    if not n_clicks or not email_data:
        return dash.no_update
    
    return dbc.Alert("✅ Email sent successfully!", color="success", className="mt-3")

# Callback to load individual reviews for HQ
@app.callback(
    Output('hq-individual-reviews-list', 'children'),
    [Input('hq-review-timeframe-selector', 'value'),
     Input('hq-review-filter', 'value')],
    [State('hq-aspect-selector', 'value'),
     State('selected-property-id', 'data')],
    prevent_initial_call=True  # Components are dynamically created
)
def load_hq_individual_reviews(days_back, review_filter, selected_aspect, property_id):
    # Check for None or empty values explicitly
    if property_id is None or selected_aspect is None or days_back is None:
        return html.Div()
    if property_id == '' or selected_aspect == '' or days_back == '':
        return html.Div()
    
    try:
        reviews_data = property_service.get_reviews_for_aspect(property_id, selected_aspect, days_back)
        
        # Handle new dictionary format with positive and negative reviews
        if not reviews_data or (not reviews_data.get('positive') and not reviews_data.get('negative')):
            return dbc.Alert("No reviews found for this timeframe.", color="info", className="mt-3")
        
        negative_reviews = reviews_data.get('negative', [])
        positive_reviews = reviews_data.get('positive', [])
        
        # Apply filter
        if review_filter == 'negative':
            positive_reviews = []  # Hide positive reviews
        elif review_filter == 'positive':
            negative_reviews = []  # Hide negative reviews
        # If 'all', show both (no filtering needed)
        
        # Create a function to render review cards
        def create_review_card(review, is_negative=True):
            # Get sentiment color
            sentiment = review.get('sentiment', 'negative')
            if is_negative:
                sentiment_color = 'danger' if sentiment == 'very_negative' else 'warning'
                border_color = '#dc3545' if sentiment == 'very_negative' else '#ffc107'
            else:
                sentiment_color = 'success'
                border_color = '#28a745'
            
            # Format star rating
            star_rating = review.get('star_rating', 0)
            stars = '⭐' * int(star_rating)
            
            # Format evidence (array of strings)
            evidence = review.get('evidence', [])
            evidence_text = ' | '.join(evidence) if evidence else 'N/A'
            
            # Format opinion terms (array of strings) as colored badges
            opinion_terms = review.get('opinion_terms', [])
            opinion_badge_color = '#dc3545' if is_negative else '#28a745'  # Red for negative, green for positive
            opinion_badges = [
                dbc.Badge(term, 
                         style={
                             'backgroundColor': opinion_badge_color,
                             'color': 'white',
                             'marginRight': '0.25rem',
                             'marginBottom': '0.25rem',
                             'fontSize': '0.8rem'
                         })
                for term in opinion_terms
            ] if opinion_terms else [html.Span("N/A", className="text-muted", style={'fontSize': '0.85rem'})]
            
            return dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Strong(f"Review ID: {review.get('review_uid', 'Unknown')}", style={'fontSize': '0.9rem'}),
                                dbc.Badge(sentiment.replace('_', ' ').title(), color=sentiment_color, className="ms-2"),
                            ]),
                            html.Div([
                                html.Span(stars, style={'color': '#ffc107', 'fontSize': '1rem'}),
                                html.Span(f" ({star_rating}/5)", className="text-muted ms-2", style={'fontSize': '0.85rem'}),
                            ], className="mt-1"),
                        ], md=8),
                        dbc.Col([
                            html.Div([
                                html.Small(f"Date: {review.get('review_date', 'N/A')}", className="text-muted d-block"),
                                html.Small(f"Channel: {review.get('channel', 'N/A')}", className="text-muted d-block"),
                            ], className="text-end")
                        ], md=4),
                    ]),
                    html.Hr(className="my-2"),
                    html.P(review.get('review_text', 'No review text available.'), 
                           style={'fontSize': '0.95rem', 'lineHeight': '1.6', 'marginTop': '1rem'}),
                    html.Hr(className="my-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Strong("Evidence:", className="text-muted", style={'fontSize': '0.85rem'}),
                            html.P(evidence_text, style={'fontSize': '0.85rem', 'marginTop': '0.25rem', 'fontStyle': 'italic'}),
                        ], md=6),
                        dbc.Col([
                            html.Strong("Opinion Terms:", className="text-muted", style={'fontSize': '0.85rem'}),
                            html.Div(opinion_badges, style={'marginTop': '0.25rem'}),
                        ], md=6),
                    ]),
                ], style={'padding': '1rem'})
            ], className="mb-3", style={'border': f'1px solid {border_color}', 'borderRadius': '8px'})
        
        # Create sections for negative and positive reviews
        sections = []
        
        # Negative Reviews Section
        if negative_reviews:
            negative_cards = [create_review_card(review, is_negative=True) for review in negative_reviews]
            sections.append(
                html.Div([
                    html.Div([
                        html.H6([
                            html.I(className="bi bi-chat-left-text-fill me-2", style={'color': '#dc3545'}),
                            f"Negative Reviews ({len(negative_reviews)})"
                        ], style={'fontWeight': '600', 'color': '#dc3545', 'marginBottom': '1rem'}),
                    ]),
                    html.Div(negative_cards)
                ], className="mb-4")
            )
        
        # Positive Reviews Section
        if positive_reviews:
            positive_cards = [create_review_card(review, is_negative=False) for review in positive_reviews]
            sections.append(
                html.Div([
                    html.Div([
                        html.H6([
                            html.I(className="bi bi-check-circle-fill me-2", style={'color': '#28a745'}),
                            f"Positive Reviews ({len(positive_reviews)})"
                        ], style={'fontWeight': '600', 'color': '#28a745', 'marginBottom': '1rem'}),
                    ]),
                    html.Div(positive_cards)
                ], className="mb-4")
            )
        
        total_reviews = len(negative_reviews) + len(positive_reviews)
        return html.Div([
            html.P([
                f"Showing {total_reviews} review(s) from selected timeframe: ",
                html.Span(f"{len(negative_reviews)} negative", style={'color': '#dc3545', 'fontWeight': '600'}),
                f", {len(positive_reviews)} positive",
            ], className="text-muted mb-3", style={'fontSize': '0.9rem', 'fontWeight': '500'}),
            html.Div(sections)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error loading reviews: {str(e)}", color="danger")

# Callback to load individual reviews for PM
@app.callback(
    Output('pm-individual-reviews-list', 'children'),
    [Input('pm-review-timeframe-selector', 'value'),
     Input('pm-review-filter', 'value')],
    [State('pm-aspect-selector', 'value'),
     State('pm-selected-property-store', 'data')],
    prevent_initial_call=True  # Components are dynamically created
)
def load_pm_individual_reviews(days_back, review_filter, selected_aspect, property_id):
    # Check for None or empty values explicitly
    if property_id is None or selected_aspect is None or days_back is None:
        return html.Div()
    if property_id == '' or selected_aspect == '' or days_back == '':
        return html.Div()
    
    try:
        reviews_data = property_service.get_reviews_for_aspect(property_id, selected_aspect, days_back)
        
        # Handle new dictionary format with positive and negative reviews
        if not reviews_data or (not reviews_data.get('positive') and not reviews_data.get('negative')):
            return dbc.Alert("No reviews found for this timeframe.", color="info", className="mt-3")
        
        negative_reviews = reviews_data.get('negative', [])
        positive_reviews = reviews_data.get('positive', [])
        
        # Apply filter
        if review_filter == 'negative':
            positive_reviews = []  # Hide positive reviews
        elif review_filter == 'positive':
            negative_reviews = []  # Hide negative reviews
        # If 'all', show both (no filtering needed)
        
        # Use the same create_review_card function as HQ (can be extracted as helper in future refactor)
        def create_review_card(review, is_negative=True):
            sentiment = review.get('sentiment', 'negative')
            if is_negative:
                sentiment_color = 'danger' if sentiment == 'very_negative' else 'warning'
                border_color = '#dc3545' if sentiment == 'very_negative' else '#ffc107'
            else:
                sentiment_color = 'success'
                border_color = '#28a745'
            
            star_rating = review.get('star_rating', 0)
            stars = '⭐' * int(star_rating)
            
            evidence = review.get('evidence', [])
            evidence_text = ' | '.join(evidence) if evidence else 'N/A'
            
            # Format opinion terms (array of strings) as colored badges
            opinion_terms = review.get('opinion_terms', [])
            opinion_badge_color = '#dc3545' if is_negative else '#28a745'  # Red for negative, green for positive
            opinion_badges = [
                dbc.Badge(term, 
                         style={
                             'backgroundColor': opinion_badge_color,
                             'color': 'white',
                             'marginRight': '0.25rem',
                             'marginBottom': '0.25rem',
                             'fontSize': '0.8rem'
                         })
                for term in opinion_terms
            ] if opinion_terms else [html.Span("N/A", className="text-muted", style={'fontSize': '0.85rem'})]
            
            return dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Strong(f"Review ID: {review.get('review_uid', 'Unknown')}", style={'fontSize': '0.9rem'}),
                                dbc.Badge(sentiment.replace('_', ' ').title(), color=sentiment_color, className="ms-2"),
                            ]),
                            html.Div([
                                html.Span(stars, style={'color': '#ffc107', 'fontSize': '1rem'}),
                                html.Span(f" ({star_rating}/5)", className="text-muted ms-2", style={'fontSize': '0.85rem'}),
                            ], className="mt-1"),
                        ], md=8),
                        dbc.Col([
                            html.Div([
                                html.Small(f"Date: {review.get('review_date', 'N/A')}", className="text-muted d-block"),
                                html.Small(f"Channel: {review.get('channel', 'N/A')}", className="text-muted d-block"),
                            ], className="text-end")
                        ], md=4),
                    ]),
                    html.Hr(className="my-2"),
                    html.P(review.get('review_text', 'No review text available.'), 
                           style={'fontSize': '0.95rem', 'lineHeight': '1.6', 'marginTop': '1rem'}),
                    html.Hr(className="my-2"),
                    dbc.Row([
                        dbc.Col([
                            html.Strong("Evidence:", className="text-muted", style={'fontSize': '0.85rem'}),
                            html.P(evidence_text, style={'fontSize': '0.85rem', 'marginTop': '0.25rem', 'fontStyle': 'italic'}),
                        ], md=6),
                        dbc.Col([
                            html.Strong("Opinion Terms:", className="text-muted", style={'fontSize': '0.85rem'}),
                            html.Div(opinion_badges, style={'marginTop': '0.25rem'}),
                        ], md=6),
                    ]),
                ], style={'padding': '1rem'})
            ], className="mb-3", style={'border': f'1px solid {border_color}', 'borderRadius': '8px'})
        
        # Create sections for negative and positive reviews
        sections = []
        
        # Negative Reviews Section
        if negative_reviews:
            negative_cards = [create_review_card(review, is_negative=True) for review in negative_reviews]
            sections.append(
                html.Div([
                    html.Div([
                        html.H6([
                            html.I(className="bi bi-chat-left-text-fill me-2", style={'color': '#dc3545'}),
                            f"Negative Reviews ({len(negative_reviews)})"
                        ], style={'fontWeight': '600', 'color': '#dc3545', 'marginBottom': '1rem'}),
                    ]),
                    html.Div(negative_cards)
                ], className="mb-4")
            )
        
        # Positive Reviews Section
        if positive_reviews:
            positive_cards = [create_review_card(review, is_negative=False) for review in positive_reviews]
            sections.append(
                html.Div([
                    html.Div([
                        html.H6([
                            html.I(className="bi bi-check-circle-fill me-2", style={'color': '#28a745'}),
                            f"Positive Reviews ({len(positive_reviews)})"
                        ], style={'fontWeight': '600', 'color': '#28a745', 'marginBottom': '1rem'}),
                    ]),
                    html.Div(positive_cards)
                ], className="mb-4")
            )
        
        total_reviews = len(negative_reviews) + len(positive_reviews)
        return html.Div([
            html.P([
                f"Showing {total_reviews} review(s) from selected timeframe: ",
                html.Span(f"{len(negative_reviews)} negative", style={'color': '#dc3545', 'fontWeight': '600'}),
                f", {len(positive_reviews)} positive",
            ], className="text-muted mb-3", style={'fontSize': '0.9rem', 'fontWeight': '500'}),
            html.Div(sections)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error loading reviews: {str(e)}", color="danger")

# Clientside callback to scroll to property when map is clicked
app.clientside_callback(
    """
    function(propertyId) {
        if (!propertyId) {
            return window.dash_clientside.no_update;
        }
        
        console.log('🗺️ Clientside callback triggered with propertyId:', propertyId);
        
        // Small delay to ensure DOM is ready
        setTimeout(function() {
            const elementId = 'property-card-' + propertyId;
            console.log('🔍 Looking for element:', elementId);
            const element = document.getElementById(elementId);
            
            if (element) {
                console.log('✅ Element found, scrolling...');
                element.scrollIntoView({ 
                    behavior: 'smooth', 
                    block: 'center' 
                });
                
                // Add a temporary highlight effect
                element.style.transition = 'all 0.3s ease';
                element.style.transform = 'scale(1.05)';
                element.style.boxShadow = '0 8px 24px rgba(220, 53, 69, 0.3)';
                
                setTimeout(function() {
                    element.style.transform = 'scale(1)';
                    element.style.boxShadow = '';
                }, 600);
            } else {
                console.error('❌ Element not found:', elementId);
                console.log('Available property cards:', Array.from(document.querySelectorAll('[id^="property-card-"]')).map(el => el.id));
            }
        }, 300);
        
        return window.dash_clientside.no_update;
    }
    """,
    Output('scroll-to-property', 'data', allow_duplicate=True),
    Input('scroll-to-property', 'data'),
    prevent_initial_call=True
)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


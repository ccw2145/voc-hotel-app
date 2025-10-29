import dash
from dash import dcc, html, Input, Output, State, callback_context, dash_table
import dash_bootstrap_components as dbc
from dotenv import load_dotenv
import os
import sys
import plotly.graph_objects as go

# Load environment variables FIRST
load_dotenv()

# Add src directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import services
from services.property_service import property_service
from services.email_service import email_service
from services.recommendations_service import recommendations_service
from services.diagnostics_service import diagnostics_service
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
app = dash.Dash(__name__, external_stylesheets=[
    dbc.themes.BOOTSTRAP,
    "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css"
])
app.title = "Lakehouse Inn - Voice of Customer"

# Suppress callback exceptions for dynamically created components
app.config.suppress_callback_exceptions = True

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
                html.H1("Property List", className="mb-2", style={'fontWeight': '700'}),
                html.Div(id='hq-properties-subtitle', className="mb-4"),
            ], className="my-4 py-3"),
        ], style={'maxWidth': '1400px'}),
        
        # Executive KPIs Section
        html.Div(id='hq-executive-kpis', className="mb-5"),
        
        # Analytics & Insights Section
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Issue Analytics", className="mb-4", style={'fontWeight': '600'}),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='trend-chart-container')
                        ], md=6),
                        dbc.Col([
                            html.Div(id='aspect-breakdown-chart')
                        ], md=6),
                    ]),
                    dbc.Row([
                        dbc.Col([
                            html.Div(id='regional-comparison-chart')
                        ], md=12)
                    ], className="mt-4")
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
                    dcc.Graph(id='properties-map', config={'displayModeBar': False}, 
                             style={'height': '500px'}),
                ], style={'padding': '1.5rem'})
            ], style={'border': 'none', 'borderRadius': '12px'}, className="mb-5")
        ], style={'maxWidth': '1400px'}),
        
        # Flagged Properties - Grouped View
        dbc.Container([
            html.H3([
                html.Span("🚨", style={'marginRight': '0.5rem'}),
                "Properties Requiring Attention"
            ], className="mb-4", style={'fontWeight': '600', 'fontSize': '1.75rem'}),
            html.Div(id='flagged-properties-grouped')
        ], style={'maxWidth': '1400px'}, className="mb-5"),
        
        # All Properties - Compact Summary
        dbc.Container([
            html.Div(id='all-properties-summary')
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
        ], style={'maxWidth': '1400px'}),
        
        # Show property details (references global placeholder)
        dbc.Container([
            html.Div(id='hq-selected-property-details-container'),
        ], style={'maxWidth': '1400px'}, className="mb-4"),
        
        # Embedded Databricks AI/BI Dashboard (filtered by property)
        dbc.Container([
            html.H4("Property Analytics Dashboard", className="mb-3", style={'fontWeight': '600'}),
            html.Div(id='hq-filtered-dashboard-iframe'),
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        # Reviews Deep Dive Section
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Reviews Deep Dive", className="mb-3", style={'fontWeight': '600'}),
                    html.P("Select an aspect to analyze detailed review insights", 
                          className="text-muted mb-3",
                          style={'fontSize': '0.95rem'}),
                    dcc.Dropdown(
                        id='hq-aspect-selector',
                        placeholder="Select an aspect to analyze...",
                        className="mb-3",
                        style={'fontSize': '1rem'}
                    ),
                ], style={'padding': '1.5rem'})
            ], className="mb-4", style={'border': 'none', 'borderRadius': '12px'}),
            html.Div(id='hq-reviews-deep-dive-content'),
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        dbc.Container([
            # Genie Query Section
            dbc.Card([
                dbc.CardBody([
                    html.H4("Ask Genie", className="mb-3", style={'fontWeight': '600'}),
                    dbc.InputGroup([
                        dbc.Input(
                            id='hq-genie-input',
                            placeholder="Ask a question about this property...",
                            type="text",
                            style={'borderRadius': '8px 0 0 8px', 'padding': '0.75rem'}
                        ),
                        dbc.Button(
                            "Ask",
                            id='btn-ask-genie-hq',
                            color="danger",
                            style={'borderRadius': '0 8px 8px 0', 'padding': '0.75rem 1.5rem', 'fontWeight': '500'}
                        ),
                    ]),
                ], style={'padding': '1.5rem'})
            ], className="my-4", style={'border': 'none', 'borderRadius': '12px'}),
            html.Div(id='hq-genie-results-container', className="my-4"),
        ], style={'maxWidth': '1400px'}),
        
        dbc.Container([
            dbc.Row([
                dbc.Col([
                    dbc.Button("Back to Properties", id='btn-back-to-properties', color="secondary", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto"),
                dbc.Col([
                    dbc.Button("Proceed to Send Email", id='btn-proceed-to-email', color="danger", 
                              size="lg", style={'fontWeight': '500'})
                ], width="auto", className="ms-auto"),
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
        dbc.Container([
            html.Div([
                html.H1("Property Manager Dashboard", className="mb-2", style={'fontWeight': '700'}),
                html.P("Monitor your property's performance", 
                      className="mb-4",
                      style={'fontSize': '1.125rem', 'color': '#6c757d'}),
            ], className="my-4"),
            
            # Property selection dropdown
            dbc.Card([
                dbc.CardBody([
                    html.Label("Select Your Property:", 
                              className="mb-2",
                              style={'fontWeight': '600', 'fontSize': '1rem'}),
                    dcc.Dropdown(
                        id='pm-property-select',
                        placeholder="Select a property...",
                        className="mb-2",
                        style={'fontSize': '1rem'}
                    ),
                ], style={'padding': '1.5rem'})
            ], className="mb-4", style={'border': 'none', 'borderRadius': '12px'}),
        ], style={'maxWidth': '1400px'}),
        
        dbc.Container([
            html.Div(id='pm-property-details'),
        ], style={'maxWidth': '1400px'}, className="mb-4"),
        
        # Reviews Deep Dive Section for PM
        dbc.Container([
            dbc.Card([
                dbc.CardBody([
                    html.H4("📊 Reviews Deep Dive", className="mb-3", style={'fontWeight': '600'}),
                    html.P("Select an aspect to analyze detailed review insights", 
                          className="text-muted mb-3",
                          style={'fontSize': '0.95rem'}),
                    dcc.Dropdown(
                        id='pm-aspect-selector',
                        placeholder="Select an aspect to analyze...",
                        className="mb-3",
                        style={'fontSize': '1rem'}
                    ),
                ], style={'padding': '1.5rem'})
            ], className="mb-4", style={'border': 'none', 'borderRadius': '12px'}),
            html.Div(id='pm-reviews-deep-dive-content'),
        ], style={'maxWidth': '1400px'}, className="my-4"),
        
        dbc.Container([
            # Genie Query Section
            dbc.Card([
                dbc.CardBody([
                    html.H4("Ask Genie", className="mb-3", style={'fontWeight': '600'}),
                    dbc.InputGroup([
                        dbc.Input(
                            id='pm-genie-input',
                            placeholder="Ask a question about this property...",
                            type="text",
                            style={'borderRadius': '8px 0 0 8px', 'padding': '0.75rem'}
                        ),
                        dbc.Button(
                            "Ask",
                            id='btn-ask-genie-pm',
                            color="danger",
                            style={'borderRadius': '0 8px 8px 0', 'padding': '0.75rem 1.5rem', 'fontWeight': '500'}
                        ),
                    ]),
                ], style={'padding': '1.5rem'})
            ], className="my-4", style={'border': 'none', 'borderRadius': '12px'}),
            html.Div(id='pm-genie-results', className="my-4"),
        ], style={'maxWidth': '1400px'}),
        
        dbc.Container([
            dbc.Button("Back to Role Selection", id='btn-back-to-roles', color="secondary", 
                      size="lg", className="mb-4", style={'fontWeight': '500'})
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
])

# ========================================
# CALLBACKS
# ========================================

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
     Input('btn-proceed-to-email', 'n_clicks'),
     Input('btn-back-to-dashboard', 'n_clicks'),
     Input('btn-back-to-roles', 'n_clicks'),
     Input('btn-switch-hq', 'n_clicks'),
     Input('btn-switch-pm', 'n_clicks')],
    prevent_initial_call='initial_duplicate'  # Only prevent on initial duplicate, not on component creation
)
def handle_button_clicks(hq, pm, back_prop, proceed, back_dash, back_roles, switch_hq, switch_pm):
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
    elif button_id == 'btn-proceed-to-email':
        print(f"   ➡️  Navigating to: hq-email")
        return 'hq-email'
    elif button_id == 'btn-back-to-dashboard':
        print(f"   ➡️  Navigating to: hq-dashboard")
        return 'hq-dashboard'
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
    Input('current-screen', 'data')
)
def load_hq_properties_subtitle(screen):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        # Get stats
        stats = property_service.get_diagnostics_kpis()
        flagged = property_service.get_flagged_properties()
        
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

# Load executive KPIs for HQ
@app.callback(
    Output('hq-executive-kpis', 'children'),
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_executive_kpis(screen):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        print(f"🔄 Loading executive KPIs for screen: {screen}")
        kpis = property_service.get_diagnostics_kpis()
        print(f"✅ Loaded KPIs: {kpis}")
        
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
                                html.Span(f"{kpis['avg_negative_reviews_7d']}% negative (7d)", 
                                         style={'color': '#6c757d', 'fontSize': '0.875rem'})
                            ])
                        ], style={'padding': '1.5rem'})
                    ], style={'border': 'none', 'borderRadius': '12px', 'height': '100%'})
                ], md=6, lg=3, className="mb-4"),
                
                # Reviews Processed
                dbc.Col([
                    dbc.Card([
                        dbc.CardBody([
                            html.Div([
                                html.Div([
                                    html.I(className="bi bi-file-earmark-text", 
                                          style={'fontSize': '1.5rem', 'color': '#17a2b8', 'marginBottom': '0.5rem'}),
                                ]),
                                html.H3(str(kpis['reviews_processed_today']), 
                                       className="mb-1",
                                       style={'fontWeight': '700', 'fontSize': '2.5rem', 'color': '#212529'}),
                                html.P("Reviews Processed", 
                                      className="mb-2 text-muted",
                                      style={'fontSize': '0.95rem', 'fontWeight': '500'}),
                                html.Span("Today", style={'color': '#6c757d', 'fontSize': '0.875rem'})
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
            ], className="g-3")
        ], style={'maxWidth': '1400px'})
        
    except Exception as e:
        print(f"❌ Error loading executive KPIs: {str(e)}")
        import traceback
        traceback.print_exc()
        return html.Div()

# Load properties map
@app.callback(
    Output('properties-map', 'figure'),
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_properties_map(screen):
    print(f"\n{'='*60}")
    print(f"🗺️ LOAD_PROPERTIES_MAP CALLED")
    print(f"   screen: {screen}")
    print(f"{'='*60}\n")
    
    if screen != 'hq-properties':
        print(f"   ⏭️  Screen is '{screen}', returning empty figure")
        return go.Figure()
    
    try:
        print(f"🔄 Loading properties map for screen: {screen}")
        properties = property_service.get_all_properties()
        print(f"   Got {len(properties)} properties")
        
        # Get flagged properties once
        flagged = property_service.get_flagged_properties()
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
                        hover_text = f"<b>{d['name']}</b><br>Status: {d['status']}<br>No issues - All clear!"
                    hover_texts.append(hover_text)
                
                # Only make flagged properties clickable (have customdata)
                # Healthy properties won't trigger scroll since they're not in the accordion
                if status in ['Critical', 'Warning']:
                    customdata = [d['id'] for d in status_data]
                else:
                    customdata = None  # Healthy properties not clickable
                
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

# Handle map clicks and scroll to property
@app.callback(
    Output('scroll-to-property', 'data'),
    Input('properties-map', 'clickData'),
    prevent_initial_call=True
)
def handle_map_click(click_data):
    if not click_data:
        print("⚠️ Map clicked but no click_data")
        return None
    
    try:
        # Extract property ID from customdata
        customdata = click_data['points'][0].get('customdata')
        
        if not customdata:
            print("⚠️ Map clicked but no customdata (probably a healthy property - not clickable)")
            return None
            
        property_id = customdata
        print(f"\n{'='*60}")
        print(f"🗺️ MAP CLICKED")
        print(f"   Property ID: {property_id}")
        print(f"   Will scroll to: property-card-{property_id}")
        print(f"{'='*60}\n")
        return property_id
    except Exception as e:
        print(f"❌ Error handling map click: {str(e)}")
        print(f"   click_data: {click_data}")
        import traceback
        traceback.print_exc()
        return None

# Load flagged properties grouped by region
@app.callback(
    Output('flagged-properties-grouped', 'children'),
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_flagged_properties_grouped(screen):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        print(f"🔄 Loading grouped flagged properties for screen: {screen}")
        grouped_data = property_service.get_properties_by_region_and_severity()
        
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
                            html.Span(f" {int(round(aspect['negative_percentage']))}%", 
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
                            html.Span(f" {int(round(aspect['negative_percentage']))}%", 
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
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_all_properties_summary(screen):
    if screen != 'hq-properties':
        return html.Div()
    
    try:
        print(f"🔄 Loading all properties summary for screen: {screen}")
        properties = property_service.get_all_properties()
        
        # Get flagged properties to exclude them
        flagged = property_service.get_flagged_properties()
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
    State('current-screen', 'data'),
    prevent_initial_call=True
)
def load_expanded_properties_list(is_open, screen):
    if not is_open or screen != 'hq-properties':
        return html.Div()
    
    try:
        # Get grouped healthy properties
        grouped_properties = property_service.get_healthy_properties_grouped()
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

# Load analytics charts
@app.callback(
    [Output('trend-chart-container', 'children'),
     Output('aspect-breakdown-chart', 'children'),
     Output('regional-comparison-chart', 'children')],
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_analytics_charts(screen):
    if screen != 'hq-properties':
        return html.Div(), html.Div(), html.Div()
    
    try:
        import plotly.graph_objects as go
        
        # Get data
        trend_data = property_service.get_trend_data(days_back=30)
        aspect_data = property_service.get_aspect_breakdown()
        regional_data = property_service.get_regional_performance_summary()
        
        # Debug: Print what the chart is receiving
        print(f"\n📊 Chart received regional_data:")
        for region in regional_data[:10]:
            print(f"  {region['region']}: Total={region['total']}, Flagged={region['flagged']}, Healthy={region['total']-region['flagged']}")
        if len(regional_data) > 10:
            print(f"  ... and {len(regional_data)-10} more regions")
        
        # Trend Chart
        if trend_data:
            trend_fig = go.Figure()
            trend_fig.add_trace(go.Scatter(
                x=[d['date'] for d in trend_data],
                y=[d['issues_opened'] for d in trend_data],
                mode='lines+markers',
                name='Issues Opened',
                line=dict(color='#dc3545', width=3),
                marker=dict(size=6)
            ))
            trend_fig.update_layout(
                title="Issue Trend (Last 30 Days)",
                xaxis_title="Date",
                yaxis_title="Issues Opened",
                height=300,
                margin=dict(l=40, r=40, t=40, b=40),
                hovermode='x unified',
                plot_bgcolor='#f8f9fa'
            )
            trend_chart = dcc.Graph(figure=trend_fig, config={'displayModeBar': False})
        else:
            trend_chart = dbc.Alert("No trend data available", color="info")
        
        # Aspect Breakdown Chart
        if aspect_data:
            aspect_fig = go.Figure()
            aspect_fig.add_trace(go.Bar(
                y=[d['aspect'] for d in aspect_data[:10]],  # Top 10
                x=[d['count'] for d in aspect_data[:10]],
                orientation='h',
                marker=dict(
                    color=[d['avg_negative'] for d in aspect_data[:10]],
                    colorscale='YlOrRd',
                    showscale=True,
                    colorbar=dict(title="Avg %")
                ),
                text=[f"{d['count']} issues" for d in aspect_data[:10]],
                textposition='auto',
                hovertemplate='<b>%{y}</b><br>Count: %{x}<br>Avg Negative: %{marker.color:.1f}%<extra></extra>'
            ))
            aspect_fig.update_layout(
                title="Top Issues by Aspect",
                xaxis_title="Number of Issues",
                yaxis_title="",
                height=300,
                margin=dict(l=150, r=40, t=40, b=40),
                plot_bgcolor='#f8f9fa'
            )
            aspect_chart = dcc.Graph(figure=aspect_fig, config={'displayModeBar': False})
        else:
            aspect_chart = dbc.Alert("No aspect data available", color="info")
        
        # Regional Comparison Chart
        if regional_data:
            regional_fig = go.Figure()
            # Healthy properties first (green, bottom of stack = good)
            regional_fig.add_trace(go.Bar(
                x=[d['region'] for d in regional_data[:15]],  # Top 15
                y=[d['total'] - d['flagged'] for d in regional_data[:15]],
                name='Healthy',
                marker=dict(color='#198754'),
                hovertemplate='<b>%{x}</b><br>Healthy: %{y}<extra></extra>'
            ))
            # Flagged properties on top (red = problems)
            regional_fig.add_trace(go.Bar(
                x=[d['region'] for d in regional_data[:15]],
                y=[d['flagged'] for d in regional_data[:15]],
                name='Flagged',
                marker=dict(color='#dc3545'),
                hovertemplate='<b>%{x}</b><br>Flagged: %{y}<extra></extra>'
            ))
            regional_fig.update_layout(
                title="Regional Performance Comparison",
                xaxis_title="Region",
                yaxis_title="Number of Properties",
                barmode='stack',
                height=300,
                margin=dict(l=40, r=40, t=40, b=80),
                xaxis_tickangle=-45,
                plot_bgcolor='#f8f9fa',
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            regional_chart = dcc.Graph(figure=regional_fig, config={'displayModeBar': False})
        else:
            regional_chart = dbc.Alert("No regional data available", color="info")
        
        return trend_chart, aspect_chart, regional_chart
        
    except Exception as e:
        print(f"❌ Error loading analytics charts: {str(e)}")
        import traceback
        traceback.print_exc()
        error_msg = dbc.Alert(f"Error loading analytics: {str(e)}", color="danger")
        return error_msg, error_msg, error_msg

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
            print(f"   ⚠️  Property not found!")
            return dbc.Alert("Property not found.", color="warning")
        print(f"   ✅ Property details loaded!")
        
        # Create aspects table
        aspects_data = []
        for aspect in details['aspects']:
            status_color = 'critical' if aspect['status'] == 'critical' else (
                'warning' if aspect['status'] == 'warning' else 'good')
            aspects_data.append({
                'Aspect': aspect['name'],
                'Negative Reviews': f"{aspect['percentage']}%",
                'Status': aspect['status'].upper()
            })
        
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
                
                html.Hr(),
                
                html.H4("Aspect Analysis", className="mb-3 mt-4", style={'fontWeight': '600'}),
                dash_table.DataTable(
                    data=aspects_data,
                    columns=[{'name': i, 'id': i} for i in aspects_data[0].keys()],
                    style_cell={'textAlign': 'left', 'padding': '12px', 'fontSize': '0.95rem'},
                    style_header={
                        'backgroundColor': custom_style['primary'], 
                        'color': 'white', 
                        'fontWeight': 'bold',
                        'fontSize': '1rem',
                        'padding': '12px'
                    },
                    style_data_conditional=[
                        {'if': {'filter_query': '{Status} contains "CRITICAL"'},
                         'backgroundColor': '#ffebee', 'color': custom_style['critical'], 'fontWeight': '500'},
                        {'if': {'filter_query': '{Status} contains "WARNING"'},
                         'backgroundColor': '#fff9c4', 'color': custom_style['warning'], 'fontWeight': '500'},
                    ],
                )
            ], style={'padding': '2rem'})
        ], style={'border': 'none', 'borderRadius': '12px', 'boxShadow': '0 4px 12px rgba(0,0,0,0.1)'})
    except Exception as e:
        return dbc.Alert(f"Error loading property details: {str(e)}", color="danger")

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
            return dbc.Alert("Property not found.", color="warning")
        
        # Construct location string
        location = f"{details['city']}, {details['state']}"
        
        # Base dashboard URL - using published URL format for iframe embedding
        # Reference: https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/dashboardsv3/01f0ab936a8815ffbc5b0dd3d8ca0f9f/published/pages/a7cbab78
        base_url = "https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/dashboardsv3/01f0ab936a8815ffbc5b0dd3d8ca0f9f/published/pages/a7cbab78"
        
        # Add location filter parameter
        # URL encode the location string (double encoding needed for Databricks filters)
        from urllib.parse import quote
        # Double encode to match Databricks expected format
        encoded_location = quote(quote(location, safe=''), safe='')
        
        # Add filter parameters to the URL
        # The format for Databricks dashboard filters is: ?o=<workspace_id>&f_<page_id>~<filter_id>=<value>
        # filtered_url = f"{base_url}?o=604717363374831&f_a7cbab78~57a7e64b={encoded_location}"
        filtered_url=f"https://fe-vm-voc-lakehouse-inn-workspace.cloud.databricks.com/embed/dashboardsv3/01f0ab936a8815ffbc5b0dd3d8ca0f9f?o=604717363374831&f_cda77b68%7E7b3b0339={encoded_location}&f_a7cbab78%7E27ece451=2025-06-30T00%253A00%253A00.000%7E2025-09-01T23%253A59%253A59.999&f_a7cbab78%7E1179387e=_all_"

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
        deep_dive_data = property_service.get_reviews_deep_dive(property_id, selected_aspect)
        deep_dive = deep_dive_data.get('deep_dive')
        
        if not deep_dive:
            return dbc.Alert("No data available for this aspect.", color="info")
        
        # Create severity badge color
        severity = deep_dive['severity'].lower()
        severity_color = 'danger' if severity == 'critical' else ('warning' if severity == 'warning' else 'success')
        
        return dbc.Card([
            dbc.CardBody([
                # Header with metrics
                dbc.Row([
                    dbc.Col([
                        html.H5(deep_dive['aspect'], className="mb-2", style={'fontWeight': '600'}),
                        dbc.Badge(
                            deep_dive['severity'], 
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
                                html.Small("Total Reviews", className="text-muted"),
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
                
                html.Hr(className="my-4"),
                
                # Individual Reviews Browser
                html.Div([
                    html.Div([
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
                                    style={'width': '100%'}
                                ),
                            ], md=3),
                        ], className="mb-3"),
                    ]),
                    html.Div(id='hq-individual-reviews-list')
                ], style={'padding': '1.5rem', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'}),
                
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
        
    except Exception as e:
        return dbc.Alert(f"Error loading deep dive: {str(e)}", color="danger")

# Genie query handler (HQ)
@app.callback(
    Output('hq-genie-results-container', 'children'),
    [Input('btn-ask-genie-hq', 'n_clicks')],
    [State('hq-genie-input', 'value')],
    prevent_initial_call=True
)
def ask_genie_hq(n_clicks, query):
    if not n_clicks or not query:
        return html.Div()
    
    try:
        result = genie_service.continue_conversation(query)
        
        if 'error' in result:
            return dbc.Alert(f"Error: {result['error']}", color="danger")
        
        if not result.get('results'):
            return dbc.Alert("No results found.", color="info")
        
        output = [
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-chat-dots me-2"),
                    html.Strong("Your Question:", style={'fontSize': '0.95rem'}),
                ], style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody([
                    html.P(query, style={'fontSize': '1rem', 'color': '#495057', 'marginBottom': '0'})
                ])
            ], className="mb-3")
        ]
        
        response_count = 0
        for idx, item in enumerate(result['results']):
            if item['type'] == 'text':
                response_count += 1
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-robot me-2", style={'color': '#0d6efd'}),
                            html.Strong(f"Genie Response {response_count}:", style={'fontSize': '0.95rem'}),
                        ], style={'backgroundColor': '#e7f1ff'}),
                        dbc.CardBody([
                            html.P(item['content'], style={'fontSize': '1rem', 'lineHeight': '1.6', 'marginBottom': '0'})
                        ])
                    ], className="mb-3", style={'border': '1px solid #0d6efd'})
                )
            
            elif item['type'] == 'table':
                # Create collapsible SQL query section
                query_text = item.get('query', 'No query available')
                description = item.get('description', 'Query Results')
                
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-table me-2", style={'color': '#198754'}),
                            html.Strong(description, style={'fontSize': '1rem'}),
                        ], style={'backgroundColor': '#d1e7dd'}),
                        dbc.CardBody([
                            # SQL Query Accordion
                            dbc.Accordion([
                                dbc.AccordionItem([
                                    html.Pre(
                                        query_text,
                                        style={
                                            'backgroundColor': '#2d2d2d',
                                            'color': '#f8f8f2',
                                            'padding': '1rem',
                                            'borderRadius': '8px',
                                            'fontSize': '0.875rem',
                                            'overflowX': 'auto',
                                            'marginBottom': '0',
                                            'fontFamily': 'Monaco, Consolas, monospace'
                                        }
                                    )
                                ], title="📝 View Generated SQL", item_id=f"sql-{idx}")
                            ], start_collapsed=True, className="mb-3"),
                            
                            # Data Table
                            html.Div([
                                html.Strong(f"📊 Results: {len(item.get('data', []))} rows", 
                                          style={'fontSize': '0.9rem', 'color': '#495057', 'marginBottom': '0.5rem', 'display': 'block'}),
                                dash_table.DataTable(
                                    data=item.get('data', []),
                                    columns=[{'name': col, 'id': col} for col in item.get('columns', [])],
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '12px',
                                        'fontSize': '0.9rem',
                                        'fontFamily': 'inherit'
                                    },
                                    style_header={
                                        'backgroundColor': '#198754',
                                        'color': 'white',
                                        'fontWeight': 'bold',
                                        'border': '1px solid #198754'
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
                                    page_size=10,
                                ) if item.get('data') else html.P("No data returned", className="text-muted")
                            ])
                        ])
                    ], className="mb-3", style={'border': '1px solid #198754'})
                )
            
            elif item['type'] == 'query':
                # Query without data
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-code-square me-2", style={'color': '#6c757d'}),
                            html.Strong(item.get('description', 'Generated Query'), style={'fontSize': '1rem'}),
                        ], style={'backgroundColor': '#e2e3e5'}),
                        dbc.CardBody([
                            html.Pre(
                                item.get('query', 'No query available'),
                                style={
                                    'backgroundColor': '#2d2d2d',
                                    'color': '#f8f8f2',
                                    'padding': '1rem',
                                    'borderRadius': '8px',
                                    'fontSize': '0.875rem',
                                    'overflowX': 'auto',
                                    'marginBottom': '0',
                                    'fontFamily': 'Monaco, Consolas, monospace'
                                }
                            )
                        ])
                    ], className="mb-3")
                )
        
        return output
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Failed to query Genie: {str(e)}", color="danger")

# Genie query handler (PM)
@app.callback(
    Output('pm-genie-results', 'children'),
    [Input('btn-ask-genie-pm', 'n_clicks')],
    [State('pm-genie-input', 'value')],
    prevent_initial_call=True
)
def ask_genie_pm(n_clicks, query):
    if not n_clicks or not query:
        return html.Div()
    
    try:
        result = genie_service.continue_conversation(query)
        
        if 'error' in result:
            return dbc.Alert(f"Error: {result['error']}", color="danger")
        
        if not result.get('results'):
            return dbc.Alert("No results found.", color="info")
        
        output = [
            dbc.Card([
                dbc.CardHeader([
                    html.I(className="bi bi-chat-dots me-2"),
                    html.Strong("Your Question:", style={'fontSize': '0.95rem'}),
                ], style={'backgroundColor': '#f8f9fa'}),
                dbc.CardBody([
                    html.P(query, style={'fontSize': '1rem', 'color': '#495057', 'marginBottom': '0'})
                ])
            ], className="mb-3")
        ]
        
        response_count = 0
        for idx, item in enumerate(result['results']):
            if item['type'] == 'text':
                response_count += 1
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-robot me-2", style={'color': '#0d6efd'}),
                            html.Strong(f"Genie Response {response_count}:", style={'fontSize': '0.95rem'}),
                        ], style={'backgroundColor': '#e7f1ff'}),
                        dbc.CardBody([
                            html.P(item['content'], style={'fontSize': '1rem', 'lineHeight': '1.6', 'marginBottom': '0'})
                        ])
                    ], className="mb-3", style={'border': '1px solid #0d6efd'})
                )
            
            elif item['type'] == 'table':
                query_text = item.get('query', 'No query available')
                description = item.get('description', 'Query Results')
                
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-table me-2", style={'color': '#198754'}),
                            html.Strong(description, style={'fontSize': '1rem'}),
                        ], style={'backgroundColor': '#d1e7dd'}),
                        dbc.CardBody([
                            dbc.Accordion([
                                dbc.AccordionItem([
                                    html.Pre(
                                        query_text,
                                        style={
                                            'backgroundColor': '#2d2d2d',
                                            'color': '#f8f8f2',
                                            'padding': '1rem',
                                            'borderRadius': '8px',
                                            'fontSize': '0.875rem',
                                            'overflowX': 'auto',
                                            'marginBottom': '0',
                                            'fontFamily': 'Monaco, Consolas, monospace'
                                        }
                                    )
                                ], title="📝 View Generated SQL", item_id=f"pm-sql-{idx}")
                            ], start_collapsed=True, className="mb-3"),
                            
                            html.Div([
                                html.Strong(f"📊 Results: {len(item.get('data', []))} rows", 
                                          style={'fontSize': '0.9rem', 'color': '#495057', 'marginBottom': '0.5rem', 'display': 'block'}),
                                dash_table.DataTable(
                                    data=item.get('data', []),
                                    columns=[{'name': col, 'id': col} for col in item.get('columns', [])],
                                    style_cell={
                                        'textAlign': 'left',
                                        'padding': '12px',
                                        'fontSize': '0.9rem',
                                        'fontFamily': 'inherit'
                                    },
                                    style_header={
                                        'backgroundColor': '#198754',
                                        'color': 'white',
                                        'fontWeight': 'bold',
                                        'border': '1px solid #198754'
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
                                    page_size=10,
                                ) if item.get('data') else html.P("No data returned", className="text-muted")
                            ])
                        ])
                    ], className="mb-3", style={'border': '1px solid #198754'})
                )
            
            elif item['type'] == 'query':
                output.append(
                    dbc.Card([
                        dbc.CardHeader([
                            html.I(className="bi bi-code-square me-2", style={'color': '#6c757d'}),
                            html.Strong(item.get('description', 'Generated Query'), style={'fontSize': '1rem'}),
                        ], style={'backgroundColor': '#e2e3e5'}),
                        dbc.CardBody([
                            html.Pre(
                                item.get('query', 'No query available'),
                                style={
                                    'backgroundColor': '#2d2d2d',
                                    'color': '#f8f8f2',
                                    'padding': '1rem',
                                    'borderRadius': '8px',
                                    'fontSize': '0.875rem',
                                    'overflowX': 'auto',
                                    'marginBottom': '0',
                                    'fontFamily': 'Monaco, Consolas, monospace'
                                }
                            )
                        ])
                    ], className="mb-3")
                )
        
        return output
    except Exception as e:
        import traceback
        traceback.print_exc()
        return dbc.Alert(f"Failed to query Genie: {str(e)}", color="danger")

# Load PM property dropdown
@app.callback(
    Output('pm-property-select', 'options'),
    Input('current-screen', 'data'),
    prevent_initial_call=False
)
def load_pm_properties(screen):
    if screen != 'pm-dashboard':
        return dash.no_update
    
    try:
        properties = property_service.get_all_properties()
        options = [{'label': f"{p['name']} ({p['city']}, {p['state']})", 'value': p['property_id']} 
                   for p in properties]
        print(f"✅ Loaded {len(options)} properties for PM dropdown")
        return options
    except Exception as e:
        print(f"⚠️  Error loading PM properties: {str(e)}")
        return dash.no_update

# Load PM property details
@app.callback(
    Output('pm-property-details', 'children'),
    Input('pm-property-select', 'value')
)
def load_pm_property_details(property_id):
    if not property_id:
        return dbc.Alert("Please select a property to view details.", color="info")
    
    try:
        details = property_service.get_property_details(property_id)
        if not details:
            return dbc.Alert("Property not found.", color="warning")
        
        aspects_data = []
        for aspect in details['aspects']:
            aspects_data.append({
                'Aspect': aspect['name'],
                'Negative Reviews': f"{aspect['percentage']}%",
                'Status': aspect['status'].upper()
            })
        
        return [
            dbc.Card([
                dbc.CardBody([
                    html.H4(details['name'], className="card-title"),
                    html.P(f"{details['reviews_count']} reviews • Rating: {details['avg_rating']}/5.0",
                          className="text-muted"),
                    html.H5("Aspect Performance", className="mt-4 mb-3"),
                    dash_table.DataTable(
                        data=aspects_data,
                        columns=[{'name': i, 'id': i} for i in aspects_data[0].keys()],
                        style_cell={'textAlign': 'left', 'padding': '10px'},
                        style_header={'backgroundColor': custom_style['primary'], 'color': 'white', 'fontWeight': 'bold'},
                        style_data_conditional=[
                            {'if': {'filter_query': '{Status} contains "CRITICAL"'},
                             'backgroundColor': '#ffebee', 'color': custom_style['critical']},
                            {'if': {'filter_query': '{Status} contains "WARNING"'},
                             'backgroundColor': '#fff9c4', 'color': custom_style['warning']},
                        ],
                    )
                ])
            ])
        ]
    except Exception as e:
        return dbc.Alert(f"Error loading property details: {str(e)}", color="danger")

# Load aspect options for PM Reviews Deep Dive
@app.callback(
    Output('pm-aspect-selector', 'options'),
    Input('pm-property-select', 'value')
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
     Input('pm-property-select', 'value')]
)
def load_pm_reviews_deep_dive(selected_aspect, property_id):
    if not property_id or not selected_aspect:
        return html.Div()
    
    try:
        deep_dive_data = property_service.get_reviews_deep_dive(property_id, selected_aspect)
        deep_dive = deep_dive_data.get('deep_dive')
        
        if not deep_dive:
            return dbc.Alert("No data available for this aspect.", color="info")
        
        # Create severity badge color
        severity = deep_dive['severity'].lower()
        severity_color = 'danger' if severity == 'critical' else ('warning' if severity == 'warning' else 'success')
        
        return dbc.Card([
            dbc.CardBody([
                # Header with metrics
                dbc.Row([
                    dbc.Col([
                        html.H5(deep_dive['aspect'], className="mb-2", style={'fontWeight': '600'}),
                        dbc.Badge(
                            deep_dive['severity'], 
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
                                html.Small("Total Reviews", className="text-muted"),
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
                
                html.Hr(className="my-4"),
                
                # Individual Reviews Browser
                html.Div([
                    html.Div([
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
                                    value=30,
                                    clearable=False,
                                    style={'width': '100%'}
                                ),
                            ], md=3),
                        ], className="mb-3"),
                    ]),
                    html.Div(id='pm-individual-reviews-list')
                ], style={'padding': '1.5rem', 'backgroundColor': '#f8f9fa', 'borderRadius': '8px'}),
                
            ], style={'padding': '1.5rem'})
        ], style={'border': 'none', 'borderRadius': '12px'})
        
    except Exception as e:
        return dbc.Alert(f"Error loading deep dive: {str(e)}", color="danger")

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
            return dbc.Alert("Property not found.", color="warning"), None
        
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

# Send email
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
     Input('hq-aspect-selector', 'value')],
    [State('selected-property-id', 'data')]
)
def load_hq_individual_reviews(days_back, selected_aspect, property_id):
    # Check for None or empty values explicitly
    if property_id is None or selected_aspect is None or days_back is None:
        return html.Div()
    if property_id == '' or selected_aspect == '' or days_back == '':
        return html.Div()
    
    try:
        reviews = property_service.get_reviews_for_aspect(property_id, selected_aspect, days_back)
        
        if not reviews:
            return dbc.Alert("No negative reviews found for this timeframe.", color="info", className="mt-3")
        
        # Create review cards
        review_cards = []
        for review in reviews:
            # Get sentiment color
            sentiment = review.get('sentiment', 'negative')
            sentiment_color = 'danger' if sentiment == 'very_negative' else 'warning'
            
            # Format star rating
            star_rating = review.get('star_rating', 0)
            stars = '⭐' * int(star_rating)
            
            # Format evidence (array of strings)
            evidence = review.get('evidence', [])
            evidence_text = ' | '.join(evidence) if evidence else 'N/A'
            
            # Format opinion terms (array of strings)
            opinion_terms = review.get('opinion_terms', [])
            opinion_text = ', '.join(opinion_terms) if opinion_terms else 'N/A'
            
            review_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Strong(f"Review ID: {review.get('review_id', 'Unknown')}", style={'fontSize': '0.9rem'}),
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
                                html.P(opinion_text, style={'fontSize': '0.85rem', 'marginTop': '0.25rem', 'color': '#dc3545'}),
                            ], md=6),
                        ]),
                    ], style={'padding': '1rem'})
                ], className="mb-3", style={'border': '1px solid #dee2e6', 'borderRadius': '8px'})
            )
        
        return html.Div([
            html.P(f"Showing {len(reviews)} negative review(s)", className="text-muted mb-3", style={'fontSize': '0.9rem'}),
            html.Div(review_cards)
        ])
        
    except Exception as e:
        return dbc.Alert(f"Error loading reviews: {str(e)}", color="danger")

# Callback to load individual reviews for PM
@app.callback(
    Output('pm-individual-reviews-list', 'children'),
    [Input('pm-review-timeframe-selector', 'value'),
     Input('pm-aspect-selector', 'value')],
    [State('pm-property-select', 'value')]
)
def load_pm_individual_reviews(days_back, selected_aspect, property_id):
    # Check for None or empty values explicitly
    if property_id is None or selected_aspect is None or days_back is None:
        return html.Div()
    if property_id == '' or selected_aspect == '' or days_back == '':
        return html.Div()
    
    try:
        reviews = property_service.get_reviews_for_aspect(property_id, selected_aspect, days_back)
        
        if not reviews:
            return dbc.Alert("No negative reviews found for this timeframe.", color="info", className="mt-3")
        
        # Create review cards
        review_cards = []
        for review in reviews:
            # Get sentiment color
            sentiment = review.get('sentiment', 'negative')
            sentiment_color = 'danger' if sentiment == 'very_negative' else 'warning'
            
            # Format star rating
            star_rating = review.get('star_rating', 0)
            stars = '⭐' * int(star_rating)
            
            # Format evidence (array of strings)
            evidence = review.get('evidence', [])
            evidence_text = ' | '.join(evidence) if evidence else 'N/A'
            
            # Format opinion terms (array of strings)
            opinion_terms = review.get('opinion_terms', [])
            opinion_text = ', '.join(opinion_terms) if opinion_terms else 'N/A'
            
            review_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        dbc.Row([
                            dbc.Col([
                                html.Div([
                                    html.Strong(f"Review ID: {review.get('review_id', 'Unknown')}", style={'fontSize': '0.9rem'}),
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
                                html.P(opinion_text, style={'fontSize': '0.85rem', 'marginTop': '0.25rem', 'color': '#dc3545'}),
                            ], md=6),
                        ]),
                    ], style={'padding': '1rem'})
                ], className="mb-3", style={'border': '1px solid #dee2e6', 'borderRadius': '8px'})
            )
        
        return html.Div([
            html.P(f"Showing {len(reviews)} negative review(s)", className="text-muted mb-3", style={'fontSize': '0.9rem'}),
            html.Div(review_cards)
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


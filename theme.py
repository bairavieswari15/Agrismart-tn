import streamlit as st

def apply_theme():
    """Inject premium CSS styling for the AgriSmart TN app."""
    premium_css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }

    /* Top Bar & App Background */
    .stApp {
        background-color: #f8fafc;
    }
    
    [data-testid="stHeader"] {
        background-color: rgba(248, 250, 252, 0.9);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
        box-shadow: 2px 0 8px rgba(0,0,0,0.02);
    }

    /* Cards & Containers */
    div[data-testid="stMetric"] {
        background: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s, box-shadow 0.2s;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #059669, #10b981) !important;
        color: white !important;
        border-radius: 8px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        font-weight: 600 !important;
        letter-spacing: 0.025em;
        transition: all 0.2s ease-in-out;
        box-shadow: 0 4px 6px -1px rgba(16, 185, 129, 0.2) !important;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #047857, #059669) !important;
        box-shadow: 0 10px 15px -3px rgba(16, 185, 129, 0.3) !important;
        transform: translateY(-1px);
    }

    /* Primary Text */
    h1, h2, h3, h4, h5, h6 {
        color: #0f172a !important;
        font-weight: 700 !important;
    }

    /* Metric Values */
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #059669 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.9rem !important;
        font-weight: 500 !important;
        color: #64748b !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding-top: 10px;
        padding-bottom: 10px;
        padding-left: 16px;
        padding-right: 16px;
        border-radius: 8px 8px 0 0;
        background-color: #f1f5f9;
        color: #475569;
        font-weight: 600;
        border: 1px solid transparent;
    }
    .stTabs [aria-selected="true"] {
        background-color: #ffffff !important;
        color: #059669 !important;
        border-bottom: 3px solid #059669 !important;
    }

    /* Sidebar Nav Button Styles */
    [data-testid="stSidebar"] .stButton > button {
        background: #f8fafc !important;
        color: #334155 !important;
        border: 1px solid #e2e8f0 !important;
        border-radius: 10px !important;
        padding: 0.55rem 0.85rem !important;
        font-weight: 500 !important;
        text-align: left !important;
        justify-content: flex-start !important;
        box-shadow: none !important;
        width: 100% !important;
        margin-bottom: 2px !important;
    }

    [data-testid="stSidebar"] .stButton > button:hover {
        background: #f1f5f9 !important;
        color: #059669 !important;
        border-color: #059669 !important;
        transform: none !important;
    }

    /* Custom Category Badges - Use inside st.markdown */
    .badge-highly-suitable { background-color: #dcfce7; color: #166534; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .badge-suitable { background-color: #fef9c3; color: #854d0e; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .badge-moderate { background-color: #ffedd5; color: #9a3412; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    .badge-not-recommended { background-color: #fee2e2; color: #991b1b; padding: 4px 8px; border-radius: 12px; font-size: 0.8rem; font-weight: 600; display: inline-block; }
    
    /* Nav section titles */
    .sidebar-nav-header {
        font-size: 0.75rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #64748b;
        margin-top: 14px;
        margin-bottom: 6px;
    }
    
    /* Hide Streamlit Branding */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    </style>
    """
    st.markdown(premium_css, unsafe_allow_html=True)

apply_custom_theme = apply_theme


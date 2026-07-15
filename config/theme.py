import streamlit as st


# Color palette
BG_COLOR = "#0f0f14"
CARD_COLOR = "#1a1a24"
CARD_BORDER = "#2a2a3a"
ACCENT = "#6366f1"
ACCENT_HOVER = "#818cf8"
TEXT_PRIMARY = "#e4e4e7"
TEXT_SECONDARY = "#71717a"
TEXT_MUTED = "#52525b"
SUCCESS = "#22c55e"
WARNING = "#f59e0b"
ERROR = "#ef4444"
RUNNING = "#3b82f6"

AGENT_COLORS = {
    "coordinator": "#8b5cf6",
    "researcher": "#3b82f6",
    "analyst": "#f59e0b",
    "planner": "#22c55e",
}


def apply_theme():
    st.markdown(
        f"""
    <style>
        /* Main background */
        .stApp {{
            background-color: {BG_COLOR};
        }}

        /* Text colors */
        .stApp, .stMarkdown, .stText {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* Sidebar */
        section[data-testid="stSidebar"] {{
            background-color: {CARD_COLOR};
        }}

        /* Cards and containers */
        div[data-testid="stVerticalBlock"] > div {{
            background: transparent;
        }}

        .element-container {{
            background: transparent;
        }}

        /* Metric styling */
        div[data-testid="stMetric"] {{
            background-color: {CARD_COLOR};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
            padding: 12px 16px;
        }}
        div[data-testid="stMetric"] label {{
            color: {TEXT_SECONDARY} !important;
        }}
        div[data-testid="stMetric"] div {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* Expander */
        div[data-testid="stExpander"] {{
            background-color: {CARD_COLOR};
            border: 1px solid {CARD_BORDER};
            border-radius: 12px;
        }}

        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            background-color: {CARD_COLOR};
            border-radius: 12px;
            padding: 4px;
            gap: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px;
            color: {TEXT_SECONDARY};
        }}
        .stTabs [aria-selected="true"] {{
            background-color: {ACCENT} !important;
            color: white !important;
        }}

        /* Buttons */
        .stButton button {{
            background-color: {ACCENT};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 8px 24px;
            font-weight: 600;
        }}
        .stButton button:hover {{
            background-color: {ACCENT_HOVER};
            color: white;
        }}

        /* Input fields */
        div[data-testid="stTextInput"] input,
        div[data-testid="stDateInput"] input,
        div[data-testid="stNumberInput"] input,
        div[data-testid="stTextArea"] textarea,
        div[data-testid="stSelectbox"] div {{
            background-color: {CARD_COLOR} !important;
            border: 1px solid {CARD_BORDER} !important;
            border-radius: 8px !important;
            color: {TEXT_PRIMARY} !important;
        }}

        /* Info/Success/Warning/Error boxes */
        div[data-testid="stAlert"] {{
            border-radius: 12px;
        }}

        /* Dividers */
        hr {{
            border-color: {CARD_BORDER};
            margin: 24px 0;
        }}

        /* Code blocks */
        code {{
            background-color: {CARD_COLOR} !important;
            color: {ACCENT} !important;
        }}

        /* Headers */
        h1, h2, h3, h4 {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* Select slider */
        div[data-testid="stSlider"] div {{
            color: {TEXT_PRIMARY} !important;
        }}

        /* Multi select */
        div[data-baseweb="tag"] {{
            background-color: {ACCENT} !important;
        }}

        /* Spinner text */
        .stSpinner {{
            color: {TEXT_SECONDARY} !important;
        }}

        /* Plotly chart background */
        .js-plotly-plot .plotly, .js-plotly-plot .plotly .main-svg {{
            background: transparent !important;
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

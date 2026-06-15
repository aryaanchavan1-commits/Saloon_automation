PAGE_CONFIG = {
    "page_title": "Saloon Pro",
    "page_icon": "💈",
    "layout": "wide",
    "initial_sidebar_state": "collapsed"
}

CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; box-sizing: border-box; }
    html, body, .stApp { margin: 0; padding: 0; overflow-x: hidden; }

    .stApp {
        background: #0a0a0f;
        background-image:
            radial-gradient(ellipse at 20% 0%, rgba(120,80,255,0.06) 0%, transparent 60%),
            radial-gradient(ellipse at 80% 100%, rgba(255,50,100,0.04) 0%, transparent 50%);
    }

    #MainMenu, footer, header, div[data-testid="stToolbar"],
    div[data-testid="stDecoration"], div[data-testid="stStatusWidget"],
    section[data-testid="stSidebar"], div[data-testid="collapsedControl"] {
        display: none !important;
    }
    .stApp > header { display: none !important; }
    .appview-container .main .block-container {
        padding: 0 !important; max-width: 100% !important;
    }
    .main > div:first-child { padding-top: 0 !important; }

    .app-topbar {
        position: fixed; top: 0; left: 0; right: 0; z-index: 999;
        background: linear-gradient(135deg, #1a1a2e, #16213e);
        border-bottom: 1px solid rgba(255,255,255,0.06);
        padding: 0.6rem 1rem; height: 52px;
        display: flex; align-items: center; justify-content: space-between;
        backdrop-filter: blur(20px);
    }
    .app-topbar .app-title {
        font-size: 1.1rem; font-weight: 800;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        display: flex; align-items: center; gap: 0.4rem;
    }
    .app-topbar .app-user {
        font-size: 0.75rem; color: rgba(255,255,255,0.4);
        display: flex; align-items: center; gap: 0.5rem;
    }
    .app-topbar .app-user .role-badge {
        background: rgba(192,132,252,0.15);
        color: #c084fc; padding: 0.15rem 0.5rem;
        border-radius: 20px; font-size: 0.65rem; font-weight: 600;
    }
    .app-topbar .signout-btn {
        background: rgba(255,255,255,0.06);
        border: 1px solid rgba(255,255,255,0.1);
        color: rgba(255,255,255,0.5); cursor: pointer;
        border-radius: 10px; padding: 0.3rem 0.6rem;
        font-size: 0.75rem; transition: all 0.2s;
        text-decoration: none; display: inline-block; line-height: 1.2;
    }
    .app-topbar .signout-btn:hover { background: rgba(248,113,113,0.2); color: #f87171; }

    .app-content {
        padding: 60px 0.75rem 72px 0.75rem; min-height: 100vh;
    }

    .page-title {
        font-size: 1.25rem; font-weight: 800; color: #fff;
        margin: 0.5rem 0 0.15rem 0;
    }
    .page-subtitle {
        font-size: 0.75rem; color: rgba(255,255,255,0.35);
        margin: 0 0 1rem 0;
    }

    .bottom-nav {
        position: fixed; bottom: 0; left: 0; right: 0; z-index: 999;
        background: rgba(16,16,24,0.98);
        backdrop-filter: blur(20px);
        border-top: 1px solid rgba(255,255,255,0.06);
        display: flex; justify-content: space-around;
        align-items: stretch; height: 64px;
        padding: 0; padding-bottom: env(safe-area-inset-bottom, 0);
    }

    .metric-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.05), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.08);
        border-radius: 14px; padding: 1rem 0.75rem;
        text-align: center; backdrop-filter: blur(10px);
        animation: fadeIn 0.3s ease-out;
        transition: transform 0.2s, box-shadow 0.2s;
        height: 100%;
    }
    .metric-card:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,0.2); }
    .metric-card .icon { font-size: 1.5rem; margin-bottom: 0.25rem; }
    .metric-card .value {
        font-size: 1.3rem; font-weight: 800;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        line-height: 1.3;
    }
    .metric-card .label {
        font-size: 0.65rem; color: rgba(255,255,255,0.4);
        text-transform: uppercase; letter-spacing: 0.5px;
        font-weight: 600;
    }

    .glass-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01));
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px; padding: 1rem;
        backdrop-filter: blur(10px);
        animation: fadeIn 0.3s ease-out;
        transition: box-shadow 0.2s;
        margin-bottom: 0.75rem;
    }
    .glass-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.15); }
    .glass-card h3 {
        font-size: 0.9rem; font-weight: 700; color: rgba(255,255,255,0.9);
        margin: 0 0 0.75rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid rgba(255,255,255,0.05);
    }
    .glass-card h4 {
        font-size: 0.8rem; font-weight: 700; color: rgba(255,255,255,0.8);
        margin: 0 0 0.5rem 0;
    }

    .auth-screen {
        display: flex; justify-content: center; align-items: center;
        min-height: 100vh; padding: 1.5rem;
        background: #0a0a0f;
        background-image:
            radial-gradient(ellipse at 50% 0%, rgba(120,80,255,0.08) 0%, transparent 60%),
            radial-gradient(ellipse at 50% 100%, rgba(255,50,100,0.05) 0%, transparent 50%);
    }
    .auth-card {
        background: linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 20px; padding: 2rem 1.5rem;
        width: 100%; max-width: 400px;
        backdrop-filter: blur(20px);
    }
    .auth-header { text-align: center; margin-bottom: 1.5rem; }
    .auth-header .logo-icon { font-size: 2.5rem; }
    .auth-header h1 {
        font-size: 1.8rem; font-weight: 800;
        background: linear-gradient(135deg, #c084fc, #f472b6);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        margin: 0.25rem 0 0.1rem;
    }
    .auth-header p { color: rgba(255,255,255,0.35); font-size: 0.8rem; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem; background: rgba(255,255,255,0.03);
        border-radius: 10px; padding: 0.2rem;
        border: 1px solid rgba(255,255,255,0.04);
        flex-wrap: nowrap; overflow-x: auto;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px; padding: 0.3rem 0.6rem;
        font-weight: 600; font-size: 0.72rem;
        color: rgba(255,255,255,0.4); white-space: nowrap;
        transition: all 0.2s; min-height: 36px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(192,132,252,0.2), rgba(244,114,182,0.2));
        color: #fff !important;
    }

    .stButton > button {
        background: linear-gradient(135deg, #c084fc, #f472b6);
        border: none; color: white; font-weight: 700;
        border-radius: 12px; padding: 0.5rem 1rem;
        font-size: 0.85rem; min-height: 44px;
        transition: all 0.2s;
        box-shadow: 0 4px 16px rgba(192,132,252,0.15);
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 24px rgba(192,132,252,0.25);
    }
    .stButton > button:active { transform: translateY(0) scale(0.98); }

    .stTextInput > div > div, .stSelectbox > div > div,
    .stNumberInput > div > div, .stTextArea > div > div {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important; color: white !important;
        min-height: 44px !important; font-size: 0.85rem !important;
        transition: border-color 0.2s, box-shadow 0.2s !important;
    }
    .stTextInput > div > div:focus-within,
    .stSelectbox > div > div:focus-within,
    .stNumberInput > div > div:focus-within {
        border-color: #c084fc !important;
        box-shadow: 0 0 0 3px rgba(192,132,252,0.15) !important;
    }
    .stTextArea textarea { min-height: 80px !important; }

    .stDataFrame {
        background: rgba(255,255,255,0.02) !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255,255,255,0.04) !important;
        font-size: 0.75rem !important;
    }
    .stDataFrame [data-testid="StyledDataFrameDataCell"] {
        font-size: 0.72rem !important; padding: 0.3rem 0.5rem !important;
    }

    .stAlert {
        background: rgba(255,255,255,0.03) !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 10px !important; font-size: 0.8rem !important;
    }

    .stExpander {
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 10px; margin-bottom: 0.5rem;
    }

    .more-grid {
        display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem;
        padding: 0.5rem 0;
    }

    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(8px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .desktop-nav, .desktop-nav-inner, .desktop-nav-logo, .desktop-nav-links,
    .desktop-nav-user, .desktop-nav-extra { display: none; }

    @media (min-width: 768px) {
        .app-content { max-width: 480px; margin: 0 auto; padding: 60px 0 72px 0; }
        .bottom-nav { max-width: 480px; left: 50%; transform: translateX(-50%); border-radius: 16px 16px 0 0; }
        .app-topbar { max-width: 480px; left: 50%; transform: translateX(-50%); border-radius: 0 0 12px 12px; }
    }

    @media (min-width: 1024px) {
        .app-topbar { display: none !important; }
        .bottom-nav { display: none !important; }

        .desktop-nav { display: block; position: fixed; top: 0; left: 0; right: 0; z-index: 999; background: linear-gradient(135deg, #12121a, #1a1a2e); border-bottom: 1px solid rgba(255,255,255,0.06); backdrop-filter: blur(20px); }
        .desktop-nav-inner { display: flex; align-items: center; max-width: 1400px; margin: 0 auto; padding: 0 1.5rem; height: 52px; gap: 0.25rem; }
        .desktop-nav-logo { font-size: 1rem; font-weight: 800; background: linear-gradient(135deg, #c084fc, #f472b6); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin-right: 1rem; white-space: nowrap; display: flex; align-items: center; gap: 0.3rem; }
        .desktop-nav-links { display: flex; align-items: center; gap: 0; flex: 1; }
        .desktop-nav-user { font-size: 0.7rem; color: rgba(255,255,255,0.35); white-space: nowrap; margin: 0 0.5rem; }
        .desktop-nav-user .role-badge { background: rgba(192,132,252,0.12); color: #c084fc; padding: 0.05rem 0.35rem; border-radius: 20px; font-size: 0.55rem; font-weight: 600; }
        .desktop-nav-extra { display: flex; align-items: center; gap: 0; }

        .desktop-nav .stButton > button {
            background: transparent !important; border: none !important;
            box-shadow: none !important; color: rgba(255,255,255,0.5) !important;
            font-size: 1.1rem !important; padding: 0.25rem 0.5rem !important;
            min-height: 36px !important; border-radius: 8px !important;
            transition: all 0.15s !important;
        }
        .desktop-nav .stButton > button:hover {
            background: rgba(255,255,255,0.06) !important; color: #fff !important;
        }
        .desktop-nav .stButton > button:active, .desktop-nav .stButton > button:focus {
            color: #c084fc !important; border: none !important; outline: none !important;
        }
        .desktop-nav .stButton { margin: 0 !important; }
        .desktop-nav-extra .stButton > button {
            font-size: 1rem !important; padding: 0.25rem 0.4rem !important;
            color: rgba(255,255,255,0.35) !important;
        }
        .desktop-nav-extra .stButton > button:hover { color: #c084fc !important; }

        .app-content {
            max-width: none !important; padding: 68px 2rem 2rem !important;
            margin: 0 !important; min-height: 100vh;
        }
        .app-content .block-container { max-width: 1200px; margin: 0 auto; }

        .stTabs [data-baseweb="tab-list"] { flex-wrap: wrap; }
    }

    .bottom-nav .stButton > button {
        background: transparent !important; border: none !important;
        box-shadow: none !important; font-size: 1.2rem !important;
        padding: 0.2rem 0 !important; min-height: 44px !important;
        border-radius: 0 !important; color: rgba(255,255,255,0.5) !important;
        line-height: 1.15 !important; white-space: pre-line !important;
        transition: all 0.15s !important;
    }
    .bottom-nav .stButton > button:hover {
        color: rgba(255,255,255,0.8) !important; background: transparent !important;
    }
    .bottom-nav .stButton > button:active, .bottom-nav .stButton > button:focus {
        color: #c084fc !important; background: transparent !important;
        border: none !important; outline: none !important;
    }
    .bottom-nav .stButton { margin: 0 !important; }

    .more-grid-btns .stButton > button {
        background: linear-gradient(135deg, rgba(255,255,255,0.04), rgba(255,255,255,0.01)) !important;
        border: 1px solid rgba(255,255,255,0.06) !important; border-radius: 14px !important;
        padding: 1.2rem 0.5rem !important; text-align: center !important;
        min-height: 80px !important; height: 100% !important;
        font-size: 0.75rem !important; font-weight: 600 !important;
        color: rgba(255,255,255,0.6) !important; line-height: 1.4 !important;
        white-space: pre-line !important; transition: all 0.15s !important;
        box-shadow: none !important;
    }
    .more-grid-btns .stButton > button:hover {
        background: rgba(192,132,252,0.08) !important;
        border-color: rgba(192,132,252,0.2) !important; color: #fff !important;
        transform: translateY(-1px);
    }
    .more-grid-btns .stButton { margin: 0 0 0.6rem 0 !important; }

    ::-webkit-scrollbar { width: 0; height: 0; }

    @media print {
        .app-topbar, .bottom-nav, .desktop-nav { display: none !important; }
        .app-content { padding: 0 !important; }
    }
</style>
"""

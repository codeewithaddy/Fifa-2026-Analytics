"""
app.py — FIFA World Cup 2026 Companion Stats Hub
Main entry point setting up clean sidebar navigation and routing.
"""

import streamlit as st

# ── Clean Professional Multi-Page Navigation ─────────────────
pg = st.navigation({
    "Tournament Centre": [
        st.Page("pages/0_Home.py", title="Live Match Centre", icon="⚽", default=True),
        st.Page("pages/3_Golden_Boot.py", title="Goal Projections", icon="📈"),
    ],
    "Analytics Room": [
        st.Page("pages/1_xG_Engine.py", title="Shooting Analysis", icon="🎯"),
        st.Page("pages/2_Player_Scout.py", title="Player Comparison", icon="⚔️"),
        st.Page("pages/4_Team_DNA.py", title="Team Performance", icon="🌍"),
    ]
})

# Run the selected page
pg.run()

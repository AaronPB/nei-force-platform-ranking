import streamlit as st
from streamlit_carousel import carousel
import pandas as pd

from src.managers import DataManager

# Define image sliders
# TODO Add proper sliders
sliders = [
    dict(title="", text="", img="images/nei_almeria_2024.jpg"),
    dict(title="", text="", img="images/force_platform_logo.png"),
]


def ranking():
    # Managers
    if "data_mngr" not in st.session_state:
        st.session_state.data_mngr = DataManager()

    carousel(items=sliders, controls=False, container_height=200)
    st.header(":material/social_leaderboard: Ranking del TOP 20")
    st.write("¡Las 20 personas con mejor equilibrio al cerrar los ojos!")

    df = st.session_state.data_mngr.getScoreboard()

    if not df.empty:
        st.dataframe(
            data=df,
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre"),
                "cop": st.column_config.AreaChartColumn(
                    "Trayectoria del centro de presiones", y_min=-30, y_max=30
                ),
                "area": st.column_config.NumberColumn(
                    "Área elipse (cm2)", format="%.2f"
                ),
                "score": st.column_config.NumberColumn("Puntuación", format="%d"),
            },
            height=740,
        )

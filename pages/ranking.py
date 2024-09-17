import streamlit as st
from streamlit_carousel import carousel
import pandas as pd

from src.managers import DataManager
from pages import level_normal, level_hard

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

    df = st.session_state.data_mngr.getScoreboard()

    col1, col2 = st.columns(2)

    col1.header(
        ":material/social_leaderboard: Modo carretera", divider="green", anchor=False
    )
    col2.header(
        ":material/social_leaderboard: Modo derrapes", divider="red", anchor=False
    )
    col1.markdown(
        """
        - Previsión del camino aleatorio
        - 10 cambios de dirección en 20s
        """
    )
    col2.markdown(
        """
        - Camino aleatorio desconocido
        - 20 cambios de dirección en 20s
        """
    )

    btn_level_normal = col1.button(
        label="Iniciar desafío",
        key="btn_test_normal",
        type="primary",
        use_container_width=True,
    )
    btn_level_hard = col2.button(
        label="Iniciar desafío",
        key="btn_test_hard",
        type="primary",
        use_container_width=True,
    )
    if btn_level_normal:
        st.switch_page(st.Page(level_normal.level_normal))
    if btn_level_hard:
        st.switch_page(st.Page(level_hard.level_hard))

    if not df.empty:
        col1.dataframe(
            data=df.iloc[0:10, :],
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre"),
                "cop": st.column_config.AreaChartColumn(
                    "Trayectoria", y_min=-30, y_max=30
                ),
                "area": st.column_config.NumberColumn("Área (cm2)", format="%.2f"),
                "score": st.column_config.NumberColumn("Puntuación", format="%d"),
            },
            height=740,
        )
        col2.dataframe(
            data=df.iloc[10:20, :],
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre"),
                "cop": st.column_config.AreaChartColumn(
                    "Trayectoria", y_min=-30, y_max=30
                ),
                "area": st.column_config.NumberColumn("Área (cm2)", format="%.2f"),
                "score": st.column_config.NumberColumn("Puntuación", format="%d"),
            },
            height=740,
        )

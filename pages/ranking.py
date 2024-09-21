import streamlit as st
from streamlit_carousel import carousel
import yaml

from src.managers import DataManager
from pages import level_normal, level_hard

# Define image sliders
sliders = [
    dict(title="", text="", img="images/nei_almeria_2024.jpg"),
    dict(title="", text="", img="images/slider1.jpg"),
    dict(title="", text="", img="images/slider2.jpg"),
    dict(title="", text="", img="images/slider3.jpg"),
    dict(title="", text="", img="images/slider4.jpg"),
]


def ranking():
    # Load data and achievement managers
    if "data_mngr" not in st.session_state:
        st.session_state.data_mngr = DataManager()
    if "achievements" not in st.session_state:
        with open("files/achievements.yaml", "r", encoding="utf-8") as file:
            st.session_state.achievements = yaml.safe_load(file)
    if "inverted_mode" not in st.session_state:
        st.session_state.inverted_mode = False

    carousel(items=sliders, controls=False, container_height=200, interval=4000)

    col1, col2 = st.columns(2)

    col1.header(
        ":material/directions_car: Modo carretera", divider="green", anchor=False
    )
    col2.header(":material/car_crash: Modo derrapes", divider="red", anchor=False)
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
    btn_level_normal_inverted = col1.button(
        label="Iniciar desafío **espejo**",
        key="btn_test_normal_inverted",
        type="primary",
        use_container_width=True,
    )
    btn_level_hard_inverted = col2.button(
        label="Iniciar desafío **espejo**",
        key="btn_test_hard_inverted",
        type="primary",
        use_container_width=True,
    )
    if btn_level_normal:
        st.session_state.inverted_mode = False
        st.switch_page(st.Page(level_normal.level_normal))
    if btn_level_hard:
        st.session_state.inverted_mode = False
        st.switch_page(st.Page(level_hard.level_hard))
    if btn_level_normal_inverted:
        st.session_state.inverted_mode = True
        st.switch_page(st.Page(level_normal.level_normal))
    if btn_level_hard_inverted:
        st.session_state.inverted_mode = True
        st.switch_page(st.Page(level_hard.level_hard))

    df_normal = st.session_state.data_mngr.getScoreboardNormal()
    df_hard = st.session_state.data_mngr.getScoreboardHard()

    if not df_normal.empty:
        col1.write(
            f":material/social_leaderboard: **TOP-15** de {len(df_normal)} participantes"
        )
        col1.dataframe(
            data=df_normal.iloc[0:15, :],
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre participante"),
                "score": st.column_config.NumberColumn("Puntos", format="%d"),
            },
            height=565,
        )
    if not df_hard.empty:
        col2.write(
            f":material/social_leaderboard: **TOP-15** de {len(df_hard)} participantes"
        )
        col2.dataframe(
            data=df_hard.iloc[0:15, :],
            use_container_width=True,
            column_config={
                "name": st.column_config.TextColumn("Nombre participante"),
                "score": st.column_config.NumberColumn("Puntos", format="%d"),
            },
            height=565,
        )

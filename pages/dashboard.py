import streamlit as st
import pandas as pd
import yaml
import time

from pages import ranking

from loguru import logger


def loadAchievementsFile(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data


achievements = loadAchievementsFile("files/achievements.yaml")
achievement_top = achievements["achievement_top"]
achievement_area = achievements["achievement_area"]
achievement_area_percentage = achievements["achievement_area_percentage"]


def getAchievements(position: int, total: int, area: float) -> dict:
    achievements = {}
    percentage = position / total * 100

    # Check achievements for position
    for key in sorted(achievement_top.keys()):
        if position <= key:
            achievements["position"] = achievement_top[key]
            break

    # If not in TOP20, check achievements for percentage
    if not achievements:
        for key in sorted(achievement_area_percentage.keys()):
            if percentage <= key:
                achievements["percentage"] = achievement_area_percentage[key]
                break

    # Check achievements for area
    for key in sorted(achievement_area.keys()):
        if key <= area < key + 1:
            achievements["area"] = achievement_area[key]
            break

    return achievements


def getData() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Nombre": "Prueba",
            "Area": 1.2,
            "Puntuación": 700,
        },
        index=["1"],
    )


def dashboard():
    # Session variables
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "results" not in st.session_state:
        st.session_state.results = pd.DataFrame()

    # Page
    if st.session_state.get("btn_save", False):
        # TODO Merge data to ranked dataframe and backup csv file.
        # Reset states
        st.session_state.recording = False
        st.session_state.results = pd.DataFrame()
        # Switch to ranking page
        st.switch_page(st.Page(ranking.ranking))

    if st.session_state.get("btn_rec_start", False):
        st.session_state.recording = True
    elif st.session_state.get("btn_rec_cancel", False):
        st.session_state.recording = False
        st.session_state.results = pd.DataFrame()

    logger.debug(st.session_state.recording)
    logger.debug(st.session_state.results.empty)

    # Show results instead of recording button
    if st.session_state.recording and not st.session_state.results.empty:
        st.header("Resultados")
        # TODO Check results to load multiple achievements
        # TODO change vars to actual data
        position = 670
        total = 893
        area = 5.32
        metric_col1, metric_col2 = st.columns(2)
        metric_col1.metric(
            "Posición ranking", f"Puesto nº {position}", f"De {total} personas", "off"
        )
        metric_col2.metric("Área total trayectoria", f"{area} cm2")

        achievements = getAchievements(position, total, area)
        if achievements:
            for achievement in achievements.values():
                st.warning(achievement[0], icon=achievement[1])
            st.balloons()
        else:
            st.snow()

        col1, col2 = st.columns(2)
        col1.button(
            label="Guardar", key="btn_save", type="primary", use_container_width=True
        )
        col2.button(label="Cancelar", key="btn_rec_cancel", use_container_width=True)

        st.header("Trayectorias del centro de presión")
        # TODO Build COP graphs with plotly
        return

    if not st.session_state.recording and st.session_state.results.empty:
        st.info("Colócate en las plataformas", icon=":material/settings_accessibility:")

    _, countdown_col, _ = st.columns([2, 0.5, 2])
    countdown = countdown_col.empty()

    btn_record_start = st.button(
        label="Iniciar prueba",
        key="btn_rec_start",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.recording,
    )

    if btn_record_start:
        with st.status("Iniciando grabación...") as status:
            # TODO Connect sensors
            for i in range(3, 0, -1):
                countdown.metric("Iniciando", i)
                time.sleep(1)
            status.update(label="Grabando...")
            for i in range(100, -1, -1):
                seconds = i / 10
                formatted_time = f"{int(seconds):02}.{int(i % 10)}"
                countdown.metric("¡Grabando!", formatted_time)
                # TODO Record from sensors
                time.sleep(0.1)
        countdown.empty()
        status.update(label="Calculando...", state="running")
        # TODO Get here results and build dataframe.
        st.session_state.results = getData()
        time.sleep(3)
        status.update(label="¡Completado!", state="complete")
        st.switch_page(st.Page(dashboard))

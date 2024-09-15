import streamlit as st
import pandas as pd
import yaml
import time
import random

from src.handlers import SensorGroup

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


def recordPlatforms(countdown):
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


def recordDemo(countdown):
    with st.status("Iniciando grabación...") as status:
        for i in range(3, 0, -1):
            countdown.metric("Iniciando", i)
            time.sleep(1)
        status.update(label="Grabando...")
        for i in range(40, -1, -1):
            seconds = i / 10
            formatted_time = f"{int(seconds):02}.{int(i % 10)}"
            countdown.metric("¡Grabando!", formatted_time)
            time.sleep(0.1)
    countdown.empty()
    status.update(label="¡Completado! Preparando resultados...", state="complete")
    # Generate demo data
    sensor_groups: list[SensorGroup] = st.session_state.sensor_mngr.getGroups()
    for group in sensor_groups:
        for sensor in group.getSensors().values():
            # Just for test purposes.
            # This simulated data is not correct because force variations affects other sensor measures.
            if "Z" in sensor.getName():
                sensor.values = [
                    round(random.uniform(1.14e-04, 9.65e-05), 5) for _ in range(100)
                ]
            else:
                sensor.values = [
                    round(random.uniform(8.58e-05, 2.14e-05), 5) for _ in range(100)
                ]


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
    # Dashboard variables
    if "recording" not in st.session_state:
        st.session_state.recording = False
    if "results" not in st.session_state:
        st.session_state.results = {}
    if "get_balloons" not in st.session_state:
        st.session_state.get_balloons = False

    # Page
    if st.session_state.get("btn_save", False):
        # Merge data to ranked dataframe and backup csv file.
        st.session_state.data_mngr.updateScoreboard(
            st.session_state.results["dataframe"]
        )
        # Reset states
        st.session_state.recording = False
        # Switch to ranking page
        st.switch_page(st.Page(ranking.ranking))

    if st.session_state.get("btn_rec_start", False):
        st.session_state.recording = True
    elif st.session_state.get("btn_rec_cancel", False):
        st.session_state.recording = False

    logger.debug(st.session_state.recording)
    logger.debug(st.session_state.results)

    # Show results instead of recording button
    if st.session_state.recording and st.session_state.results:
        st.header("Resultados")
        position = st.session_state.results["position"]
        total = st.session_state.results["total"]
        area = st.session_state.results["area"]
        score = st.session_state.results["score"]
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric(
            "Posición ranking", f"Puesto nº {position}", f"De {total} personas", "off"
        )
        metric_col2.metric("Área total trayectoria", f"{area:.2f} cm2")
        metric_col3.metric("Puntuación", f"{round(score):d}", f"Máximo 1000", "off")

        achievements = getAchievements(position, total, area)
        if achievements:
            for achievement in achievements.values():
                st.warning(achievement[0], icon=achievement[1])
        if not st.session_state.get_balloons:
            st.balloons()
            st.session_state.get_balloons = True

        # Build COP graphs with plotly
        st.plotly_chart(st.session_state.data_mngr.getFigure())

        # Save options
        df_editor = st.data_editor(
            data=pd.DataFrame(
                {
                    "name": "Tu nombre",
                    "cop": [st.session_state.results["cop"]],
                    "area": area,
                    "score": score,
                }
            ),
            use_container_width=True,
            disabled=("cop", "area", "score"),
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
            hide_index=True,
        )
        if df_editor is not None:
            st.session_state.results["dataframe"] = df_editor
        col1, col2 = st.columns(2)
        col1.button(
            label="Guardar", key="btn_save", type="primary", use_container_width=True
        )
        col2.button(label="Cancelar", key="btn_rec_cancel", use_container_width=True)
        return

    st.session_state.results = {}
    st.session_state.get_balloons = False

    if not st.session_state.recording:
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

    btn_return = st.button(
        label="Volver",
        use_container_width=True,
    )
    if btn_return:
        st.switch_page(st.Page(ranking.ranking))

    if btn_record_start:
        if (
            not st.session_state.demo_enabled
            and not st.session_state.test_mngr.getSensorConnected()
        ):
            logger.warning("No platforms connected!")
            st.session_state.recording = False
            st.switch_page(st.Page(dashboard))
            return
        if not st.session_state.demo_enabled:
            logger.info("Starting platform record!")
            recordPlatforms(countdown)
        else:
            logger.info("Starting demo!")
            recordDemo(countdown)
        # Get COP and area values
        st.session_state.data_mngr.loadData(st.session_state.sensor_mngr.getGroups())
        # TODO Save data in results
        st.session_state.results = st.session_state.data_mngr.getResults()
        st.switch_page(st.Page(dashboard))

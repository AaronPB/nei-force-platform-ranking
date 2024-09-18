import streamlit as st
import time
import yaml

from pages import ranking

from loguru import logger


def loadAchievementsFile(filepath: str) -> dict:
    with open(filepath, "r", encoding="utf-8") as file:
        data = yaml.safe_load(file)
    return data


achievements = loadAchievementsFile("files/achievements.yaml")
achievement_top = achievements["achievement_top"]
achievement_percentage = achievements["achievement_percentage"]


def getAchievements(position: int, total: int) -> dict:
    achievements = {}
    percentage = position / total * 100

    # Check achievements for position
    for key in sorted(achievement_top.keys()):
        if position <= key:
            achievements["position"] = achievement_top[key]
            break

    # If not in TOP20, check achievements for percentage
    if not achievements:
        for key in sorted(achievement_percentage.keys()):
            if percentage <= key:
                achievements["percentage"] = achievement_percentage[key]
                break

    return achievements


def startTest(test_info, figure):
    pass


def startDemo(test_info, figure, fps, path_length, start_length, finish_length):
    sleep_time = 1 / fps
    with st.spinner("Ejecutando prueba"):
        test_info.title("Quédate en el centro")
        for i in range(start_length):
            figure.plotly_chart(st.session_state.data_mngr.getDemoFramedFigure(i))
            time.sleep(sleep_time)
        test_info.title("¡Sigue el camino!")
        for i in range(path_length):
            figure.plotly_chart(
                st.session_state.data_mngr.getDemoFramedFigure(i + start_length)
            )
            time.sleep(sleep_time)
        test_info.title("¡Completado!")
        for i in range(finish_length - fps):
            figure.plotly_chart(
                st.session_state.data_mngr.getDemoFramedFigure(
                    i + start_length + path_length
                )
            )
            time.sleep(sleep_time)


def level_normal():
    if "level_recorded" not in st.session_state:
        st.session_state.level_recorded = False
    if "get_balloons" not in st.session_state:
        st.session_state.get_balloons = False

    if st.session_state.get("btn_save", False):
        # Merge data to ranked dataframe and backup csv file.
        # st.session_state.data_mngr.updateScoreboard(
        #     st.session_state.results["dataframe"]
        # )
        # Reset states
        st.session_state.level_recorded = False
        # Switch to ranking page
        st.switch_page(st.Page(ranking.ranking))
    elif st.session_state.get("btn_rec_cancel", False):
        st.session_state.level_recorded = False

    st.header(":material/directions_car: Modo carretera", divider="green", anchor=False)

    test_info = st.empty()
    figure = st.empty()
    test_btns = st.empty()

    if st.session_state.level_recorded:
        # Results and achievements
        results = st.session_state.data_mngr.getResultsNormal()
        score = results["score"]
        position = results["position"]
        total = results["total"]
        metric_col1, metric_col2, metric_col3 = st.columns([0.3, 0.2, 0.5])
        metric_col1.metric(
            "Posición ranking", f"Nº {position}", f"De {total} personas", "off"
        )
        # metric_col2.metric("Área total trayectoria", f"{area:.2f} cm2")
        metric_col2.metric("Puntuación", f"{round(score):d}", f"De 1000", "off")

        achievements = getAchievements(position, total)
        if achievements:
            for achievement in achievements.values():
                metric_col3.warning(achievement[0], icon=achievement[1])
        if not st.session_state.get_balloons:
            st.balloons()
            st.session_state.get_balloons = True
        st.plotly_chart(st.session_state.data_mngr.getCompleteFigure())
        col1, col2 = st.columns(2)
        col1.button(
            label="Guardar", key="btn_save", type="primary", use_container_width=True
        )
        col2.button(label="Cancelar", key="btn_rec_cancel", use_container_width=True)
        return

    btn_col1, btn_col2, btn_col3 = test_btns.columns(3)
    btn_start = btn_col1.button(
        label="Iniciar prueba",
        key="btn_start_test",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.demo_enabled
        and not st.session_state.platforms_connected,
    )
    btn_col2.button("Regenerar", use_container_width=True)
    btn_return = btn_col3.button(
        label="Volver",
        use_container_width=True,
    )

    if btn_return:
        st.switch_page(st.Page(ranking.ranking))

    # Build road path
    path_objectives = 10
    fps = 20
    duration_secs = 20
    initial_secs = 5
    final_secs = 3
    path_length = int(duration_secs * fps)
    start_length = int(initial_secs * fps)
    finish_length = int(final_secs * fps)
    if not btn_start:
        st.session_state.data_mngr.createPath(
            path_objectives, path_length, start_length, finish_length
        )

    figure.plotly_chart(st.session_state.data_mngr.getCompleteFigure())

    if btn_start:
        if (
            not st.session_state.demo_enabled
            and not st.session_state.platforms_connected
        ):
            logger.warning("No platforms connected!")
            st.session_state.recording = False
            st.switch_page(st.Page(level_normal))
            return
        test_btns.empty()
        if not st.session_state.demo_enabled:
            logger.info("Starting platform record!")
            startTest(test_info, figure)
        else:
            logger.info("Starting demo!")
            startDemo(test_info, figure, fps, path_length, start_length, finish_length)

        test_info.empty()
        st.session_state.level_recorded = True
        st.switch_page(st.Page(level_normal))

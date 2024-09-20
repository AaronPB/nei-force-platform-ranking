import streamlit as st
import time
import random

from pages import ranking

from loguru import logger


def getAchievements(position: int, total: int) -> dict:
    achievements = {}
    percentage = position / total * 100

    # Check achievements for position
    for key in sorted(st.session_state.achievements["achievement_top"].keys()):
        if position <= key:
            achievements["position"] = st.session_state.achievements["achievement_top"][
                key
            ]
            break

    # If not in TOP20, check achievements for percentage
    if not achievements:
        for key in sorted(
            st.session_state.achievements["achievement_percentage"].keys()
        ):
            if percentage <= key:
                achievements["percentage"] = st.session_state.achievements[
                    "achievement_percentage"
                ][key]
                break

    return achievements


def startTest(test_info, figure, fps, path_length, start_length, finish_length):
    sleep_time = 1 / fps
    if st.session_state.inverted_mode:
        st.session_state.data_mngr.setupSensorGroups(
            st.session_state.sensor_mngr.getGroup("platform_2"),
            st.session_state.sensor_mngr.getGroup("platform_1"),
            False,
        )
    else:
        st.session_state.data_mngr.setupSensorGroups(
            st.session_state.sensor_mngr.getGroup("platform_1"),
            st.session_state.sensor_mngr.getGroup("platform_2"),
            False,
        )
    st.session_state.test_mngr.testStart()
    with st.spinner("Ejecutando prueba"):
        test_info.title("Quédate en el centro")
        for i in range(start_length):
            st.session_state.test_mngr.testRegisterValues()
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(i))
            time.sleep(sleep_time)
        test_info.title("¡Sigue el camino!")
        for i in range(path_length):
            idx = i + start_length
            st.session_state.test_mngr.testRegisterValues()
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(idx))
            time.sleep(sleep_time)
        test_info.title("¡Completado!")
        for i in range(finish_length - fps):
            idx = i + start_length + path_length
            st.session_state.test_mngr.testRegisterValues()
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(idx))
            time.sleep(sleep_time)
    st.session_state.test_mngr.testStop()


def startDemo(test_info, figure, fps, path_length, start_length, finish_length):
    sleep_time = 1 / fps
    global_path = st.session_state.data_mngr.global_path
    st.session_state.data_mngr.setupSensorGroups(
        st.session_state.sensor_mngr.getGroup("platform_1"),
        st.session_state.sensor_mngr.getGroup("platform_2"),
        True,
    )
    st.session_state.data_mngr.clearSensorData()
    # Prepare sensor data injection
    force_total = 800
    platform_left = []
    platform_right = []
    for pose in global_path:
        pose = random.uniform(pose - 0.25, pose + 0.25)
        platform_left_values, platform_right_values = (
            st.session_state.data_mngr.getDemoPlatformForces(pose, force_total)
        )
        platform_left.append(platform_left_values)
        platform_right.append(platform_right_values)
    with st.spinner("Ejecutando prueba"):
        test_info.title("Quédate en el centro")
        for i in range(start_length):
            st.session_state.data_mngr.setDemoPlatformForces(
                platform_left[i], platform_right[i]
            )
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(i))
            time.sleep(sleep_time)
        test_info.title("¡Sigue el camino!")
        for i in range(path_length):
            idx = i + start_length
            st.session_state.data_mngr.setDemoPlatformForces(
                platform_left[idx], platform_right[idx]
            )
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(idx))
            time.sleep(sleep_time)
        test_info.title("¡Completado!")
        for i in range(finish_length - fps):
            idx = i + start_length + path_length
            st.session_state.data_mngr.setDemoPlatformForces(
                platform_left[idx], platform_right[idx]
            )
            figure.plotly_chart(st.session_state.data_mngr.getFramedFigure(idx))
            time.sleep(sleep_time)


def level_normal():
    if "level_recorded" not in st.session_state:
        st.session_state.level_recorded = False
    if "get_balloons" not in st.session_state:
        st.session_state.get_balloons = False
    if "user_name" not in st.session_state:
        st.session_state.user_name = "Anónimo"
    if "user_score" not in st.session_state:
        st.session_state.user_score = 400

    if st.session_state.get("btn_save", False):
        # Merge data to ranked dataframe and backup csv file.
        st.session_state.data_mngr.updateScoreboardNormal(
            st.session_state.user_name, st.session_state.user_score
        )
        # Reset states
        st.session_state.level_recorded = False
        # Switch to ranking page
        st.switch_page(st.Page(ranking.ranking))
    elif st.session_state.get("btn_rec_cancel", False):
        st.session_state.level_recorded = False

    if st.session_state.inverted_mode:
        st.header(
            ":material/directions_car: Modo carretera", divider="green", anchor=False
        )
        if not st.session_state.level_recorded:
            st.error(
                ":material/warning: **Modo espejo activo** - ¡Los controles están invertidos!"
            )
    else:
        st.header(
            ":material/directions_car: Modo carretera", divider="green", anchor=False
        )

    figure = st.empty()
    test_info = st.empty()
    test_btns = st.empty()

    if st.session_state.level_recorded:
        # Results and achievements
        results = st.session_state.data_mngr.getResultsNormal(
            st.session_state.inverted_mode
        )
        st.session_state.user_score = results["score"]
        position = results["position"]
        total = results["total"]
        metric_col1, metric_col2, metric_col3 = st.columns([0.3, 0.25, 0.45])
        metric_col1.metric(
            "Posición ranking",
            f"Nº {position}",
            f"De {total} personas",
            "off",
        )
        if st.session_state.inverted_mode:
            metric_col2.metric(
                "Puntuación",
                f"{int(st.session_state.user_score):d}",
                f"De 1500 (x1.5)",
                "normal",
            )
        else:
            metric_col2.metric(
                "Puntuación",
                f"{int(st.session_state.user_score):d}",
                f"De 1000",
                "off",
            )

        achievements = getAchievements(position, total)
        if achievements:
            for achievement in achievements.values():
                metric_col3.warning(achievement[0], icon=achievement[1])
        if not st.session_state.get_balloons:
            st.balloons()
            st.session_state.get_balloons = True
        st.plotly_chart(st.session_state.data_mngr.getCompleteFigure())
        col1, col2, col3 = st.columns([0.5, 0.25, 0.25])
        st.session_state.user_name = col1.text_input(
            label="Indica tu nombre", label_visibility="collapsed", value="Anónimo"
        )
        col2.button(
            label="Guardar", key="btn_save", type="primary", use_container_width=True
        )
        col3.button(label="Cancelar", key="btn_rec_cancel", use_container_width=True)
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
            path_objectives,
            path_length,
            start_length,
            finish_length,
            fps,
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
            if st.session_state.inverted_mode:
                logger.info("¡Inverted mode enabled!")
            startTest(test_info, figure, fps, path_length, start_length, finish_length)
        else:
            logger.info("Starting demo!")
            startDemo(test_info, figure, fps, path_length, start_length, finish_length)

        test_info.empty()
        st.session_state.level_recorded = True
        st.switch_page(st.Page(level_normal))

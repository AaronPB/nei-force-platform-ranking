import streamlit as st
import time

from pages import ranking

from loguru import logger


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
        # TODO Generate results
        figure.plotly_chart(st.session_state.data_mngr.getCompleteFigure())
        col1, col2 = st.columns(2)
        col1.button(
            label="Guardar", key="btn_save", type="primary", use_container_width=True
        )
        col2.button(label="Cancelar", key="btn_rec_cancel", use_container_width=True)
        return

    btn_return = st.button(
        label="Volver",
        use_container_width=True,
    )
    if btn_return:
        st.switch_page(st.Page(ranking.ranking))

    btn_col1, btn_col2 = test_btns.columns(2)
    btn_start = btn_col1.button(
        label="Iniciar prueba",
        key="btn_start_test",
        type="primary",
        use_container_width=True,
        disabled=not st.session_state.demo_enabled
        and not st.session_state.platforms_connected,
    )
    btn_col2.button("Regenerar", use_container_width=True)

    # Build road path
    path_objectives = 10
    fps = 20
    duration_secs = 20
    initial_secs = 5
    final_secs = 3
    path_length = int(duration_secs * fps)
    start_length = int(initial_secs * fps)
    finish_length = int(final_secs * fps)
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

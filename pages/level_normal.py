import streamlit as st
import time

from pages import ranking

from loguru import logger
from src.managers.dataManager import TrajectoryFigure


def level_normal():
    if "level_recorded" not in st.session_state:
        st.session_state.level_recorded = False
    if "level_figure" not in st.session_state:
        st.session_state.level_figure = TrajectoryFigure(10)
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

    timer = st.empty()
    figure = st.empty()
    test_btns = st.empty()

    if st.session_state.level_recorded:
        # TODO Generate results
        figure.plotly_chart(st.session_state.level_figure.getCompleteFigure())
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
    )
    btn_col2.button("Regenerar", use_container_width=True)

    st.session_state.level_figure = TrajectoryFigure(10)

    figure.plotly_chart(st.session_state.level_figure.getCompleteFigure())

    if btn_start:
        test_btns.empty()
        timer_col1, timer_col2 = timer.columns(2)
        timer_title = timer_col1.empty()
        timer_time = timer_col2.empty()

        with st.spinner("Ejecutando prueba"):
            # Generate random path
            path_length = 400
            player_x = 0
            timer_title.title("¡Prepárate!")
            for i in range(60):
                time_index = 60 - i
                seconds = time_index / 20
                formatted_time = f"{int(seconds):02}.{int(time_index % 20)}"
                timer_time.title(formatted_time)
                figure.plotly_chart(
                    st.session_state.level_figure.getFigure(i, player_x)
                )
                time.sleep(0.05)
            timer_title.title("Concentración")
            for i in range(path_length):
                time_index = path_length - i
                seconds = time_index / 20
                formatted_time = f"{int(seconds):02}.{int(time_index % 20)}"
                timer_time.title(formatted_time)
                figure.plotly_chart(
                    st.session_state.level_figure.getFigure(i + 60, player_x)
                )
                time.sleep(0.05)
            timer_title.title("¡Finalizado!")
            timer_time.empty()
            for i in range(40):
                figure.plotly_chart(
                    st.session_state.level_figure.getFigure(
                        i + 60 + path_length, player_x
                    )
                )
                time.sleep(0.05)
        timer.empty()
        st.session_state.level_recorded = True
        st.switch_page(st.Page(level_normal))

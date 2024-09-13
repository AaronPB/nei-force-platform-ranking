import streamlit as st
import pandas as pd
import time

from pages import ranking

from loguru import logger


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

    if not st.session_state.recording and st.session_state.results.empty:
        st.info("Colócate en las plataformas", icon=":material/settings_accessibility:")

    _, countdown_col, _ = st.columns([1, 0.5, 1])
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
            time.sleep(0.5)
            for i in range(3, 0, -1):
                countdown.metric("¡Preparados!", i)
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

    if st.session_state.recording and not st.session_state.results.empty:
        st.write("¡Aquí están los resultados!")
        st.data_editor(
            data=st.session_state.results,
            use_container_width=True,
            hide_index=True,
            disabled=("Area", "Puntuación"),
        )

        col1, col2 = st.columns(2)
        col1.button(label="Guardar",key="btn_save",type="primary",use_container_width=True)
        col2.button(label="Cancelar",key="btn_rec_cancel",use_container_width=True)

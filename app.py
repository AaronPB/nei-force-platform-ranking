import streamlit as st

from pages import ranking, level_normal, level_hard
from src.managers import ConfigManager, SensorManager, TestManager


def main():
    # Page configuration
    st.set_page_config(
        page_title="Platform Ranking",
        page_icon="images/app_icon.png",
        layout="wide",
        initial_sidebar_state="collapsed",
    )
    # Logo
    st.logo(
        image="images/app_logo.png",
        icon_image="images/app_icon.png",
        link="https://github.com/AaronPB",
    )
    # Load pages
    pg = st.navigation(
        [
            st.Page(
                ranking.ranking,
                title="Ranking",
                icon=":material/star:",
            ),
            st.Page(
                level_normal.level_normal,
                title="Modo carretera",
                icon=":material/directions_car:",
            ),
            st.Page(
                level_hard.level_hard,
                title="Modo derrapes",
                icon=":material/car_crash:",
            ),
        ]
    )
    pg.run()

    # Define sidebar and main variables
    if "config_mngr" not in st.session_state:
        st.session_state.config_mngr = ConfigManager()
    if "sensor_mngr" not in st.session_state:
        st.session_state.sensor_mngr = SensorManager()
        st.session_state.sensor_mngr.setup(st.session_state.config_mngr)
    if "test_mngr" not in st.session_state:
        st.session_state.test_mngr = TestManager()
        st.session_state.test_mngr.setSensorGroups(
            st.session_state.sensor_mngr.getGroups()
        )
    if "platforms_connected" not in st.session_state:
        st.session_state.platforms_connected = False
    if "demo_enabled" not in st.session_state:
        st.session_state.demo_enabled = False

    if st.session_state.get("enable_demo", False):
        st.session_state.demo_enabled = True
    elif st.session_state.get("disable_demo", False):
        st.session_state.demo_enabled = False

    btn_connect_sensors = st.sidebar.button(
        label="Conectar plataformas",
        key="btn_sensors",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.demo_enabled,
    )

    if not st.session_state.demo_enabled:
        platform_status = st.sidebar.empty()

        if btn_connect_sensors:
            st.session_state.platforms_connected = False
            with platform_status.status("Conectando sensores..."):
                st.session_state.test_mngr.checkConnection()
            platform_status.empty()

        sensor_groups = st.session_state.sensor_mngr.getGroups()
        connected_sensor = 0
        for group in sensor_groups:
            connected_sensor += len(group.getSensors(only_available=True))

        if connected_sensor == 0:
            st.sidebar.error(
                "Conecta las plataformas.",
                icon=":material/error:",
            )
        elif connected_sensor < 24:
            st.sidebar.warning(
                f"{connected_sensor} de 24 sensores conectados.",
                icon=":material/change_circle:",
            )
        elif connected_sensor == 24:
            st.sidebar.success(
                "Plataformas conectadas.",
                icon=":material/check_circle:",
            )
            st.session_state.platforms_connected = True

    if st.session_state.demo_enabled:
        st.sidebar.success("Modo demo activo.", icon=":material/build_circle:")
    st.sidebar.divider()
    if st.session_state.demo_enabled:
        st.sidebar.button(label="Desactivar demo", key="disable_demo", use_container_width=True)
    else:
        st.sidebar.button(label="Activar demo", key="enable_demo", use_container_width=True)


if __name__ == "__main__":
    main()

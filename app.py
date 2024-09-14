import streamlit as st

from pages import ranking, dashboard
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
                dashboard.dashboard,
                title="Panel",
                icon=":material/table_chart_view:",
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

    btn_connect_sensors = st.sidebar.button(
        label="Conectar plataformas",
        key="btn_sensors",
        type="primary",
        use_container_width=True,
    )

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


if __name__ == "__main__":
    main()

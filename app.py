import streamlit as st
from pages import ranking, info, dashboard, settings


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
                info.info,
                title="Información",
                icon=":material/info:",
            ),
            st.Page(
                dashboard.dashboard,
                title="Panel",
                icon=":material/table_chart_view:",
            ),
            st.Page(
                settings.settings,
                title="Configuración",
                icon=":material/settings:",
            ),
        ]
    )
    pg.run()


if __name__ == "__main__":
    main()

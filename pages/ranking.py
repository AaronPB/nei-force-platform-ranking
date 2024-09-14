import streamlit as st
from streamlit_carousel import carousel
import pandas as pd

# Just for graph testing
import random

# Define image sliders
# TODO Add proper sliders
sliders = [
    dict(title="", text="", img="images/nei_almeria_2024.jpg"),
    dict(title="", text="", img="images/force_platform_logo.png"),
]


def generateDataframe() -> pd.DataFrame:
    df = pd.DataFrame(
        {
            "Nombre": ["Usuario1", "Usuario2", "Usuario3"],
            "Equilibrio": [
                [random.randint(-3, 3) for _ in range(100)] for _ in range(3)
            ],
            "Área elipse (cm2)": [1.23, 2.32, 2.45],
            "Puntuación": [950, 870, 340],
        }
    )
    df.index = df.index + 1
    return df


def ranking():
    carousel(items=sliders, controls=False, container_height=200)
    st.header(":material/social_leaderboard: Ranking del TOP 20")
    st.write("¡Las 20 personas con mejor equilibrio al cerrar los ojos!")

    st.dataframe(
        data=generateDataframe(),
        use_container_width=True,
        column_config={
            "Equilibrio": st.column_config.AreaChartColumn(
                "Trayectoria del centro de presiones", y_min=-3, y_max=3
            ),
        },
    )

# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os

from plotly.subplots import make_subplots
import plotly.graph_objs as go

from src.handlers import SensorGroup

from loguru import logger


class DataManager:
    def __init__(self):
        self.df_calibrated = pd.DataFrame()
        self.df_scoreboard = pd.DataFrame(
            columns=["name", "cop", "area", "score"],
        )
        self.df_scoreboard_sorted = pd.DataFrame(
            columns=["name", "cop", "area", "score"],
        )
        # Load saved dataframe
        self.file_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "files",
            "data.csv",
        )
        if os.path.exists(self.file_path):
            self.df_scoreboard = pd.read_csv(self.file_path)
            df_scores = self.df_scoreboard.copy(deep=True)
            self.df_scoreboard_sorted = df_scores.sort_values(
                by="score", ascending=False
            )
            self.df_scoreboard_sorted = self.df_scoreboard_sorted.reset_index(drop=True)
            self.df_scoreboard_sorted.index = self.df_scoreboard_sorted.index + 1
        # Plotly figure
        self.plotly_fig = COPFigure()

    # Data load methods

    def loadData(self, sensor_groups: list[SensorGroup]) -> None:
        self.df_calibrated = pd.DataFrame()
        for group in sensor_groups:
            for sensor in group.getSensors().values():
                slope = sensor.getSlope()
                intercept = sensor.getIntercept()
                self.df_calibrated[sensor.getName()] = [
                    value * slope + intercept for value in sensor.getValues()
                ]
        self.plotly_fig.updateData(self.df_calibrated)

    def updateScoreboard(self, df: pd.DataFrame = None) -> None:
        if df is not None:
            self.df_scoreboard = pd.concat([self.df_scoreboard, df], ignore_index=True)
        df_scores = self.df_scoreboard.copy(deep=True)
        self.df_scoreboard_sorted = df_scores.sort_values(by="score", ascending=False)
        self.df_scoreboard_sorted = self.df_scoreboard_sorted.reset_index(drop=True)
        self.df_scoreboard_sorted.index = self.df_scoreboard_sorted.index + 1
        self.df_scoreboard.to_csv(self.file_path, index=False)

    # Getters

    def getFigure(self) -> go.Figure:
        return self.plotly_fig.getFigure()

    def getResults(self) -> dict:
        areas = self.plotly_fig.getAreas()
        cops = self.plotly_fig.getCOPs()
        cops_array = np.array(cops)
        # Operate
        area_min = 0
        area_max = 10
        score_min = 500
        score_max = 1000
        area = sum(areas)
        total_cop = np.sum(cops_array, axis=0).tolist()
        position = (
            np.searchsorted(self.df_scoreboard_sorted["area"].values, sum(areas)) + 1
        )
        total = len(self.df_scoreboard) + 1
        value = np.clip(area, area_min, area_max)
        scale = (area_max - area) / area_max
        a = 2
        score = score_min + (score_max - score_min) * (a**scale - 1) / (a - 1)
        return {
            "area": area,
            "score": score,
            "position": position,
            "total": total,
            "cop": total_cop,
        }

    def getScoreboard(self) -> pd.DataFrame:
        return self.df_scoreboard_sorted

    def formatDataframe(
        self, df: pd.DataFrame, idx1: int = 0, idx2: int = 0
    ) -> pd.DataFrame:
        # Format dataframe values to 0.000000e+00
        df = df.map("{:.6e}".format)
        return df


class TrajectoryFigure:
    def __init__(self, path_objectives: int = 10) -> None:
        self.figure = go.Figure()
        self.user_path = np.array([])
        self.path_window_length = 10
        random_path_length = 400
        interfase_path_length = int(random_path_length / (2 * path_objectives))

        # Generate random path
        objective_points = self.generateObjectives(path_objectives)

        path_segments = []
        logger.debug(objective_points)
        # Generate transition and constant segments
        for i in range(len(objective_points) - 1):
            path_segments.append(
                np.linspace(
                    objective_points[i], objective_points[i + 1], interfase_path_length
                )
            )
            path_segments.append(
                np.full(interfase_path_length, objective_points[i + 1])
            )
        # Final transition to 0
        path_segments.append(
            np.linspace(objective_points[-1], 0, interfase_path_length)
        )
        path_segments.append(np.full(interfase_path_length, 0))

        self.random_path = np.hstack(path_segments)
        self.global_path = np.pad(
            self.random_path, (60, 60), mode="constant", constant_values=0
        )
        self.buildTraces()

    def generateObjectives(self, path_objectives):
        points = [0]
        for _ in range(1, path_objectives):
            if np.random.rand() < 0.5:
                change = np.random.uniform(0.5, 2)
            else:
                change = np.random.uniform(-2, -0.5)
            if points[-1] < -1.3:
                change = np.random.uniform(2, 3)
            elif points[-1] > 1.3:
                change = np.random.uniform(-3, -2)
            new_point = points[-1] + change
            new_point = np.clip(new_point, -3, 3)
            points.append(new_point)
        return np.array(points)

    def buildTraces(self) -> None:
        path_corners_offset = 0.5
        self.figure.add_trace(
            go.Scatter(
                x=self.global_path,
                y=np.linspace(0, len(self.global_path), len(self.global_path)),
                mode="lines",
                line=dict(color="white", width=3),
                name="Camino",
            )
        )
        self.figure.add_trace(
            go.Scatter(
                x=self.global_path + path_corners_offset,
                y=np.linspace(0, len(self.global_path), len(self.global_path)),
                mode="lines",
                line=dict(color="gray", width=2),
                name="Borde derecho",
            )
        )
        self.figure.add_trace(
            go.Scatter(
                x=self.global_path - path_corners_offset,
                y=np.linspace(0, len(self.global_path), len(self.global_path)),
                mode="lines",
                line=dict(color="gray", width=2),
                name="Borde izquierdo",
                fill="tonextx",
                fillcolor="rgba(0, 100, 255, 0.2)",
            )
        )
        self.figure.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=60,
            y1=60,
            xref="paper",
            yref="y",
            line=dict(color="red", width=3, dash="dash"),
        )
        self.figure.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=460,
            y1=460,
            xref="paper",
            yref="y",
            line=dict(color="red", width=3, dash="dash"),
        )
        user_pose = go.Scatter(
            x=[0],
            y=[0],
            mode="markers",
            marker=dict(symbol="triangle-up", size=22, color="red"),
            name="Jugador",
            showlegend=False,
        )
        self.figure.add_trace(user_pose)

    def getFigure(self, index: int, user_pose: float) -> go.Figure:
        self.user_path = np.append(self.user_path, user_pose)
        self.figure.update_traces(
            x=[user_pose], y=[index], selector=dict(name="Jugador")
        )
        self.figure.update_layout(
            xaxis=dict(
                range=[-5, 5],
                showticklabels=False,
                showline=False,
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="yellow",
            ),
            yaxis=dict(
                range=[index - 1, index + 20],
                showticklabels=False,
                showline=False,
            ),
            showlegend=False,
            # width=400,
            # height=400
        )
        return self.figure

    def getCompleteFigure(self) -> go.Figure:
        if len(self.user_path) > 0:
            self.figure.add_trace(
                go.Scatter(
                    x=self.user_path,
                    y=np.linspace(0, len(self.user_path) - 1, len(self.user_path)),
                    mode="lines",
                    line=dict(color="red", width=2),
                    name="Camino trazado",
                )
            )
        self.figure.update_layout(
            xaxis=dict(
                range=[-5, 5],
                showticklabels=False,
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="yellow",
            ),
            yaxis=dict(
                range=[0, 600],
                showticklabels=False,
                showline=False,
                zeroline=True,
                zerolinewidth=2,
                zerolinecolor="yellow",
            ),
            showlegend=False,
            height=800,
        )
        return self.figure


class COPFigure:
    def __init__(self) -> None:
        self.figure = make_subplots(
            rows=1,
            cols=2,
            shared_xaxes=True,
            shared_yaxes=True,
            specs=[[{"type": "xy"}, {"type": "xy"}]],
        )
        self.buildSubplots()
        self.df: pd.DataFrame = None
        self.area1: float = 0
        self.area2: float = 0

    def buildSubplots(self) -> None:
        x_range = [-200, 200]
        y_range = [-300, 300]
        square_trace = go.Scatter(
            x=[x_range[0], x_range[1], x_range[1], x_range[0], x_range[0]],
            y=[y_range[0], y_range[0], y_range[1], y_range[1], y_range[0]],
            mode="lines",
            line=dict(color="blue", width=2),
            fill="toself",
            fillcolor="rgba(0,0,255,0.1)",
            name="Platform",
            showlegend=False,
        )
        default_ellipse_trace = go.Scatter(
            x=[0],
            y=[0],
            mode="lines",
            line=dict(color="Red"),
            fill="toself",
            fillcolor="rgba(255,0,0,0.3)",
            name="LMS ellipse",
            showlegend=False,
        )
        default_cop_trace = go.Scatter(
            x=[0],
            y=[0],
            mode="lines",
            line=dict(color="MediumPurple"),
            name="COP",
            showlegend=False,
        )
        default_ellipse_text_trace = go.Scatter(
            x=[0],
            y=[0],
            mode="text",
            name="COP area",
            text=["Area"],
            textposition="middle center",
            textfont=dict(size=14, color="White"),
            showlegend=False,
        )
        # self.figure.add_trace(square_trace, row=1, col=1)
        # self.figure.add_trace(square_trace, row=1, col=2)
        self.figure.add_trace(default_cop_trace, row=1, col=1)
        self.figure.add_trace(default_cop_trace, row=1, col=2)
        self.figure.add_trace(default_ellipse_trace, row=1, col=1)
        self.figure.add_trace(default_ellipse_trace, row=1, col=2)
        self.figure.add_trace(default_ellipse_text_trace, row=1, col=1)
        self.figure.add_trace(default_ellipse_text_trace, row=1, col=2)

    def getFigure(self) -> go.Figure:
        self.figure.update_layout(
            title="Trayectorias de los centros de presiones",
            xaxis_title="Desplazamiento Medio-Lateral (mm)",
            yaxis_title="Desplazamiento Anterior-Posterior (mm)",
            xaxis2_title="Desplazamiento Medio-Lateral (mm)",
            # xaxis_range=[-200, 200],
            # yaxis_range=[-300, 300],
            # xaxis2_range=[-200, 200],
            # yaxis2_range=[-300, 300],
        )
        self.figure.update_annotations()
        return self.figure

    def getAreas(self) -> list[float]:
        return [self.area1, self.area2]

    def getCOPs(self) -> list[np.array]:
        return [self.copx1, self.copy1, self.copx2, self.copy2]

    def updateData(self, df: pd.DataFrame) -> None:
        self.df = df
        self.copx1, self.copy1 = self.getCOP(
            self.df.iloc[:, 4:8].values,
            self.df.iloc[:, 8:12].values,
            self.df.iloc[:, 0:4].values,
        )
        offset = 12
        self.copx2, self.copy2 = self.getCOP(
            self.df.iloc[:, 4 + offset : 8 + offset].values,
            self.df.iloc[:, 8 + offset : 12 + offset].values,
            self.df.iloc[:, 0 + offset : 4 + offset].values,
        )
        elipsx1, elipsy1, self.area1 = self.getEllipse(self.copx1, self.copy1)
        elipsx2, elipsy2, self.area2 = self.getEllipse(self.copx2, self.copy2)
        self.figure.update_traces(
            x=self.copy1, y=self.copx1, selector=dict(name="COP"), col=2
        )
        self.figure.update_traces(
            x=self.copy2, y=self.copx2, selector=dict(name="COP"), col=1
        )
        self.figure.update_traces(
            x=elipsy1, y=elipsx1, selector=dict(name="LMS ellipse"), col=2
        )
        self.figure.update_traces(
            x=elipsy2, y=elipsx2, selector=dict(name="LMS ellipse"), col=1
        )
        self.figure.update_traces(
            text=[f"Área: {self.area1:.2f} cm2"], selector=dict(name="COP area"), col=2
        )
        self.figure.update_traces(
            text=[f"Área: {self.area2:.2f} cm2"], selector=dict(name="COP area"), col=1
        )

    def getCOP(
        self, forces_x: np.array, forces_y: np.array, forces_z: np.array
    ) -> tuple[np.array, np.array]:
        lx, ly, h = 508, 308, 20
        mx = (
            ly
            / 2
            * (-forces_z[:, 3] + forces_z[:, 0] + forces_z[:, 1] - forces_z[:, 2])
        )
        my = (
            lx
            / 2
            * (-forces_z[:, 3] + forces_z[:, 0] + forces_z[:, 1] + forces_z[:, 2])
        )
        xsum = forces_x[:, 1] + forces_x[:, 2] - forces_x[:, 0] - forces_x[:, 3]
        ysum = forces_y[:, 2] + forces_y[:, 3] - forces_y[:, 0] - forces_y[:, 1]
        zsum = np.sum(forces_z, axis=1)
        copx = (-h * xsum - my) / zsum
        copy = (-h * ysum + mx) / zsum
        copxmean = copx - np.mean(copx)
        copymean = copy - np.mean(copy)
        return copxmean, copymean

    def getEllipse(
        self, copx: np.array, copy: np.array
    ) -> tuple[np.array, np.array, float]:
        cov_matrix = np.cov(copx, copy)
        D, V = np.linalg.eig(cov_matrix)

        # Ellipse rotation angle
        theta = np.arctan2(V[1, 0], V[0, 0])

        # Ellipse semi-axis
        semi_axis = np.sqrt(D)

        # Ellipse params
        a = semi_axis[0]
        b = semi_axis[1]
        area = np.pi * a * b / 100  # In cm2
        x0 = np.mean(copx)
        y0 = np.mean(copy)

        # Ellipse coords
        phi = np.linspace(0, 2 * np.pi, 100)
        x = x0 + a * np.cos(phi) * np.cos(theta) - b * np.sin(phi) * np.sin(theta)
        y = y0 + a * np.cos(phi) * np.sin(theta) + b * np.sin(phi) * np.cos(theta)

        return x, y, area

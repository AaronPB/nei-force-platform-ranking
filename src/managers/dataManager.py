# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import os

from plotly.subplots import make_subplots
import plotly.graph_objs as go

from src.handlers import SensorGroup, Sensor

from loguru import logger


class DataManager:
    def __init__(self):
        self.df_calibrated = pd.DataFrame()
        self.df_scoreboard_normal = pd.DataFrame(columns=["name", "score"])
        self.df_scoreboard_hard = pd.DataFrame(columns=["name", "score"])

        # Platform variables
        self.platform_left = list[Sensor]
        self.platform_left_m = np.array([])
        self.platform_left_b = np.array([])
        self.platform_right = list[Sensor]
        self.platform_right_m = np.array([])
        self.platform_right_b = np.array([])
        self.force_mean_left = 0
        self.force_mean_right = 0

        # Load saved dataframe
        self.file_path_normal = os.path.join(
            os.path.dirname(__file__), "..", "..", "files", "data_normal.csv"
        )
        self.file_path_hard = os.path.join(
            os.path.dirname(__file__), "..", "..", "files", "data_hard.csv"
        )
        if os.path.exists(self.file_path_normal):
            self.df_scoreboard_normal = pd.read_csv(self.file_path_normal)
        if os.path.exists(self.file_path_hard):
            self.df_scoreboard_hard = pd.read_csv(self.file_path_hard)
        # Plotly figure
        self.plotly_fig = TrajectoryFigure(10)

    # Data load methods

    def reloadFigure(self, path_objectives: int = 10) -> None:
        self.plotly_fig = TrajectoryFigure(path_objectives)

    def setupSensorGroups(
        self,
        platform_left: SensorGroup,
        platform_right: SensorGroup,
    ) -> None:
        m_list = []
        b_list = []
        for sensor in platform_left.getSensors(only_available=True).values():
            self.platform_left.append(sensor)
            m_list.append(sensor.getSlope())
            b_list.append(sensor.getIntercept())
        self.platform_left_m = np.hstack(m_list)
        self.platform_left_b = np.hstack(b_list)
        m_list = []
        b_list = []
        for sensor in platform_right.getSensors(only_available=True).values():
            self.platform_right.append(sensor)
            m_list.append(sensor.getSlope())
            b_list.append(sensor.getIntercept())
        self.platform_right_m = np.hstack(m_list)
        self.platform_right_b = np.hstack(b_list)

    def updateScoreboard(self, df: pd.DataFrame = None) -> None:
        pass
        # if df is not None:
        #     self.df_scoreboard = pd.concat([self.df_scoreboard, df], ignore_index=True)
        # df_scores = self.df_scoreboard.copy(deep=True)
        # self.df_scoreboard_sorted = df_scores.sort_values(by="score", ascending=False)
        # self.df_scoreboard_sorted = self.df_scoreboard_sorted.reset_index(drop=True)
        # self.df_scoreboard_sorted.index = self.df_scoreboard_sorted.index + 1
        # self.df_scoreboard.to_csv(self.file_path, index=False)

    # Getters

    def getDemoFramedFigure(self, index: int) -> go.Figure:
        user_pose = 0
        return self.plotly_fig.getFigure(index, user_pose)

    def getFramedFigure(self, index: int) -> go.Figure:
        # Get user_pose from platform_data
        force_left = np.sum(
            np.array([sensor.getValues()[-1] for sensor in self.platform_left])
            * self.platform_left_m
            + self.platform_left_b
        )
        force_right = np.sum(
            np.array([sensor.getValues()[-1] for sensor in self.platform_right])
            * self.platform_right_m
            + self.platform_right_b
        )
        force_diff = force_right - force_left
        force_total = force_right + force_left
        if force_diff >= 0:
            user_pose = min(5, 5 * (force_diff / force_total))
        else:
            user_pose = min(-5, -5 * (abs(force_diff) / force_total))

        return self.plotly_fig.getFigure(index, user_pose)

    def getCompleteFigure(self) -> go.Figure:
        return self.plotly_fig.getCompleteFigure()

    def getResultsNormal(self) -> dict:
        score_max = 1000
        score_min = 400
        df_score = self.getScoreboardNormal()

        # Get score
        random_path = self.plotly_fig.getRandomPath()
        user_path = self.plotly_fig.getUserPath()
        diff_path = np.sum(np.abs(random_path - user_path))
        score = score_max - ((score_max - score_min) * min(diff_path, 2000) / 2000)

        position = np.searchsorted(df_score["score"].values, score) + 1
        total = len(df_score) + 1
        return {"score": score, "position": position, "total": total}

    def getScoreboardNormal(self) -> pd.DataFrame:
        df_scores = self.df_scoreboard_normal.copy(deep=True)
        df_sorted = df_scores.sort_values(by="score", ascending=False)
        df_sorted = df_sorted.reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        return df_sorted

    def getScoreboardHard(self) -> pd.DataFrame:
        df_scores = self.df_scoreboard_hard.copy(deep=True)
        df_sorted = df_scores.sort_values(by="score", ascending=False)
        df_sorted = df_sorted.reset_index(drop=True)
        df_sorted.index = df_sorted.index + 1
        return df_sorted


class TrajectoryFigure:
    def __init__(self, path_objectives: int) -> None:
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

    def getRandomPath(self):
        return self.global_path[60 : 60 + len(self.user_path)]

    def getUserPath(self):
        return self.user_path[60 : 60 + len(self.user_path)]

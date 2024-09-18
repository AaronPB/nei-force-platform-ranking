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

        # Road variables
        self.global_path = np.array([])
        self.random_path = np.array([])
        self.user_path = np.array([])
        self.path_idx_start = 0
        self.path_idx_finish = 0
        self.fps = 20

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
        self.plotly_fig: TrajectoryFigure

    # Data load methods

    def createPath(
        self,
        path_objectives: int,
        path_length: int,
        start_length: int,
        finish_length: int,
        fps: int,
    ) -> None:
        # Clear variables
        self.random_path = np.array([])
        self.user_path = np.array([])
        self.path_idx_start = start_length
        self.path_idx_finish = start_length + path_length
        self.fps = fps

        # Generate random path
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
        objective_points = np.array(points)

        path_segments = []
        logger.debug(objective_points)
        # Generate transition and constant segments
        interfase_path_length = int(path_length / (2 * path_objectives))
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
            self.random_path,
            (start_length, finish_length),
            mode="constant",
            constant_values=0,
        )
        self.plotly_fig = TrajectoryFigure(
            self.global_path, self.path_idx_start, self.path_idx_finish, self.fps
        )

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

    def updateScoreboardNormal(self, name: str, score: float) -> None:
        if name in self.df_scoreboard_normal["name"].values:
            i = 1
            new_name = f"{name}_{i}"
            while new_name in self.df_scoreboard_normal["name"].values:
                i += 1
                new_name = f"{name}_{i}"
            name = new_name
        new_entry = pd.DataFrame({"name": name, "score": score}, index=[0])
        self.df_scoreboard_normal = pd.concat(
            [self.df_scoreboard_normal, new_entry], ignore_index=True
        )
        self.df_scoreboard_normal.to_csv(self.file_path_normal, index=False)

    def updateScoreboardHard(self, name: str, score: float) -> None:
        if name in self.df_scoreboard_hard["name"].values:
            i = 1
            new_name = f"{name}_{i}"
            while new_name in self.df_scoreboard_hard["name"].values:
                i += 1
                new_name = f"{name}_{i}"
            name = new_name
        new_entry = pd.DataFrame({"name": name, "score": score}, index=[0])
        self.df_scoreboard_hard = pd.concat(
            [self.df_scoreboard_hard, new_entry], ignore_index=True
        )
        self.df_scoreboard_hard.to_csv(self.file_path_hard, index=False)

    # Getters

    def getDemoFramedFigure(self, index: int, objective: float) -> go.Figure:
        user_pose = np.random.uniform(objective - 0.25, objective + 0.25, 1)
        self.user_path = np.append(self.user_path, user_pose)
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
        self.user_path = np.append(self.user_path, [user_pose])
        return self.plotly_fig.getFigure(index, [user_pose])

    def getCompleteFigure(self) -> go.Figure:
        if len(self.user_path) > 0:
            return self.plotly_fig.getCompleteFigure(self.user_path)
        return self.plotly_fig.getCompleteFigure()

    def getResultsNormal(self) -> dict:
        score_max = 1000
        score_min = 400
        max_diff = 600 * (self.fps / 20)
        df_score = self.getScoreboardNormal()

        # Get score
        diff_path = np.sum(
            np.abs(
                self.random_path
                - self.user_path[self.path_idx_start : self.path_idx_finish]
            )
        )
        score = score_max - (
            (score_max - score_min) * min(diff_path, max_diff) / max_diff
        )

        position = np.searchsorted(np.sort(df_score["score"].values), score)
        total = len(df_score) + 1
        position = total - position
        return {"score": score, "position": position, "total": total}

    def getResultsHard(self) -> dict:
        score_max = 1000
        score_min = 400
        max_diff = 600 * (self.fps / 20)
        df_score = self.getScoreboardHard()

        # Get score
        diff_path = np.sum(
            np.abs(
                self.random_path
                - self.user_path[self.path_idx_start : self.path_idx_finish]
            )
        )
        score = score_max - (
            (score_max - score_min) * min(diff_path, max_diff) / max_diff
        )

        position = np.searchsorted(np.sort(df_score["score"].values), score)
        total = len(df_score) + 1
        position = total - position
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
    def __init__(
        self, random_path: np.ndarray, start_idx: int, finish_idx: int, fps: int
    ) -> None:
        self.figure = go.Figure()
        self.random_path = random_path
        self.start_idx = start_idx
        self.finish_idx = finish_idx
        self.fps = fps
        self.path_window_length = 10  # Not used

        self.buildTraces()

    def buildTraces(self) -> None:
        path_corners_offset = 0.5
        self.figure.add_trace(
            go.Scatter(
                x=self.random_path,
                y=np.linspace(0, len(self.random_path), len(self.random_path)),
                mode="lines",
                line=dict(color="white", width=3),
                name="Camino",
            )
        )
        self.figure.add_trace(
            go.Scatter(
                x=self.random_path + path_corners_offset,
                y=np.linspace(0, len(self.random_path), len(self.random_path)),
                mode="lines",
                line=dict(color="gray", width=2),
                name="Borde derecho",
            )
        )
        self.figure.add_trace(
            go.Scatter(
                x=self.random_path - path_corners_offset,
                y=np.linspace(0, len(self.random_path), len(self.random_path)),
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
            y0=self.start_idx,
            y1=self.start_idx,
            xref="paper",
            yref="y",
            line=dict(color="red", width=3, dash="dash"),
        )
        self.figure.add_shape(
            type="line",
            x0=0,
            x1=1,
            y0=self.finish_idx,
            y1=self.finish_idx,
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

    def getFigure(self, index: int, user_pose: np.ndarray) -> go.Figure:
        self.figure.update_traces(x=user_pose, y=[index], selector=dict(name="Jugador"))
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
                range=[index - 1, index + self.fps],
                showticklabels=False,
                showline=False,
            ),
            showlegend=False,
            # width=400,
            # height=400
        )
        return self.figure

    def getCompleteFigure(self, user_path: np.ndarray = None) -> go.Figure:
        if user_path is not None and len(user_path) > 0:
            self.figure.add_trace(
                go.Scatter(
                    x=user_path,
                    y=np.linspace(0, len(user_path) - 1, len(user_path)),
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
                range=[0, len(self.random_path)],
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

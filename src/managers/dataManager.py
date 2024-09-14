# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from src.managers.sensorManager import SensorManager
from src.handlers import SensorGroup, Sensor
from src.enums.sensorTypes import STypes
from src.enums.sensorStatus import SGStatus

from loguru import logger


class DataManager:
    def __init__(self):
        # Time
        self.timestamp_list: list = []
        self.timeincr_list: list = []
        # Data
        self.df_raw: pd.DataFrame = pd.DataFrame()
        self.df_calibrated: pd.DataFrame = pd.DataFrame()
        self.df_filtered: pd.DataFrame = pd.DataFrame()
        # Sensor header suffixes
        self.imu_ang_headers: list[str] = ["qx", "qy", "qz", "qw"]
        self.imu_vel_headers: list[str] = ["wx", "wy", "wz"]
        self.imu_acc_headers: list[str] = ["x_acc", "y_acc", "z_acc"]
        # WIP Platform loadcell sensors orientation
        self.forces_sign: dict[str, int] = {
            "X_1": 1,
            "X_2": -1,
            "X_3": -1,
            "X_4": 1,
            "Y_1": 1,
            "Y_2": 1,
            "Y_3": -1,
            "Y_4": -1,
            "Z_1": 1,
            "Z_2": 1,
            "Z_3": 1,
            "Z_4": 1,
        }

    def clearDataFrames(self) -> None:
        self.df_raw: pd.DataFrame = pd.DataFrame()
        self.df_calibrated: pd.DataFrame = pd.DataFrame()
        self.df_filtered: pd.DataFrame = pd.DataFrame()

    # Data load methods

    def loadData(self, time_list: list, sensor_groups: list[SensorGroup]) -> None:
        self.clearDataFrames()
        self.timestamp_list = time_list
        self.timeincr_list = [(t - time_list[0]) / 1000 for t in time_list]
        for group in sensor_groups:
            if not group.getRead():
                continue
            if group.getStatus() == SGStatus.ERROR:
                continue
            for sensor in group.getSensors(only_available=True).values():
                self.df_raw[sensor.getName()] = sensor.getValues()
                slope = sensor.getSlope()
                intercept = sensor.getIntercept()
                self.df_calibrated[sensor.getName()] = [
                    value * slope + intercept for value in sensor.getValues()
                ]

    def isRangedPlot(self, idx1: int, idx2: int) -> bool:
        if idx1 != 0 or idx2 != 0:
            if idx2 > idx1 and idx1 >= 0 and idx2 <= len(self.df_filtered):
                return True
        return False

    # Getters

    def getDataSize(self) -> int:
        return len(self.df_raw)

    def getRawDataframe(self, idx1: int = 0, idx2: int = 0) -> pd.DataFrame:
        return self.formatDataframe(self.df_raw.copy(deep=True), idx1, idx2)

    def getCalibrateDataframe(self, idx1: int = 0, idx2: int = 0) -> pd.DataFrame:
        return self.formatDataframe(self.df_calibrated.copy(deep=True), idx1, idx2)

    def formatDataframe(
        self, df: pd.DataFrame, idx1: int = 0, idx2: int = 0
    ) -> pd.DataFrame:
        timestamp = self.timestamp_list.copy()
        if self.isRangedPlot(idx1, idx2):
            timestamp = timestamp[idx1:idx2]
            df = df.iloc[idx1:idx2]
        # Format dataframe values to 0.000000e+00
        df = df.map("{:.6e}".format)
        # Add timestamp values
        df.insert(0, "timestamp", timestamp)
        return df

    # Data process methods

    # - Sensor methods
    def getForce(self, sensor_name: str, sign: int) -> pd.DataFrame:
        df = self.df_filtered[sensor_name].copy(deep=True)
        df *= sign
        return df

    # - Platform group methods

    # Expected input format: name_1, name_2, name_3, name_4
    # Output: x1, x2, x3, x4
    def getPlatformForces(self, sensor_names: list[str]) -> pd.DataFrame:
        df_list: list[pd.DataFrame] = []
        for sensor_name in sensor_names:
            sign = 1
            for key in self.forces_sign.keys():
                if key in sensor_name:
                    sign = self.forces_sign[key]
                    break
            df_list.append(self.getForce(sensor_name, sign))
        return pd.concat(df_list)

    def getPlatformCOP(
        self, df_fx: pd.DataFrame, df_fy: pd.DataFrame, df_fz: pd.DataFrame
    ) -> tuple[pd.Series, pd.Series]:
        # Platform dimensions
        lx = 508  # mm
        ly = 308  # mm
        h = 20  # mm
        # Get sum forces
        fx = df_fx.sum(axis=1)
        fy = df_fy.sum(axis=1)
        fz = df_fz.sum(axis=1)
        # Operate
        mx = (
            ly
            / 2
            * (
                -df_fz.iloc[:, 0]
                - df_fz.iloc[:, 1]
                + df_fz.iloc[:, 2]
                + df_fz.iloc[:, 3]
            )
        )
        my = (
            lx
            / 2
            * (
                -df_fz.iloc[:, 0]
                + df_fz.iloc[:, 1]
                + df_fz.iloc[:, 2]
                - df_fz.iloc[:, 3]
            )
        )
        # Get COP
        cop_x = (-h * fx - my) / fz
        cop_y = (-h * fy + mx) / fz
        cop_x = cop_x - np.mean(cop_x)
        cop_y = cop_y - np.mean(cop_y)
        return [cop_x, cop_y]

    def getEllipseFromCOP(
        self, cop: tuple[pd.Series, pd.Series]
    ) -> tuple[float, float, float, float]:

        cov_matrix = np.cov(cop[0], cop[1])

        # Eigen vectors and angular rotation
        D, V = np.linalg.eig(cov_matrix)
        theta = np.arctan2(V[1, 0], V[0, 0])

        ellipse_axis = np.sqrt(D)

        # Ellipse params
        a = ellipse_axis[0]
        b = ellipse_axis[1]
        area = np.pi * a * b

        return a, b, theta, area

    # Tare sensors

    def tareSensors(self, sensor_manager: SensorManager, last_values: int) -> None:
        for group in sensor_manager.getGroups(only_available=True):
            for sensor in group.getSensors(only_available=True).values():
                # Only tare loadcells and encoders
                if sensor.getType() not in [
                    STypes.SENSOR_LOADCELL,
                    STypes.SENSOR_ENCODER,
                ]:
                    continue
                # Tare process
                logger.debug(f"Tare sensor {sensor.getName()}")
                slope = sensor.getSlope()
                intercept = sensor.getIntercept()
                calib_values = [
                    value * slope + intercept
                    for value in sensor.getValues()[-last_values:]
                ]
                new_intercept = float(sensor.getIntercept() - np.mean(calib_values))
                logger.debug(f"From {intercept} to {new_intercept}")
                sensor_manager.setSensorIntercept(sensor, new_intercept)

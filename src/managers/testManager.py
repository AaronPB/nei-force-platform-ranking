# -*- coding: utf-8 -*-

from loguru import logger
from src.handlers.sensorGroup import SensorGroup


class TestManager:
    __test__ = False

    def __init__(self) -> None:
        self.sensor_groups: list[SensorGroup]
        self.sensors_connected: bool = False

    # Setters and getters
    def setSensorGroups(self, sensor_groups: list[SensorGroup]) -> None:
        self.sensor_groups = sensor_groups

    def getSensorConnected(self) -> bool:
        return self.sensors_connected

    # Test methods
    def checkConnection(self) -> bool:
        connection_results_list = [
            handler.checkConnections() for handler in self.sensor_groups
        ]
        self.sensors_connected = any(connection_results_list)
        return self.sensors_connected

    def testStart(self) -> None:
        [handler.clearValues() for handler in self.sensor_groups]
        [handler.start() for handler in self.sensor_groups]

    def testRegisterValues(self) -> None:
        [handler.register() for handler in self.sensor_groups]

    def testStop(self) -> None:
        [handler.stop() for handler in self.sensor_groups]

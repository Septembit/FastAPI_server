from pydantic import BaseModel
from typing import Any
from datetime import datetime

class NetworkInfo(BaseModel):
    ID: str
    IP_addr: str
    port: int
    WiFi_ssid: Any
    WiFi_pw: Any
    WiFi_format: Any


class DeviceSettings(BaseModel):
    ID: str
    PLC_IP_addr: Any
    Log_level: int
    Enable: bool
    Location: Any
    GPIO_mode: bool
    Camera_orien: int
    Threshold: int
    Duration: int
    Standby_time: int
    Lang: str
    WiFi_mode: bool
    PLC_mode: bool
    Display_face: bool
    Face_size_ratio: int
    Prevent_photo_auth: int
    WiFi_ssid: Any
    WiFi_pw: Any
    WiFi_format: Any
    IP_addr: str
    GatewayIP_addr: str
    port: str
    Wifi_IP_addr: str

class UserInfo(BaseModel):
    ID: str
    User_ID: Any
    RFID_code: str
    Name: str
    Department: Any
    Rank: int
    Enabled: bool
    image: Any


class DeleteUserInfo(BaseModel):
    ID: str
    User_ID: str


class DeleteDeviceInfo(BaseModel):
    ID: str


class AliveStatusInfo(BaseModel):
    alive: bool


class ConnectStatusInfo(BaseModel):
    ID: str
    status: bool


class DateInfo(BaseModel):
    ID: str
    date: str


class DeviceSyncRequest(BaseModel):
    ID: str
    Update_datetime: str
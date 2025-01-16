from fastapi import FastAPI, Response
import uvicorn
import shutil
import os
from fastapi.responses import FileResponse
import argparse
import tempfile
import zipfile
import yaml
from state import *
import logging
import base64
import csv
from datetime import datetime
import subprocess

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)
data_path = config["data_path"]


# Initial data
network_info = NetworkInfo(
    ID="0", IP_addr="127.0.0.1", port="8000", WiFi_ssid="", WiFi_pw="", WiFi_format=""
)

user_info = UserInfo(
    ID="0",
    User_ID="1234",
    RFID_code="12",
    Name="David",
    Department="123",
    Rank=1,
    Enabled=True,
    image="qerwe",
)

device_settings = DeviceSettings(
    ID="0",
    PLC_IP_addr="0.0.0.0",
    Log_level=1,
    Enable=True,
    Location="Door",
    GPIO_mode=True,
    Camera_orien=1,
    Threshold=40,
    Duration=10,
    Standby_time=10,
    Lang="en",
    WiFi_ssid="",
    WiFi_pw="",
    WiFi_format="",
    IP_addr="127.0.0.1",
    port="8000",
    WiFi_mode=True,
    PLC_mode=True,
    Display_face=True,
    Face_size_ratio=60,
    Prevent_photo_auth=1,
    Wifi_IP_addr="0.0.0.0",
    GatewayIP_addr="0.0.0.0",
)

delete_user_info = DeleteUserInfo(ID="0", User_ID="1234")

delete_device_info = DeleteDeviceInfo(
    ID="0",
)
alive_status_info = AliveStatusInfo(alive=True)
connect_status_info = ConnectStatusInfo(ID="0", status=True)
app = FastAPI()


# update and get alive status
@app.put("/api/device/alive")
async def update_alive_status(new_alive: AliveStatusInfo):
    global alive_status_info
    alive_status_info = new_alive
    return {"result": 1}


@app.get("/api/device/alive")
async def get_alive_status():
    return {"result": 0}


# update and get status
@app.put("/api/device/status")
async def update_device_status(new_connect: ConnectStatusInfo):
    global connect_status_info
    connect_status_info = new_connect
    return {"result": 1}


@app.get("/api/device/status")
async def get_device_status(ID: str):
    return {"result": 0}


# upload and get log files.
@app.get("/api/log/list")
async def get_log_file(ID: str, date: str, response: Response):
    global data_path
    LOG_DIR = os.path.expanduser(os.path.join(data_path, ID, "log"))
    try:
        filenames = get_files_after_date(LOG_DIR, date)
        return {"filename": filenames, "result": 0}
    except Exception as e:
        logging.error(f"Error processing request get {ID}: {e}")
        response.status_code = 500
        return {"error": e, "result": 1}


@app.get("/api/file")
async def get_file(ID: str, file_path: str):
    global data_path
    file_path = os.path.expanduser(os.path.join(data_path, ID, "log", file_path))
    return FileResponse(file_path)


@app.get("/api/log/files")
async def get_log_files(ID: str, file_list: list):
    try:
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=True) as temp_zip:
            with zipfile.ZipFile(temp_zip.name, "w") as zipf:
                for file in file_list:
                    if file.endswith(".log"):
                        date, _ = os.path.splitext(file)
                        file_name = os.path.join("dev-id_", date, ".log")
                        LOG_DIR = os.path.join("logfiles", ID, "log")
                        file_path = os.path.join(LOG_DIR, file_name)
                        zipf.write(file_path, arcname=file_name)
                    else:
                        IMAGE_DIR = os.path.join(ID, "image")
                        file_path = os.path.join(IMAGE_DIR, file)
                        zipf.write(file_path, arcname=file)
            return {"files": FileResponse(temp_zip.name, filename=os.path.basename(temp_zip.name)), "result": 0}
    except Exception as e:
        logging.error(f"Error processing request get {ID}: {e}")
        return {"error": e, "result": 1}


# get and update network information
@app.put("/api/device/network")
async def update_network_info(new_info: DeviceSettings):
    global device_settings, data_path
    device_settings = new_info

    ID_folder_path = os.path.expanduser(os.path.join(data_path, device_settings.ID))
    if not os.path.exists(ID_folder_path):
        os.makedirs(ID_folder_path)
    if not os.path.exists(os.path.join(ID_folder_path, "log")):
        os.makedirs(os.path.join(ID_folder_path, "log"))
    if not os.path.exists(os.path.join(ID_folder_path, "dataset")):
        os.makedirs(os.path.join(ID_folder_path, "dataset"))
    csv_file = os.path.join(ID_folder_path, "dataset", "users.csv")
    if not os.path.exists(csv_file):
        open(csv_file, "w").close()
    config_file_name = "config_" + device_settings.ID + ".yaml"
    config_file = os.path.expanduser(os.path.join(data_path, config_file_name))
    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            yaml.safe_dump(device_settings.dict(), f)
    else:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
            data.update(device_settings.dict())
        with open(config_file, "w") as file:
            yaml.safe_dump(data, file)

    return {"result": 0}


@app.get("/api/device/network", response_model=NetworkInfo)
async def get_network_info():
    return network_info


# update and get device settings
@app.put("/api/device/settings")
async def update_device_settings(new_settings: DeviceSettings):
    global device_settings, data_path
    device_settings = new_settings
    ID_folder_path = os.path.expanduser(os.path.join(data_path, device_settings.ID))
    if not os.path.exists(ID_folder_path):
        os.makedirs(ID_folder_path)
    config_file_name = "config_" + device_settings.ID + ".yaml"
    config_file = os.path.expanduser(os.path.join(data_path, config_file_name))

    if not os.path.exists(config_file):
        with open(config_file, "w") as f:
            yaml.safe_dump(device_settings.dict(), f)
    else:
        with open(config_file, "r") as f:
            data = yaml.safe_load(f)
            data.update(device_settings.dict())
        with open(config_file, "w") as file:
            yaml.safe_dump(data, file)

    return {"result": 0}


@app.get("/api/device/settings", response_model=DeviceSettings)
async def get_device_settings():
    return device_settings


# update and get user information
@app.put("/api/users")
async def update_user_info(new_infos: Any):
    global user_info, data_path
    try:
        for new_info in new_infos:
            user_info = new_info
            ID_folder_path = os.path.expanduser(os.path.join(data_path, user_info.ID))
            User_ID_folder_path = os.path.join(ID_folder_path, "dataset", user_info.User_ID)
            if not os.path.exists(User_ID_folder_path):
                os.makedirs(User_ID_folder_path)
            # save image
            encoded_image = user_info.image
            decoded_image = base64.b64decode(encoded_image)

            with open(os.path.join(User_ID_folder_path, user_info.User_ID) + ".jpg", "wb") as f:
                f.write(decoded_image)
            config_file = os.path.join(User_ID_folder_path, user_info.User_ID) + ".yaml"
            user_info.image = os.path.join(User_ID_folder_path, user_info.User_ID) + ".jpg"
            csv_file = os.path.join(ID_folder_path, "dataset", "users.csv")
            csv_data = [
                {
                    "User_ID": user_info.User_ID,
                    "Name": user_info.Name,
                    "RFID_code": user_info.RFID_code,
                    "Department": user_info.Department,
                    "Rank": user_info.Rank,
                }
            ]
            save_to_csv(csv_file, csv_data)
            if not os.path.exists(config_file):
                with open(config_file, "w") as f:
                    yaml.dump(user_info.dict(), f)
            else:
                with open(config_file, "r") as f:
                    data = yaml.safe_load(f)
                    data.update(user_info.dict())
                with open(config_file, "w") as file:
                    yaml.safe_dump(data, file)

        return {"result": 0}
    except Exception as e:
        return {"result": 1, "error": e}


@app.get("/api/users", response_model=UserInfo)
async def get_user_info():
    return user_info


# delete user information
@app.put("/api/users/{ID}/{user_id}")
async def delete_user_info(ID: str, User_ID: str):
    global data_path
    try:
        user_path = os.path.expanduser(os.path.join(data_path, ID, "dataset", User_ID))
        shutil.rmtree(user_path)
        csv_file = os.path.expanduser(
            os.path.join(data_path, ID, "dataset", "users.csv")
        )
        csv_delete_row(csv_file, User_ID)
        return {"result": 0}
    except Exception as e:
        print(f"Error deleting user data: {e}")
        return {"result": 1, "error": e}  


@app.put("/api/device")
async def delete_device_info(ID: str):
    global data_path
    try:
        ID_folder_path = os.path.expanduser(os.path.join(data_path, ID))
        shutil.rmtree(ID_folder_path)
        os.remove(os.path.expanduser(os.path.join(data_path, "config_" + ID + ".yaml")))
        return {"result": 0}
    except Exception as e:
        print(e)
        return {"result": 1, "error": e}


@app.put("/api/device/sync_clock")
async def sync_clock(request: DeviceSyncRequest):
    result = sync_device_clock(request.ID, request.Update_datetime)
    return result

@app.put("/api/device/reboot")
async def reboot(ID: str):
    result = {"result": 0}
    return result

def save_to_csv(file_name, new_data):
    file_exists = os.path.isfile(file_name)
    fieldnames = ["User_ID", "Name", "RFID_code", "Department", "Rank"]
    if not file_exists:
        with open(file_name, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(new_data)
    else:
        existing_data = []
        with open(file_name, mode="r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file, fieldnames=fieldnames)
            existing_data = list(reader)
        existing_ids = {row["User_ID"]: row for row in existing_data}

        for data in new_data:
            if data["User_ID"] in existing_ids:
                existing_ids[data["User_ID"]].update(data)
            else:
                existing_ids[data["User_ID"]] = data

        with open(file_name, mode="w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writerows(existing_ids.values())


def get_files_after_date(folder_path, date_str):
    target_date = datetime.strptime(date_str, "%Y-%m-%d")
    log_files = [
        f
        for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and f.endswith(".log")
    ]

    result_files = [
        f for f in log_files if datetime.strptime(f[:-4], "%Y-%m-%d") >= target_date
    ]

    return result_files


def csv_delete_row(input_file, User_ID):
    input_output_file = input_file
    fieldnames = ["User_ID", "Name", "RFID_code", "Department", "Rank"]

    temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)

    with open(input_output_file, mode="r", newline="") as csvfile, temp_file:
        reader = csv.DictReader(csvfile, fieldnames=fieldnames)
        writer = csv.DictWriter(temp_file, fieldnames=fieldnames)
        for row in reader:
            if row["User_ID"] != User_ID:
                writer.writerow(row)
    shutil.move(temp_file.name, input_output_file)


def sync_device_clock(ID: str, update_datetime: datetime):
    try:
        command = f"sudo date -s '{update_datetime.strftime('%Y-%m-%d %H:%M:%S')}'"
        subprocess.run(command, shell=True, check=True)
        return {"result": 0}  
    except Exception as e:
        print(f"Error syncing device clock: {e}")
        return {"result": 1}  

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", type=str, help="ip address.")
    ap.add_argument("--port", type=int, help="port number")
    args = vars(ap.parse_args())
    print(args)
    uvicorn.run("fastapi_server:app", host=args["host"], port=args["port"])
import asyncio
from io import BytesIO
from PIL import Image
import logging
import time
import subprocess

from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform
from control.frame_server import FrameServer

import socketio
from v4l2py.device import Device, VideoCapture

from utils.ReadConfig import ReadConfig,JsonToString,ReadConfig2CapProp
from utils.FileManager import MyReadFile,MyWriteFile,ScanFile,DeleteAllFileInFolder
from model.capture_prop import CaptureProp
from API.APIUpload import upload
from control.socketio_manager import SocketIoManager

captureProp=ReadConfig2CapProp(MyReadFile('config.txt'))
sio=socketio.AsyncClient()
sioManager=SocketIoManager(captureProp,sio)
async def checkSocketIOConnect():
    while True:        
        try:
            if sioManager.isConnect==False and sioManager.isCapturing==False:
                #await sioManager.sio.connect(captureProp.serverUrl)
                await sioManager.sio.connect(url=captureProp.serverUrl,wait=True,wait_timeout=60)
                await sioManager.sio.wait()
            await asyncio.sleep(1)
        except:
            print("Fail to connect socketio server")
            await asyncio.sleep(2)  


#################################################################################
#MAIN
async def main():
    fmt = "%(threadName)-10s %(asctime)-15s %(levelname)-5s %(name)s: %(message)s"
    logging.basicConfig(level="INFO", format=fmt)
    asyncio.create_task(checkSocketIOConnect())
    

try:
    asyncio.run(main())
except KeyboardInterrupt:
    logging.info("Ctrl-C pressed. Bailing out")

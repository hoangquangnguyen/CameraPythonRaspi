import asyncio
import socketio

from utils.ReadConfig import ReadConfig,JsonToString
from utils.FileManager import MyReadFile,MyWriteFile,DeleteAllFileInFolder
from control.upload_controller import UploadController
from model.capture_prop import CaptureProp
from control.capture_controller import raspiCamCapture,cameraCapture

class SocketIoManager:
    def __init__(self,captureProp:CaptureProp,sio):
        self.captureProp=captureProp
        self.isConnect = False
        self.isCapturing=False
        self.sio=sio

        #region event
        @self.sio.event
        async def connect():
            self.isConnect=True
            await self.sio.emit("u_send_info", {"deviceos":"udevice","devicename":self.captureProp.deviceName,"camid":self.captureProp.camId,"focus":self.captureProp.focus})
            print('connection established')

        @self.sio.event
        async def server_request_u_update_device_info(data):
            try:
                print(data)
                self.captureProp.deviceName=data['devicename']
                self.captureProp.camId=data['camid']
                self.captureProp.focus=data['focus']
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
                await self.sio.emit("u_send_info", {"deviceos":"udevice","devicename":self.captureProp.deviceName,"camid":self.captureProp.camId,"focus":self.captureProp.focus})
            except:
                print("err")

        @self.sio.event
        async def server_request_u_change_resolution(data):
            try:
                self.captureProp.rWidth=data['resW']
                self.captureProp.rHeight=data['resH']
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
            except:
                print("err")

        @self.sio.event
        async def server_request_u_change_interval(data):
            try:
                self.captureProp.captureInterval=data
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
            except:
                print("err")   

        @self.sio.event
        async def server_request_u_change_wait_time(data):
            try:
                self.captureProp.waitTime=data
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
            except:
                print("err") 

        @self.sio.event
        async def server_request_u_change_capture_time(data):
            try:
                self.captureProp.captureTime=data
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
            except:
                print("err")

        @self.sio.event
        async def server_request_u_change_focus(data):
            try:
                self.captureProp.focus=data
                #MyWriteFile('config.txt',JsonToString(jsonConfig))
            except:
                print("err")

        @self.sio.event
        async def server_request_u_upload(data):
            uc=UploadController()
            asyncio.create_task(uc.uploadToServer(self.sio,self.captureProp.serverUrl,self.captureProp.deviceName,data))

        @self.sio.event
        async def server_request_u_capture(data):
            await DeleteAllFileInFolder("./img")
            asyncio.create_task(cameraCapture(self.sio,self.captureProp))

        @self.sio.event
        async def disconnect():
            self.isConnect=False
            print('disconnected from server')


        @self.sio.event
        async def connect_error(data):
            self.isConnect=False
            print("The connection failed!")
        #endregion event
    



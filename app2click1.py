import asyncio
from io import BytesIO
from PIL import Image
import logging
import time
from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform
import socketio

from utils.ReadConfig import ReadConfig,JsonToString,ReadConfig2CapProp
from utils.FileManager import MyReadFile,MyWriteFile,ScanFile,DeleteAllFileInFolder
from utils.socketio_key_enum import SocketIOKey

from API.APIUpload import upload

isConnect=False
isCapturing=False
sio = socketio.AsyncClient()
jsonConfig=ReadConfig(MyReadFile('config.txt'))
config=ReadConfig2CapProp(jsonConfig)
myCount=0
#region EVENT
@sio.event
async def connect():
    global isConnect
    isConnect=True
    await sio.emit(SocketIOKey.u_send_info.value, 
                {"deviceos":"udevice",
                 "devicename":config.deviceName
                 ,"camid":config.camId
                 ,"focus":config.focus})
    print('connection established')

@sio.event
async def server_request_u_update_device_info(data):
    SocketIOKey.server_request_u_update_device_info
    try:
        print(data)
        config.deviceName=data['devicename']
        config.camId=data['camid']
        config.focus=data['focus']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
        await sio.emit(SocketIOKey.u_send_info.value, 
                {"deviceos":"udevice",
                 "devicename":config.deviceName
                 ,"camid":config.camId
                 ,"focus":config.focus})
    except:
        print("err")

@sio.event
async def server_request_u_delete_image(data):
    SocketIOKey.server_request_u_delete_image
    try:  
        await DeleteAllFileInFolder("img")
    except:
        print("err")

@sio.event
async def server_request_u_change_config(data):
    SocketIOKey.server_request_u_change_config
    try:
        jsonConfig['rWidth']=data['resW']
        jsonConfig['rHeight']=data['resH']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

@sio.event
async def server_request_u_onoff_camera(data):
    SocketIOKey.server_request_u_onoff_camera
    if(data==1):
        try:        
            #setting camera
            global picam0 
            global picam1
            global capture_config
            global capture_config1

            picam0=Picamera2(0)       
            picam1=Picamera2(1)
            
            rWidth=config.rWidth
            rHeigth=config.rHeight
            capture_config = picam0.create_still_configuration(
                main={"size": (rWidth,rHeigth)},
                queue=True) #transform=Transform(vflip=True),
            picam0.options["quality"] = 95
            picam0.options["compress_level"] = 5

            capture_config1 = picam1.create_still_configuration(
                main={"size": (rWidth,rHeigth)},       
                queue=True) 
            picam1.options["quality"] = 95
            picam1.options["compress_level"] = 5

            picam0.start(config=capture_config,show_preview=False)
            picam1.start(config=capture_config1,show_preview=False)
            settings={}
            #focus
            settings["AfMode"]=controls.AfModeEnum.Continuous
            settings["AfRange"]=controls.AfRangeEnum.Normal
            settings["AfMetering"]=controls.AfMeteringEnum.Auto
            #white balance
            settings["AwbEnable"]=True
            settings["AwbMode"]=controls.AwbModeEnum.Auto
            #settings["ExposureValue"]=0
            #settings["Sharpness"]=0
            settings["FrameRate"]=56
            settings["HdrMode"]=controls.HdrModeEnum.SingleExposure
            #
            # Give time for Aec and Awb to settle, before disabling them
            time.sleep(1)
            picam0.set_controls(settings)
            picam1.set_controls(settings)
            # And wait for those settings to take effect
            time.sleep(1)
        except:
            print("err on camera")
    else:
        try:
            picam0.stop()
            picam0.close()
            picam1.stop()
            picam1.close()
        except:
            print("err off camera")


@sio.event
async def server_request_u_upload(data):
    asyncio.create_task(uploadToServer(jsonConfig['Server'],jsonConfig['DeviceName'],data))   

@sio.event
async def server_request_u_capture(data):
    asyncio.create_task(cameraCapture())

@sio.event
async def disconnect():
    global isConnect
    isConnect=False
    print('disconnected from server')

@sio.event
async def connect_error(data):
    global isConnect
    isConnect=False
    print("The connection failed!")
#endregion


async def checkSocketIOConnect():
    while True:        
        try:
            if isConnect==False and isCapturing==False:
                print("try reconnect1")
                await sio.connect(url=jsonConfig['Server'],wait=True,wait_timeout=60)
                print("try reconnect2")
                #await sio.wait()
                #print("try reconnect3")
            await asyncio.sleep(1)
        except:
            print("Unclosed client session")           
        finally:
            await asyncio.sleep(2)  
            
async def saveImage(frame,x,camid):
    #buff = BytesIO(bytes(frame))
    imgPath="img/"+jsonConfig['DeviceName']+"_"+str(camid)+'_'+str(x)+".jpeg"
    image = Image.fromarray(frame)
    image.save(imgPath,bitmap_format='bmp',quality=100,optimize=False,compression_level=0)

async def uploadToServer(server,devicename,folderName):
    allfile=ScanFile("img")
    myUrl =server+"/multiple-upload"
    i=0
    while i<len(allfile):
        if i+3<len(allfile):
            manyFiles=[("many-files",open('img/'+str(allfile[i]),'rb')),("many-files",open('img/'+str(allfile[i+1]),'rb')),("many-files",open('img/'+str(allfile[i+2]),'rb'))]
            await upload(myUrl,manyFiles,devicename,folderName)
            i=i+3
        else:
            await upload(myUrl,[("many-files",open('img/'+str(allfile[i]),'rb'))],devicename,folderName)
            i=i+1
        await asyncio.sleep(0.01) 
    print("upload complete")       
    await sio.emit("u_upload_complete", "nodata")
    

#region caprure image
async def cameraCapture():
    global myCount
    isCapturing=False
    isStartRaspi=False
    isStartRaspi=True
    #region loop get frame 
    isCapturing=True
    await sio.emit(SocketIOKey.u_start_capture.value, "nodata")
    frame0 = picam0.capture_array()
    frame1 = picam1.capture_array()
    #endregion loop get frame
    await asyncio.sleep(0.1)
    await sio.emit(SocketIOKey.u_capture_complete.value, "nodata")
    await asyncio.create_task(saveImage(frame0,myCount,0))
    await asyncio.create_task(saveImage(frame1,myCount,1))
    myCount+=1
    isCapturing=False
    await asyncio.sleep(0.1)
    await sio.emit(SocketIOKey.u_save_image_complete.value, "nodata")
#endregion capture image

#################################################################################
#MAIN
    
if __name__ == '__main__':
    try:
        fmt = "%(threadName)-10s %(asctime)-15s %(levelname)-5s %(name)s: %(message)s"
        logging.basicConfig(level="INFO", format=fmt)
        asyncio.run(checkSocketIOConnect())
    except KeyboardInterrupt:
        logging.info("Ctrl-C pressed. Bailing out")


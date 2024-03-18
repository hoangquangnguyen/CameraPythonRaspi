import asyncio
import socketio
from PIL import Image
import logging
import time

from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform

from utils.ReadConfig import ReadConfig,JsonToString,ReadConfig2CapProp,ConfigToString
from utils.FileManager import MyReadFile,MyWriteFile,ScanFile,DeleteAllFileInFolder
from utils.socketio_key_enum import SocketIOKey

from API.APIUpload import upload

global isConnect
global isCapturing
isConnect=False
isCapturing=False
sio = socketio.AsyncClient()
jsonConfig=ReadConfig(MyReadFile('config.txt'))
config=ReadConfig2CapProp(jsonConfig)
myCount=0
global picam0
picam0=Picamera2()
picam0.stop()
picam0.close()
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
        config.rWidth=data['rWidth']
        config.rHeight=data['rHeight']
        config.captureInterval=data['captureInterval']
        config.captureTime=data['captureTime']
        config.waitTime=data['waitTime']

        MyWriteFile('config.txt',ConfigToString(config))
    except:
        print("err")

@sio.event
async def server_request_u_onoff_camera(data):
    SocketIOKey.server_request_u_onoff_camera
    if(data==1):
        try:        
            #setting camera
            global picam0 
            global capture_config
            picam0=Picamera2() 
            
            rWidth=config.rWidth
            rHeigth=config.rHeight
            capture_config = picam0.create_still_configuration(
                main={"size": (rWidth,rHeigth)},
                queue=True) #transform=Transform(vflip=True),
            picam0.options["quality"] = 95
            picam0.options["compress_level"] = 5

            picam0.start(config=capture_config,show_preview=False)
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
            # And wait for those settings to take effect
            time.sleep(1)
        except:
            print("err on camera")
    else:
        try:
            picam0.stop()
            picam0.close()
        except:
            print("err off camera")

@sio.event
async def server_request_u_upload(data):
    asyncio.create_task(uploadToServer(config.serverUrl,config.deviceName,data))   

@sio.event
async def server_request_u_capture(data):
    await DeleteAllFileInFolder("img")
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
                await sio.connect(url=config.serverUrl,wait=True,wait_timeout=60)
                #await sio.wait()
                #print("try reconnect3")
            await asyncio.sleep(1)
            await sio.emit(SocketIOKey.u_camera_status.value,picam0.is_open)
        except Exception as ex:
            print(ex)
            print("Unclosed client session")           
            await asyncio.sleep(1)           
        finally:
            await asyncio.sleep(2)  
            
async def saveImage(frame,x,camid):
    #buff = BytesIO(bytes(frame))
    imgPath="img/"+config.deviceName+"_"+str(camid)+'_'+str(x)+".jpeg"
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
    isCapturing=False
    isStartRaspi=False
    waittime=config.waitTime
    capInterval=config.captureInterval
    captureTime=config.captureTime
    isStartRaspi=True
    dataimg0=[]
    startI=0
    if picam0.is_open:
        #region loop get frame 
        await asyncio.sleep(waittime)
        isCapturing=True
        start = time.monotonic()
        await sio.emit(SocketIOKey.u_start_capture.value, "nodata")
        while isStartRaspi==True:
            new = time.monotonic()
            await asyncio.sleep(0.01)
            elapsed = (new - start)*1000   
            if elapsed <= captureTime*1000 :
                frame0 = picam0.capture_array()                      
                if capInterval>0:
                    if(elapsed-startI>=capInterval*1000):
                        dataimg0.append(frame0)
                        startI=elapsed
                else:
                    dataimg0.append(frame0)
            else:
                isStartRaspi=False
        #endregion loop get frame
        await asyncio.sleep(0.1)
        await sio.emit(SocketIOKey.u_capture_complete.value, "nodata")
        for i in range(0,len(dataimg0)):
            await asyncio.create_task(saveImage(dataimg0.pop(0),i,0))
            #await saveImage(dataimg[i],i)
        dataimg0.clear()
        isCapturing=False
        await asyncio.sleep(0.1)
        await sio.emit(SocketIOKey.u_save_image_complete.value, "nodata")
    else:
        await sio.emit(SocketIOKey.u_start_capture.value, "nocap")
        await asyncio.sleep(0.1)
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
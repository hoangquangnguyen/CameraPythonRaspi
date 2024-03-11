import asyncio
from io import BytesIO
from PIL import Image
import logging
import time
from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform
import socketio

from utils.ReadConfig import ReadConfig,JsonToString
from utils.FileManager import MyReadFile,MyWriteFile,ScanFile,DeleteAllFileInFolder

from API.APIUpload import upload

global isConnect
global isCapturing
isConnect=False
isCapturing=False
sio = socketio.AsyncClient()
jsonConfig=ReadConfig(MyReadFile('config.txt'))
myCount=0
#region EVENT
@sio.event
async def connect():
    global isConnect
    isConnect=True
    await sio.emit("u_send_info", {"deviceos":"udevice","devicename":jsonConfig['DeviceName'],"camid":jsonConfig['CamId'],"focus":jsonConfig['Focus']})
    print('connection established')

@sio.event
async def server_request_u_update_device_info(data):
    try:
        print(data)
        jsonConfig['DeviceName']=data['devicename']
        jsonConfig['CamId']=data['camid']
        jsonConfig['Focus']=data['focus']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
        await sio.emit("u_send_info", {"deviceos":"udevice","devicename":jsonConfig['DeviceName'],"camid":jsonConfig['CamId'],"focus":jsonConfig['Focus']})
    except:
        print("err")

@sio.event
async def server_request_u_change_resolution(data):
    try:
        jsonConfig['rWidth']=data['resW']
        jsonConfig['rHeight']=data['resH']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
        await DeleteAllFileInFolder("img")
    except:
        print("err")

@sio.event
async def server_request_u_change_interval(data):
    try:
        jsonConfig['Interval']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
            #setting camera
        global picam0 
        picam0=Picamera2()
        global capture_config
        rWidth=jsonConfig['rWidth']
        rHeigth=jsonConfig['rHeight']
     
        capture_config = picam0.create_still_configuration(
            raw={}, display=None,
            main={"size": (rWidth,rHeigth)},
            queue=True) #transform=Transform(vflip=True),
        # picam0.options["quality"] = 95
        # picam0.options["compress_level"] = 5

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
        #settings["HdrMode"]=controls.HdrModeEnum.SingleExposure
        #
        # Give time for Aec and Awb to settle, before disabling them
        time.sleep(1)
        picam0.set_controls(settings)
        # And wait for those settings to take effect
        time.sleep(1)
    except:
        print("err")   

@sio.event
async def server_request_u_change_wait_time(data):
    try:
        jsonConfig['WaitTime']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
        picam0.stop()
        picam0.close()
    except:
        print("err") 

@sio.event
async def server_request_u_change_capture_time(data):
    try:
        jsonConfig['CaptureTime']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

@sio.event
async def server_request_u_change_focus(data):
    try:
        jsonConfig['Focus']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

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
    isStartRaspi=True
    #region loop get frame 
    isCapturing=True
    await sio.emit("u_start_capture", "nodata")
    # capture_config = picam0.create_still_configuration(raw={"size":(4608,2592)}, display=None,controls={"AfMode": controls.AfModeEnum.Continuous})
    # r = picam0.switch_mode_capture_request_and_stop(capture_config)
    # r.save_dng("img/full1.dng")
    frame0 = picam0.capture_array()
    
    #endregion loop get frame
    await asyncio.sleep(0.1)
    await sio.emit("u_capture_complete", "nodata")
    await asyncio.create_task(saveImage(frame0,myCount,0))
    myCount+=1
    isCapturing=False
    await asyncio.sleep(0.1)
    await sio.emit("u_save_image_complete", "nodata")
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


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

isConnect=False
isCapturing=False
sio = socketio.AsyncClient()
jsonConfig=ReadConfig(MyReadFile('config.txt'))

#region EVENT
@sio.event
async def connect():
    global isConnect
    isConnect=True
    await sio.emit("u_send_info", {"deviceos":"udevice","devicename":jsonConfig['devicename'],"camid":jsonConfig['camid'],"focus":jsonConfig['focus']})
    print('connection established')

@sio.event
async def server_request_u_update_device_info(data):
    try:
        print(data)
        jsonConfig['devicename']=data['devicename']
        jsonConfig['camid']=data['camid']
        jsonConfig['focus']=data['focus']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
        await sio.emit("u_send_info", {"deviceos":"udevice","devicename":jsonConfig['devicename'],"camid":jsonConfig['camid'],"focus":jsonConfig['focus']})
    except:
        print("err")

@sio.event
async def server_request_u_change_resolution(data):
    try:
        jsonConfig['resW']=data['resW']
        jsonConfig['resH']=data['resH']
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

@sio.event
async def server_request_u_change_interval(data):
    try:
        jsonConfig['interval']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")   

@sio.event
async def server_request_u_change_wait_time(data):
    try:
        jsonConfig['waittime']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err") 

@sio.event
async def server_request_u_change_capture_time(data):
    try:
        jsonConfig['capturetime']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

@sio.event
async def server_request_u_change_focus(data):
    try:
        jsonConfig['focus']=data
        MyWriteFile('config.txt',JsonToString(jsonConfig))
    except:
        print("err")

@sio.event
async def server_request_u_upload(data):
    asyncio.create_task(uploadToServer(jsonConfig['server'],jsonConfig['devicename'],data))

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
                print("try reconnect1")
                await sio.connect(url=jsonConfig['server'],wait=True,wait_timeout=60)
                print("try reconnect2")
                #await sio.wait()
                #print("try reconnect3")
            await asyncio.sleep(1)
        except:
            print("Unclosed client session")           
        finally:
            await asyncio.sleep(2)  
            
async def saveImage(frame,x):
    #buff = BytesIO(bytes(frame))
    imgPath="img/"+jsonConfig['devicename']+'_'+str(x)+".jpeg"
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
    waittime=jsonConfig['waittime']
    rWidth=jsonConfig['resW']
    rHeigth=jsonConfig['resH']
    capInterval=jsonConfig['interval']
    captureTime=jsonConfig['capturetime']
    #config Raspi
    picam0 = Picamera2(0)
        #setting camera
    capture_config = picam0.create_still_configuration(
        main={"size": (rWidth,rHeigth)},
        transform=Transform(vflip=True),
        queue=True,
        controls={"AfMode": controls.AfModeEnum.Continuous,"Brightness":0.05}) 
    picam0.set_controls({"FrameRate": 56})
    picam0.options["quality"] = 95
    picam0.options["compress_level"] = 0

    picam0.start(config=capture_config,show_preview=False)
    #
    isStartRaspi=True
    dataimg0=[]
    
    startI=0
    #region loop get frame 
    await asyncio.sleep(waittime)
    isCapturing=True
    start = last = time.monotonic()
    await sio.emit("u_start_capture", "nodata")
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
    await sio.emit("u_capture_complete", "nodata")
    for i in range(0,len(dataimg0)):
        await asyncio.create_task(saveImage(dataimg0[i],i))
        #await saveImage(dataimg[i],i)
    dataimg0.clear()
    isCapturing=False
    await asyncio.sleep(0.1)
    await sio.emit("u_save_image_complete", "nodata")
    picam0.stop()
    picam0.close()
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


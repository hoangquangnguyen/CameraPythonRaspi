from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform
from control.frame_server import FrameServer
from model.capture_prop import CaptureProp
import time
import asyncio
import numpy as np
from utils.FileManager import saveImageFromArray

async def raspiCamCapture(capProps:CaptureProp):
    isCapturing=False  
        #region get Frame
    picam2 = Picamera2()
        #setting camera
    capture_config = picam2.create_still_configuration(
        main={"size": (capProps.rWidth,capProps.rHeight)},
        transform=Transform(vflip=True),
        queue=True,
        controls={"AfMode": controls.AfModeEnum.Continuous,"Brightness":0.05}) 
    picam2.set_controls({"FrameRate": 56})
    picam2.options["quality"] = 95
    picam2.options["compress_level"] = 3

    server = FrameServer(picam2)
    server.start()
    picam2.start(config=capture_config,show_preview=False)

async def cameraCapture(sioManager,capProps:CaptureProp):
    isCapturing=False
    isStartRaspi=False
    #config Raspi
    picam2 = Picamera2()
        #setting camera
    capture_config = picam2.create_still_configuration(
        main={"size": (capProps.rWidth,capProps.rHeight)},
        transform=Transform(vflip=True),
        queue=True,
        controls={"AfMode": controls.AfModeEnum.Continuous,"Brightness":0.05}) 
    picam2.set_controls({"FrameRate": 56})
    picam2.options["quality"] = 95
    picam2.options["compress_level"] = 0

    picam2.start(config=capture_config,show_preview=False)
    #
    isStartRaspi=True
    dataimg=[]
    start = time.monotonic()
    startI=0
    await asyncio.sleep(capProps.waitTime)
    await sioManager.emit("u_start_capture", "nodata")
    print("u_start_capture")
    isCapturing=True
    #region loop get frame 
    start = time.monotonic()
    while isStartRaspi==True:
        new = time.monotonic()
        elapsed = (new - start)*1000
        if elapsed <= capProps.captureTime*1000 :  
            frame = picam2.capture_array()                     
            if capProps.captureInterval>0:
                if(elapsed-startI>=capProps.captureInterval*1000):
                    dataimg.append(frame)
                    startI=elapsed
            else:
                dataimg.append(frame)
        else:
            isStartRaspi=False
            break
        await asyncio.sleep(0.01)

    #endregion loop get frame
    await asyncio.sleep(0.01)
    await sioManager.emit("u_capture_complete", "nodata")  
    print("u_capture_complete")      
    for i in range(0,len(dataimg)):
        imgPath="./img/"+"cam"+str(capProps.camId)+"img"+str(i)+".jpg"
        await saveImageFromArray(dataimg[i],imgPath)
    dataimg.clear()
    isCapturing=False  
    #await sioManager.sio.emit("u_save_image_complete", "nodata")
    await asyncio.sleep(0.01)
    await sioManager.emit("u_save_image_complete", "nodata")
    picam2.stop()
    picam2.close()
            
    
        
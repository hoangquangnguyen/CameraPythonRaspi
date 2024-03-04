import time
from threading import Condition, Thread
import asyncio
from io import BytesIO
from PIL import Image

from model.capture_prop import CaptureProp
from picamera2 import Picamera2

class FrameServer:
    def __init__(self, picam2:Picamera2, stream='main',captureprop=CaptureProp()):
        """A simple class that can serve up frames from one of the Picamera2's configured streams to multiple other threads.

        Pass in the Picamera2 object and the name of the stream for which you want
        to serve up frames.
        """
        self._picam2 = picam2
        self._stream = stream
        self._props=captureprop
        self._array = None
        self._condition = Condition()
        self._running = True
        self._count = 0
        self._frames=[]
        self._thread = Thread(target=self._thread_func, daemon=True)
    
    def saveImage(self,frame,x,deviceID):
        #buff = BytesIO(bytes(frame)) 
        image = Image.fromarray(frame)
        image.save("img/"+self._props.deviceName+'_'+str(x)+".jpeg",bitmap_format='bmp',quality=100,optimize=False,compression_level=0)

    @property
    def count(self):
        """A count of the number of frames received."""
        return self._count
    @property
    def frames(self):
        """ Frames received."""
        return self._frames
    def start(self):
        """To start the FrameServer, you will also need to start the Picamera2 object."""
        self._thread.start()

    def stop(self):
        """To stop the FrameServer

        First stop any client threads (that might be
        blocked in wait_for_frame), then call this stop method. Don't stop the
        Picamera2 object until the FrameServer has been stopped.
        """
        self._running = False
        self._thread.join()

    def _thread_func(self):
    #region thread_func
        start = time.monotonic()
        startI=0
        while self._running:
        #loop capture frame           
            array = self._picam2.capture_array(self._stream)
            new = time.monotonic()
            elapsed = (new - start)*1000
            if elapsed >= self._props.waitTime*1000 :
            #start capture after wait
                # if isCapturing == False:
                #emit start capture
                #     isCapturing=True
                #     starI=elapsed
                    #await sio.emit("u_start_capture", "nodata")

                if elapsed <= (self._props.captureTime+self._props.waitTime)*1000 :
                #captue Image                       
                    if self._props.captureInterval>0:
                        if(elapsed-startI>=self._props.captureInterval*1000):
                            self._frames.append(array)
                            self._count += 1
                            startI=elapsed
                    else:
                        self._frames.append(array)
                        self._count += 1
                else:
                    #await sio.emit("u_capture_complete", "nodata")
                    #save image            
                    for i in range(0,len(self._frames)):
                        self.saveImage(self._frames[i],i,0)
                    self._frames.clear()
                    #isCapturing=False
                    #emit complete save all image
                    #await sio.emit("u_save_image_complete", "nodata")
                    #stop thread
                    self._running = False
                    self._thread.join()
                    self._picam2.stop()
    #endregion thread_func                 

    def wait_for_frame(self, previous=None):
        """You may optionally pass in the previous frame that you got last time you called this function.

        This will guarantee that you don't get duplicate frames
        returned in the event of spurious wake-ups, and it may even return more
        quickly in the case where a new frame has already arrived.
        """
        with self._condition:
            if previous is not None and self._array is not previous:
                return self._array
            while True:
                self._condition.wait()
                if self._array is not previous:
                    return self._array

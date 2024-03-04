class CaptureProp:
    def __init__(self,deviceName="D0",serverUrl="http://192.168.1.2:3333", camId=0,rWidth=1920,rHeight=1080,waitTime=5.0,captureTime=15.0,captureInterval=0.3):
        """A simple class that can serve up frames from one of the Picamera2's configured streams to multiple other threads.
        Pass in the Picamera2 object and the name of the stream for which you want
        to serve up frames.
        """
        self.deviceName=deviceName
        self.camId = camId
        self.rWidth = rWidth
        self.rHeight = rHeight
        self.captureInterval = captureInterval
        self.waitTime = waitTime
        self.captureTime = captureTime
        self.serverUrl=serverUrl
        self.focus=65
  
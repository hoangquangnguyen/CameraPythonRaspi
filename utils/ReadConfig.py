import simplejson as json
from model.capture_prop import CaptureProp

def ReadConfig(data):
    return json.loads(data)

def JsonToString(data):
    return json.dumps(data)

def ReadConfig2CapProp(data):
    jsonConfig=json.loads(data)
    capProps=CaptureProp()
    capProps.camId=0
    capProps.serverUrl=jsonConfig['server']
    capProps.waitTime=jsonConfig['waittime']
    capProps.rWidth=jsonConfig['resW']
    capProps.rHeight=jsonConfig['resH']
    capProps.captureInterval=jsonConfig['interval']
    capProps.deviceName=jsonConfig['devicename']
    capProps.captureTime= jsonConfig['capturetime']
    return capProps

    
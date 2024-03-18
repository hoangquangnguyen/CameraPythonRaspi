import simplejson as json
from model.capture_prop import CaptureProp

def ReadConfig(data):
    return json.loads(data)

def JsonToString(data):
    return json.dumps(data)

def ReadConfig2CapProp(jsonConfig):
    capProps=CaptureProp()
    capProps.camId=0
    capProps.serverUrl=jsonConfig['serverUrl']
    capProps.waitTime=jsonConfig['waitTime']
    capProps.rWidth=jsonConfig['rWidth']
    capProps.rHeight=jsonConfig['rHeight']
    capProps.captureInterval=jsonConfig['captureInterval']
    capProps.deviceName=jsonConfig['deviceName']
    capProps.captureTime= jsonConfig['captureTime']
    return capProps

def ConfigToString(data):
    return json.dumps({
        "deviceName": data.deviceName, 
        "serverUrl": data.serverUrl,
       "camId": data.camId, 
       "focus": 65, 
       "rWidth": data.rWidth, 
       "rHeight": data.rHeight, 
       "waitTime": data.waitTime, 
       "captureInterval": data.captureInterval, 
       "captureTime": data.captureTime})

    
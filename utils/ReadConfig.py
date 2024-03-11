import simplejson as json
from model.capture_prop import CaptureProp

def ReadConfig(data):
    return json.loads(data)

def JsonToString(data):
    return json.dumps(data)

def ReadConfig2CapProp(data):
    jsonConfig=json.loads(data)
    capProps=CaptureProp()
    capProps.CamId=0
    capProps.ServerUrl=jsonConfig['Server']
    capProps.WaitTime=jsonConfig['WaitTime']
    capProps.rWidth=jsonConfig['rWidth']
    capProps.rHeight=jsonConfig['rHeight']
    capProps.captureInterval=jsonConfig['Interval']
    capProps.deviceName=jsonConfig['DeviceName']
    capProps.captureTime= jsonConfig['CaptureTime']
    return capProps

    
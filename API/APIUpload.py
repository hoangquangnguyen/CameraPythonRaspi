import requests

async def upload(myUrl,myFiles,deviceName,folderName):
    form_data={"devicename":deviceName,"foldername":folderName}
    resp=requests.post(url=myUrl,data=form_data,files=myFiles)
    return resp.status_code


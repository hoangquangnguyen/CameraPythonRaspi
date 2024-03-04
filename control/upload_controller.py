from utils.FileManager import ScanFile
from API.APIUpload import upload
import asyncio

class UploadController:
    async def uploadToServer(sels,sioManager,server,devicename,folderName):
        allfile=ScanFile("./img")
        myUrl =server+"/multiple-upload"
        i=0
        while i<len(allfile):
            if i+3<len(allfile):
                manyFiles=[("many-files",open('./img/'+str(allfile[i]),'rb')),("many-files",open('img/'+str(allfile[i+1]),'rb')),("many-files",open('img/'+str(allfile[i+2]),'rb'))]
                await upload(myUrl,manyFiles,devicename,folderName)
                i=i+3
            else:
                await upload(myUrl,[("many-files",open('./img/'+str(allfile[i]),'rb'))],devicename,folderName) 
                i=i+1 
            await asyncio.sleep(0.01)        
        await sioManager.emit("u_upload_complete", "nodata")
        print("upload complete")
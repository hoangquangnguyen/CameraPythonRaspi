import os
from io import BytesIO
from PIL import Image

def MyReadFile(path):
    f = open(path, "r")
    return f.read()

def MyWriteFile(path,data):
    f = open(path, "w")
    f.write(data)
    f.close()

def CreateFolder(path,name):
    return 0

async def DeleteAllFileInFolder(path):
    try:
        files = os.listdir(path)
        for file in files:
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)

        #print("All files deleted successfully.")
        return True
    except:
        print("Error occurred while deleting files.")

def ScanFile(path):
    try:
        files = os.listdir(path)
        #print("Scan folder successfully.")
        return files
    except:
        print("Error occurred Scan folder.")
        return []

async def saveImageFromBuffer(frame,imgPath):
    buff = BytesIO(bytes(frame)) 
    image = Image.open(buff, formats=["JPEG"])
    image.save(imgPath,bitmap_format='bmp',quality=100,optimize=False,compression_level=0)#param1_4.7mb_cap24s_202s
    #image.save("img/"+"cam"+str(deviceID)+"img"+str(x)+".jpg",format="JPEG",saveExtra={"bitmap_format": "bmp"},quality=95,compression_level=0)#param2_2.3mb_cap24s_180s
    #image.save("img/"+"cam"+str(deviceID)+"img"+str(x)+".jpg",bitmap_format='bmp',quality=95,optimize=True,compression_level=0)#param3_2mb_cap24s_270s

async def saveImageFromArray(frame,imgPath):
        #buff = BytesIO(bytes(frame)) 
        image = Image.fromarray(frame)
        image.save(imgPath,bitmap_format='png',quality=100,optimize=False,compression_level=0)

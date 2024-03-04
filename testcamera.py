# from picamera2 import Picamera2
# from libcamera import Transform

# def print_af_state(request):
#     md = request.get_metadata()
#     print(("Idle", "Scanning", "Success", "Fail")[md['AfState']], md.get('LensPosition'))

# picam2 = Picamera2()
# preview_config = picam2.create_preview_configuration(transform=Transform(rotation=0,hflip=True))
# picam2.configure(preview_config)
# while(True):
#     picam2.pre_callback = print_af_state
#     picam2.start(show_preview=True)
#     success = picam2.autofocus_cycle()
#     picam2.pre_callback = None


from picamera2 import Picamera2
from libcamera import controls
from libcamera import Transform
picam2 = Picamera2()
preview_config = picam2.create_preview_configuration(main={"size": (1600,1200)},transform=Transform(vflip=True))
picam2.start(config=preview_config,show_preview=True)
picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
picam2.set_controls({"AfPause": controls.AfPauseEnum.Resume})
picam2.set_controls({"AfRange": controls.AfRangeEnum.Normal})
picam2.set_controls({"AwbEnable": True})
picam2.set_controls({"AwbMode": controls.AwbModeEnum.Auto})
picam2.set_controls({"Brightness":0.04})
picam2.set_controls({"ExposureValue":0.5})
picam2.set_controls({"Saturation":1.2})
#picam2.set_controls({"ColourGains":(2.0, 1.9)})
picam2.set_controls({"Sharpness":0})
picam2.set_controls({'HdrMode': controls.HdrModeEnum.SingleExposure})
#oiseReductionMode
#
while(True):
    a=0
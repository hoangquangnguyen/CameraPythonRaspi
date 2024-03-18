from enum import Enum
 
class SocketIOKey(Enum):
    server_request_u_capture= "server_request_u_capture"
    server_request_u_upload= "server_request_u_upload"
    server_request_u_change_resolution= "server_request_u_change_resolution"
    server_request_u_change_interval= "server_request_u_change_interval"
    server_request_u_change_wait_time= "server_request_u_change_wait_time"
    server_request_u_change_capture_time= "server_request_u_change_capture_time"
    server_request_u_update_device_info= "server_request_u_update_device_info"
    server_request_u_change_focus= "server_request_u_change_focus"
    server_request_u_onoff_camera= "server_request_u_onoff_camera"
    server_request_u_delete_image= "server_request_u_delete_image"
    server_request_u_change_config= "server_request_u_change_config"
    u_send_info= "u_send_info"
    u_start_capture="u_start_capture"
    u_capture_complete="u_capture_complete"
    u_save_image_complete="u_save_image_complete"
    u_camera_status="u_camera_status"
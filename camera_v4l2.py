import io
from PIL import Image, ImageOps
import select
import v4l2capture
from base_camera import BaseCamera


class Camera(BaseCamera):
    """Requires python-v4l2capture module: https://github.com/gebart/python-v4l2capture"""
    # Python 3 Support: https://github.com/rmca/python-v4l2capture/tree/py3k

    video_source = "/dev/video0"

    @staticmethod
    def frames():
        video = v4l2capture.Video_device(Camera.video_source)
        # Suggest an image size. The device may choose and return another if unsupported
        # size_x = 1080
        # size_y = 540
        # 1024×576
        size_x = 1280
        size_y = 720
        size_x, size_y = video.set_format(size_x, size_y)
        video.create_buffers(1)
        video.queue_all_buffers()
        video.start()
        bio = io.BytesIO()

        try:
            while True:
                select.select((video,), (), ())  # Wait for the device to fill the buffer.
                image_data = video.read_and_queue()
                image = Image.frombytes("RGB", (size_x, size_y), image_data)
                image_mirror = ImageOps.mirror(image)
                image_mirror.save(bio, format="jpeg")
                yield bio.getvalue()
                bio.seek(0)
                bio.truncate()
        finally:
            video.close()

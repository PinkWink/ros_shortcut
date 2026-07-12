"""Simulation replacement for the Pinky Pro face LCD driver.

The real robot drives an ILI9341-style 320x240 SPI panel (spidev +
RPi.GPIO).  In simulation the same LCD interface publishes each frame as a
sensor_msgs/Image on ``screen/image_raw`` so the robot face can be viewed
with rqt_image_view or RViz.
"""

from PIL import Image
from sensor_msgs.msg import Image as ImageMsg

LCD_WIDTH = 320
LCD_HEIGHT = 240


class LCD:

    def __init__(self, node):
        self._node = node
        self._pub = node.create_publisher(ImageMsg, 'screen/image_raw', 3)

    def img_show(self, pil_image):
        img = pil_image.convert('RGB')
        if img.size != (LCD_WIDTH, LCD_HEIGHT):
            img = img.resize((LCD_WIDTH, LCD_HEIGHT))

        msg = ImageMsg()
        msg.header.stamp = self._node.get_clock().now().to_msg()
        msg.header.frame_id = 'screen_mount'
        msg.height = img.height
        msg.width = img.width
        msg.encoding = 'rgb8'
        msg.is_bigendian = 0
        msg.step = img.width * 3
        msg.data = img.tobytes()
        self._pub.publish(msg)

    def clear(self):
        try:
            self.img_show(Image.new('RGB', (LCD_WIDTH, LCD_HEIGHT)))
        except Exception:
            pass  # node may already be shut down

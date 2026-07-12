#!/usr/bin/env python3
"""Simulation counterpart of pinky_lamp_control.

Provides the same `set_lamp` service (pinky_interfaces/srv/SetLamp) as the
real robot's WS2812B lamp driver, but instead of driving GPIO it publishes
the current lamp color on `lamp/color` (std_msgs/ColorRGBA).  The bridge
forwards it to Gazebo where the LampControlPlugin colors the robot_lamp
visual.

Modes (same as the real driver):
  0 = off, 1 = on, 2 = blink (period `time` ms), 3 = dimming (period `time` ms)
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import ColorRGBA

from pinky_interfaces.srv import SetLamp

MODE_OFF = 0
MODE_ON = 1
MODE_BLINK = 2
MODE_DIMMING = 3


class LampServer(Node):

    def __init__(self):
        super().__init__('pinky_lamp_control')
        self.color_pub = self.create_publisher(ColorRGBA, 'lamp/color', 10)
        self.create_service(SetLamp, 'set_lamp', self.set_lamp_callback)

        self.mode = MODE_OFF
        self.color = (0.0, 0.0, 0.0)
        self.period = 1.0  # seconds, for blink/dimming
        self.phase_start = self.now_sec()

        self.create_timer(0.05, self.timer_callback)
        self.get_logger().info('lamp server ready: service [set_lamp] -> topic [lamp/color]')

    def now_sec(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def set_lamp_callback(self, request, response):
        if request.mode > MODE_DIMMING:
            response.result = False
            return response

        self.mode = request.mode
        # ColorRGBA in the request uses 0-255 (as on the real robot); accept 0-1 too
        scale = 255.0 if max(request.color.r, request.color.g, request.color.b) > 1.0 else 1.0
        self.color = (request.color.r / scale,
                      request.color.g / scale,
                      request.color.b / scale)
        self.period = max(request.time, 100) / 1000.0
        self.phase_start = self.now_sec()
        self.get_logger().info(
            f'set_lamp: mode={self.mode} color={self.color} period={self.period:.2f}s')
        response.result = True
        return response

    def timer_callback(self):
        elapsed = self.now_sec() - self.phase_start

        if self.mode == MODE_ON:
            brightness = 1.0
        elif self.mode == MODE_BLINK:
            brightness = 1.0 if (elapsed % self.period) < self.period / 2.0 else 0.0
        elif self.mode == MODE_DIMMING:
            brightness = 0.5 * (1.0 - math.cos(2.0 * math.pi * elapsed / self.period))
        else:  # MODE_OFF
            brightness = 0.0

        msg = ColorRGBA()
        msg.r = self.color[0] * brightness
        msg.g = self.color[1] * brightness
        msg.b = self.color[2] * brightness
        msg.a = 1.0
        self.color_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = LampServer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

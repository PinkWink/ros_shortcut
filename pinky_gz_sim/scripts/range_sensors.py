#!/usr/bin/env python3
"""Simulation counterpart of pinky_sensor_adc.

The real robot reads 1 ultrasonic + 3 IR sensors through an I2C ADC and
publishes:
  us_sensor/range  sensor_msgs/Range            (ultrasonic, 20 Hz)
  ir_sensor/range  std_msgs/UInt16MultiArray    ([left, mid, right], 20 Hz)

In simulation those sensors are narrow gpu_lidar beams bridged as
LaserScan topics (us_scan, ir_scan_l, ir_scan_mid, ir_scan_r).  This node
converts them to the same ROS interfaces as the real robot.  IR distances
are mapped to a 12-bit ADC-like value: closer obstacle -> larger value.
"""

import math

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan, Range
from std_msgs.msg import UInt16MultiArray

US_MIN, US_MAX, US_FOV = 0.02, 3.0, 0.26
IR_MIN, IR_MAX = 0.01, 0.4
ADC_MAX = 4095


def min_valid_range(scan):
    valid = [r for r in scan.ranges if math.isfinite(r) and r >= scan.range_min]
    return min(valid) if valid else None


def ir_to_adc(distance):
    if distance is None:
        return 0
    ratio = (distance - IR_MIN) / (IR_MAX - IR_MIN)
    return max(0, min(ADC_MAX, int(ADC_MAX * (1.0 - ratio))))


class SimRangeSensors(Node):

    def __init__(self):
        super().__init__('pinky_sensor_adc')
        self.us_pub = self.create_publisher(Range, 'us_sensor/range', 10)
        self.ir_pub = self.create_publisher(UInt16MultiArray, 'ir_sensor/range', 10)

        self.ir_dist = {'l': None, 'mid': None, 'r': None}

        self.create_subscription(LaserScan, 'us_scan', self.us_callback, 10)
        for key in self.ir_dist:
            self.create_subscription(
                LaserScan, f'ir_scan_{key}',
                lambda msg, k=key: self.ir_callback(k, msg), 10)

        self.create_timer(0.05, self.publish_ir)
        self.get_logger().info('sim range sensors ready: us_sensor/range, ir_sensor/range')

    def us_callback(self, scan):
        msg = Range()
        msg.header.stamp = scan.header.stamp
        msg.header.frame_id = 'ultrasonic_link'
        msg.radiation_type = Range.ULTRASOUND
        msg.field_of_view = US_FOV
        msg.min_range = US_MIN
        msg.max_range = US_MAX
        distance = min_valid_range(scan)
        msg.range = min(distance, US_MAX) if distance is not None else US_MAX
        self.us_pub.publish(msg)

    def ir_callback(self, key, scan):
        self.ir_dist[key] = min_valid_range(scan)

    def publish_ir(self):
        msg = UInt16MultiArray()
        msg.data = [ir_to_adc(self.ir_dist['l']),
                    ir_to_adc(self.ir_dist['mid']),
                    ir_to_adc(self.ir_dist['r'])]
        self.ir_pub.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = SimRangeSensors()
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

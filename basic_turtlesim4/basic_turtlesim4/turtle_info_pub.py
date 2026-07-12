import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from basic_turtlesim4_msgs.msg import TurtleInfo
from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class TurtleInfoPub(Node):
    """pose와 cmd_vel을 구독해서 커스텀 메시지(TurtleInfo)로 합쳐 발행하는 노드

    확인 예:
        ros2 topic echo /turtle_info
    """

    def __init__(self):
        super().__init__('turtle_info_pub')

        # /turtle1/pose 토픽 구독
        self.pose_subscriber = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10)

        # /turtle1/cmd_vel 토픽 구독
        self.cmd_vel_subscriber = self.create_subscription(
            Twist, '/turtle1/cmd_vel', self.cmd_vel_callback, 10)

        # 커스텀 메시지 발행 (Publisher)
        self.info_publisher = self.create_publisher(
            TurtleInfo, '/turtle_info', 10)

        # 1초마다 커스텀 메시지를 발행하는 타이머
        self.timer = self.create_timer(1.0, self.timer_callback)

        self.pose = Pose()
        self.cmd_vel = Twist()

    def pose_callback(self, msg):
        self.pose = msg

    def cmd_vel_callback(self, msg):
        self.cmd_vel = msg

    def timer_callback(self):
        """구독해 둔 pose와 cmd_vel을 커스텀 메시지에 담아 발행"""
        info = TurtleInfo()
        info.pose_x = self.pose.x
        info.pose_y = self.pose.y
        info.theta = self.pose.theta
        info.cmd_linear = float(self.cmd_vel.linear.x)
        info.cmd_angular = float(self.cmd_vel.angular.z)

        self.info_publisher.publish(info)
        self.get_logger().info(
            f'TurtleInfo 발행: x={info.pose_x:.2f}, y={info.pose_y:.2f}, '
            f'cmd_linear={info.cmd_linear:.2f}')


def main(args=None):
    rclpy.init(args=args)
    node = TurtleInfoPub()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        # Ctrl+C 또는 launch 종료(SIGINT)에 의한 정상 종료
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

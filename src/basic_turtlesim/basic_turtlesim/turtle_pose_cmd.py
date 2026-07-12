import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.msg import Pose


class TurtlePoseCmd(Node):
    """turtlesim의 pose를 구독하고, cmd_vel을 발행해서 거북이를 움직이는 노드"""

    def __init__(self):
        super().__init__('turtle_pose_cmd')

        # /turtle1/pose 토픽 구독 (Subscriber)
        self.pose_subscriber = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10)

        # /turtle1/cmd_vel 토픽 발행 (Publisher)
        self.cmd_vel_publisher = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10)

        # 0.1초마다 cmd_vel을 발행하는 타이머
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.pose = Pose()

    def pose_callback(self, msg):
        """pose 토픽을 받을 때마다 호출되는 콜백"""
        self.pose = msg
        # pose는 약 62.5Hz로 들어오므로 1초에 한 번만 출력
        self.get_logger().info(
            f'x: {msg.x:.2f}, y: {msg.y:.2f}, theta: {msg.theta:.2f}',
            throttle_duration_sec=1.0)

    def timer_callback(self):
        """일정 주기로 속도 명령을 발행 - 원을 그리며 움직인다"""
        twist = Twist()
        twist.linear.x = 2.0    # 전진 속도 (m/s)
        twist.angular.z = 1.0   # 회전 속도 (rad/s)
        self.cmd_vel_publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurtlePoseCmd()
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

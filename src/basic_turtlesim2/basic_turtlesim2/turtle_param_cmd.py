import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from geometry_msgs.msg import Twist


class TurtleParamCmd(Node):
    """선속도/각속도를 파라미터로 받아 cmd_vel을 발행하는 노드

    파라미터는 launch 파일에서 config/turtle_params.yaml을 읽어 적용되고,
    실행 중에도 ros2 param set으로 바꿀 수 있다.
    """

    def __init__(self):
        super().__init__('turtle_param_cmd')

        # 파라미터 선언 (이름, 기본값)
        self.declare_parameter('linear_velocity', 1.0)
        self.declare_parameter('angular_velocity', 0.5)

        # /turtle1/cmd_vel 토픽 발행 (Publisher)
        self.cmd_vel_publisher = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10)

        # 0.1초마다 cmd_vel을 발행하는 타이머
        self.timer = self.create_timer(0.1, self.timer_callback)

        linear = self.get_parameter('linear_velocity').value
        angular = self.get_parameter('angular_velocity').value
        self.get_logger().info(
            f'시작 파라미터 - linear_velocity: {linear}, '
            f'angular_velocity: {angular}')

    def timer_callback(self):
        """타이머마다 파라미터를 읽어서 속도 명령을 발행

        매번 get_parameter로 읽기 때문에 실행 중에
        ros2 param set으로 바꾸면 바로 반영된다.
        """
        twist = Twist()
        twist.linear.x = self.get_parameter('linear_velocity').value
        twist.angular.z = self.get_parameter('angular_velocity').value
        self.cmd_vel_publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleParamCmd()
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

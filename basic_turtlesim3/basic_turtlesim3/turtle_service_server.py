import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from geometry_msgs.msg import Twist
from std_srvs.srv import SetBool


class TurtleServiceServer(Node):
    """SetBool 서비스로 거북이의 움직임을 켜고 끄는 서비스 서버 노드

    속도는 파라미터(linear_velocity, angular_velocity)로 설정한다.

    사용 예:
        ros2 service call /turtle_move_on_off std_srvs/srv/SetBool "{data: true}"
        ros2 service call /turtle_move_on_off std_srvs/srv/SetBool "{data: false}"
    """

    def __init__(self):
        super().__init__('turtle_service_server')

        # 파라미터 선언 (이름, 기본값) - launch에서 yaml로 덮어쓸 수 있다
        self.declare_parameter('linear_velocity', 1.0)
        self.declare_parameter('angular_velocity', 0.5)

        # 움직임 on/off 상태
        self.moving = False

        # 서비스 서버 생성 (서비스 타입, 서비스 이름, 콜백)
        self.service = self.create_service(
            SetBool, '/turtle_move_on_off', self.service_callback)

        # /turtle1/cmd_vel 토픽 발행 (Publisher)
        self.cmd_vel_publisher = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10)

        # 0.1초마다 속도 명령을 발행하는 타이머
        self.timer = self.create_timer(0.1, self.timer_callback)

        self.get_logger().info('turtle_move_on_off 서비스 서버 준비 완료')

    def service_callback(self, request, response):
        """서비스 요청을 받았을 때 호출되는 콜백

        request.data가 True면 움직임 시작, False면 정지
        """
        self.moving = request.data

        response.success = True
        response.message = '움직임 시작' if request.data else '움직임 정지'

        self.get_logger().info(f'서비스 요청 수신: {response.message}')
        return response

    def timer_callback(self):
        """moving 상태일 때만 파라미터로 정해진 속도를 발행"""
        if not self.moving:
            return

        twist = Twist()
        twist.linear.x = self.get_parameter('linear_velocity').value
        twist.angular.z = self.get_parameter('angular_velocity').value
        self.cmd_vel_publisher.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleServiceServer()
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

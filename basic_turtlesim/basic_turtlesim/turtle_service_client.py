import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from turtlesim.srv import SetPen


class TurtleServiceClient(Node):
    """turtlesim의 /turtle1/set_pen 서비스를 호출해서 펜 색을 바꾸는 노드"""

    def __init__(self):
        super().__init__('turtle_service_client')

        # SetPen 서비스 클라이언트 생성
        self.client = self.create_client(SetPen, '/turtle1/set_pen')

        # 서비스 서버(turtlesim)가 켜질 때까지 대기
        while not self.client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('set_pen 서비스를 기다리는 중...')

        # 2초마다 바꿀 펜 색 목록 (R, G, B)
        self.colors = [
            (255, 0, 0),    # 빨강
            (0, 255, 0),    # 초록
            (0, 0, 255),    # 파랑
        ]
        self.color_index = 0

        # 2초마다 서비스를 호출하는 타이머
        self.timer = self.create_timer(2.0, self.timer_callback)

    def timer_callback(self):
        """일정 주기로 set_pen 서비스 호출"""
        r, g, b = self.colors[self.color_index % len(self.colors)]
        self.color_index += 1

        request = SetPen.Request()
        request.r = r
        request.g = g
        request.b = b
        request.width = 5
        request.off = 0     # 0이면 펜 켜기, 1이면 펜 끄기

        self.get_logger().info(f'set_pen 요청: r={r}, g={g}, b={b}')

        # 비동기로 서비스 호출, 응답이 오면 콜백 실행
        future = self.client.call_async(request)
        future.add_done_callback(self.response_callback)

    def response_callback(self, future):
        """서비스 응답을 받았을 때 호출되는 콜백"""
        try:
            future.result()     # SetPen의 응답은 비어 있음
            self.get_logger().info('set_pen 응답 수신 완료')
        except Exception as e:
            self.get_logger().error(f'서비스 호출 실패: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = TurtleServiceClient()
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

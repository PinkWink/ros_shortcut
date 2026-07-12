import math

import rclpy
from rclpy.executors import ExternalShutdownException
from rclpy.node import Node

from basic_turtlesim4_msgs.srv import MultiSpawn
from turtlesim.srv import Spawn


class MultiSpawnServer(Node):
    """커스텀 서비스(MultiSpawn)로 여러 마리의 거북이를 소환하는 서비스 서버 노드

    요청받은 수(num)만큼 화면 중앙을 둘러싼 원 위에 거북이를 소환하고,
    소환한 위치 목록을 응답으로 돌려준다.
    내부적으로는 turtlesim의 /spawn 서비스를 클라이언트로 호출한다.

    사용 예:
        ros2 service call /multi_spawn basic_turtlesim4_msgs/srv/MultiSpawn "{num: 3}"
    """

    def __init__(self):
        super().__init__('multi_spawn_server')

        # 커스텀 서비스 서버 생성
        self.service = self.create_service(
            MultiSpawn, '/multi_spawn', self.service_callback)

        # turtlesim의 /spawn 서비스를 호출할 클라이언트
        self.spawn_client = self.create_client(Spawn, '/spawn')
        while not self.spawn_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('spawn 서비스를 기다리는 중...')

        # 소환 위치를 정할 원의 중심과 반지름
        self.center_x = 5.5
        self.center_y = 5.5
        self.radius = 3.0

        self.get_logger().info('multi_spawn 서비스 서버 준비 완료')

    def service_callback(self, request, response):
        """num 마리의 거북이를 원 위에 고르게 소환"""
        self.get_logger().info(f'multi_spawn 요청 수신: num={request.num}')

        for i in range(request.num):
            # 원을 num 등분한 위치 계산
            angle = 2.0 * math.pi * i / request.num
            x = self.center_x + self.radius * math.cos(angle)
            y = self.center_y + self.radius * math.sin(angle)
            theta = angle + math.pi / 2.0    # 원의 접선 방향을 바라보게

            # turtlesim의 spawn 서비스 호출 (비동기)
            # 같은 노드가 서비스를 처리하는 중이므로 응답을 기다리지 않는다
            spawn_request = Spawn.Request()
            spawn_request.x = x
            spawn_request.y = y
            spawn_request.theta = theta
            self.spawn_client.call_async(spawn_request)

            # 소환한 위치를 응답 배열에 추가
            response.x.append(x)
            response.y.append(y)
            response.theta.append(theta)

        return response


def main(args=None):
    rclpy.init(args=args)
    node = MultiSpawnServer()
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

import math
import time

import rclpy
from rclpy.action import ActionServer
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import ExternalShutdownException, MultiThreadedExecutor
from rclpy.node import Node

from geometry_msgs.msg import Twist
from turtlesim.action import RotateAbsolute
from turtlesim.msg import Pose


def normalize_angle(angle):
    """각도를 -pi ~ pi 범위로 정규화"""
    return math.atan2(math.sin(angle), math.cos(angle))


class TurtleActionServer(Node):
    """거북이를 목표 각도(theta)까지 회전시키는 액션 서버 노드

    turtlesim의 RotateAbsolute 액션 인터페이스를 사용한다.
      - Goal    : theta (목표 절대 각도, rad)
      - Feedback: remaining (남은 각도, rad)
      - Result  : delta (실제 회전한 각도, rad)

    사용 예:
        ros2 action send_goal --feedback /turtle_rotate_absolute \\
            turtlesim/action/RotateAbsolute "{theta: 1.57}"
    """

    def __init__(self):
        super().__init__('turtle_action_server')

        # 액션 실행 중에도 pose 콜백이 처리되도록 ReentrantCallbackGroup 사용
        self.callback_group = ReentrantCallbackGroup()

        self.pose = None

        # /turtle1/pose 토픽 구독 (Subscriber)
        self.pose_subscriber = self.create_subscription(
            Pose, '/turtle1/pose', self.pose_callback, 10,
            callback_group=self.callback_group)

        # /turtle1/cmd_vel 토픽 발행 (Publisher)
        self.cmd_vel_publisher = self.create_publisher(
            Twist, '/turtle1/cmd_vel', 10)

        # 액션 서버 생성 (노드, 액션 타입, 액션 이름, 실행 콜백)
        self.action_server = ActionServer(
            self, RotateAbsolute, '/turtle_rotate_absolute',
            self.execute_callback,
            callback_group=self.callback_group)

        self.get_logger().info('turtle_rotate_absolute 액션 서버 준비 완료')

    def pose_callback(self, msg):
        self.pose = msg

    def execute_callback(self, goal_handle):
        """액션 goal을 받았을 때 호출되는 콜백 - 목표 각도까지 회전"""
        target_theta = goal_handle.request.theta
        self.get_logger().info(f'액션 goal 수신: theta={target_theta:.2f}')

        # 첫 pose를 받을 때까지 대기
        while self.pose is None:
            time.sleep(0.1)

        start_theta = self.pose.theta
        feedback = RotateAbsolute.Feedback()

        while rclpy.ok():
            remaining = normalize_angle(target_theta - self.pose.theta)

            # 목표 각도에 도달하면 종료
            if abs(remaining) < 0.1:
                break

            # 남은 각도의 방향으로 일정한 속도로 회전
            twist = Twist()
            twist.angular.z = 1.0 if remaining > 0.0 else -1.0
            self.cmd_vel_publisher.publish(twist)

            # feedback 발행 (남은 각도)
            feedback.remaining = remaining
            goal_handle.publish_feedback(feedback)

            time.sleep(0.1)

        # 정지
        self.cmd_vel_publisher.publish(Twist())

        # 액션 성공 처리 후 result 반환 (실제 회전한 각도)
        goal_handle.succeed()
        result = RotateAbsolute.Result()
        result.delta = normalize_angle(self.pose.theta - start_theta)
        self.get_logger().info(f'액션 완료: delta={result.delta:.2f}')
        return result


def main(args=None):
    rclpy.init(args=args)
    node = TurtleActionServer()

    # 액션 실행 중에도 다른 콜백이 돌 수 있도록 멀티스레드 실행기 사용
    executor = MultiThreadedExecutor()
    executor.add_node(node)
    try:
        executor.spin()
    except (KeyboardInterrupt, ExternalShutdownException):
        # Ctrl+C 또는 launch 종료(SIGINT)에 의한 정상 종료
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()

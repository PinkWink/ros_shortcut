from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        # turtlesim 시뮬레이터
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
        ),
        # pose 구독 + cmd_vel 발행 노드
        Node(
            package='basic_turtlesim',
            executable='turtle_pose_cmd',
            name='turtle_pose_cmd',
            output='screen',
        ),
        # set_pen 서비스 클라이언트 노드
        Node(
            package='basic_turtlesim',
            executable='turtle_service_client',
            name='turtle_service_client',
            output='screen',
        ),
    ])

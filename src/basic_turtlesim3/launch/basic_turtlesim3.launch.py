import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 패키지 share 폴더에 설치된 config/turtle_params.yaml 경로
    param_file = os.path.join(
        get_package_share_directory('basic_turtlesim3'),
        'config',
        'turtle_params.yaml')

    return LaunchDescription([
        # turtlesim 시뮬레이터
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
        ),
        # 움직임 on/off 서비스 서버 노드 (yaml에서 속도 파라미터 적용)
        Node(
            package='basic_turtlesim3',
            executable='turtle_service_server',
            name='turtle_service_server',
            output='screen',
            parameters=[param_file],
        ),
        # 목표 각도까지 회전시키는 액션 서버 노드
        Node(
            package='basic_turtlesim3',
            executable='turtle_action_server',
            name='turtle_action_server',
            output='screen',
        ),
    ])

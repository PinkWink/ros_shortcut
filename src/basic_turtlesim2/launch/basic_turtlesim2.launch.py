import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    # 패키지 share 폴더에 설치된 config/turtle_params.yaml 경로
    param_file = os.path.join(
        get_package_share_directory('basic_turtlesim2'),
        'config',
        'turtle_params.yaml')

    return LaunchDescription([
        # turtlesim 시뮬레이터
        Node(
            package='turtlesim',
            executable='turtlesim_node',
            name='turtlesim',
        ),
        # 파라미터로 속도를 조절하는 cmd_vel 발행 노드
        # yaml 파일을 읽어서 파라미터 적용
        Node(
            package='basic_turtlesim2',
            executable='turtle_param_cmd',
            name='turtle_param_cmd',
            output='screen',
            parameters=[param_file],
        ),
    ])

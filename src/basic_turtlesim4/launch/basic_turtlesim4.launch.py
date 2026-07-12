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
        # 커스텀 메시지(TurtleInfo) 발행 노드
        Node(
            package='basic_turtlesim4',
            executable='turtle_info_pub',
            name='turtle_info_pub',
            output='screen',
        ),
        # 커스텀 서비스(MultiSpawn) 서버 노드
        Node(
            package='basic_turtlesim4',
            executable='multi_spawn_server',
            name='multi_spawn_server',
            output='screen',
        ),
    ])

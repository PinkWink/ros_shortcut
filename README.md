# ros_shortcut

ROS 2 Jazzy 기초를 빠르게 훑는 예제 워크스페이스입니다. turtlesim으로 토픽·서비스·액션·파라미터·커스텀 인터페이스를 익힌 뒤, URDF와 Gazebo(Harmonic) 시뮬레이션까지 이어집니다.

[PinkLAB](https://pinklab.art)에서 진행하는 강의/튜토리얼과 함께 보시면 좋습니다.

## 환경

- ROS 2 Jazzy
- Gazebo Harmonic (`ros_gz`)
- Python (ament_python)

## 패키지 구성

| 패키지 | 내용 |
|---|---|
| `basic_turtlesim` | 토픽 발행과 서비스 클라이언트 기초 (`turtle_pose_cmd`, `turtle_service_client`) |
| `basic_turtlesim2` | 파라미터 사용 (`turtle_param_cmd`) |
| `basic_turtlesim3` | 서비스 서버와 액션 서버 (`turtle_service_server`, `turtle_action_server`) |
| `basic_turtlesim4` | 커스텀 인터페이스 활용 (`turtle_info_pub`, `multi_spawn_server`) |
| `basic_turtlesim4_msgs` | 커스텀 인터페이스 정의 (`TurtleInfo.msg`, `MultiSpawn.srv`) |
| `urdf_basic` | URDF 기초 — 원기둥으로 구성한 cart-pole의 자유 낙하를 Gazebo에서 실험 |

## urdf_basic 사용법

```bash
# 워크스페이스의 src 안에 클론
mkdir -p ~/ros_ws/src
cd ~/ros_ws/src
git clone https://github.com/PinkWink/ros_shortcut.git

# 빌드
cd ~/ros_ws
colcon build
source install/setup.bash

# Gazebo + 웹 모니터 실행
ros2 launch urdf_basic cartpole_web.launch.xml
```

브라우저에서 <http://localhost:8000> 을 열면 cart-pole의 2D 애니메이션과 위치·속도 실시간 차트를 볼 수 있고, Reset 버튼으로 시뮬레이션을 처음부터 다시 시작할 수 있습니다.

matplotlib 창으로 보려면:

```bash
ros2 launch urdf_basic cartpole_gazebo.launch.py
# 다른 터미널에서
ros2 run urdf_basic joint_state_plotter
```

## 소개

- PinkLAB — <https://pinklab.art>
- 문의: contact@pinklab.art

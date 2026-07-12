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
| `pinky_description` | Pinky Pro 로봇 모델(xacro, 메시) — 라이다·카메라·IMU·초음파·IR 센서 포함 |
| `pinky_gz_sim` | Pinky Pro Gazebo 시뮬레이션 — 월드, 브리지, 램프 플러그인, 시뮬레이션용 센서/램프 노드 |
| `pinky_navigation` | slam_toolbox 기반 SLAM과 Nav2 내비게이션 (+ 웹 UI) |
| `pinky_emotion` | LCD 표정 애니메이션 — 시뮬레이션에서는 `screen/image_raw` 토픽으로 발행 |
| `pinky_interfaces` | Pinky Pro 서비스 정의 (`SetLamp`, `SetLed`, `SetBrightness`, `Emotion`) |

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

## Pinky Pro 시뮬레이션

`pinky_*` 패키지들은 [pinklab-art/pinky_pro](https://github.com/pinklab-art/pinky_pro) 저장소(개발: [byeongkyu](https://github.com/byeongkyu), 배포: PinkLAB, Apache-2.0 — 루트의 `LICENSE` 참고)에서 가져온 뒤, **시뮬레이션 전용으로 재구성**한 것입니다.

- 실물 하드웨어 전용 패키지(`pinky_bringup`, `pinky_imu_bno055`, `pinky_sensor_adc`, `pinky_lamp_control`, `pinky_led`)와 SPI LCD 드라이버는 제거했습니다.
- 대신 실물과 **동일한 ROS 인터페이스**가 Gazebo에서 동작합니다:
  - IMU → `imu_raw` (gz IMU 센서 브리지)
  - 초음파 → `us_sensor/range`, IR×3 → `ir_sensor/range` (gz 레이저 빔 기반)
  - LED 램프 → `set_lamp` 서비스 (모드: off/on/blink/dimming, Gazebo에서 램프 색이 실제로 변함)
  - LCD 표정 → `set_emotion` 서비스, 화면은 `screen/image_raw` 이미지 토픽 (rqt_image_view로 확인)

의존성 설치:

```bash
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup ros-jazzy-slam-toolbox python3-flask python3-pil
```

실행:

```bash
# Gazebo 시뮬레이션 (공장 월드 + 로봇 + 센서/램프/표정 노드)
ros2 launch pinky_gz_sim launch_sim.launch.xml

# SLAM (다른 터미널)
ros2 launch pinky_navigation gz_map_building.launch.xml

# Nav2 (지도 완성 후)
ros2 launch pinky_navigation gz_bringup_launch.xml

# 램프/표정 제어 예
ros2 service call /set_lamp pinky_interfaces/srv/SetLamp "{color: {r: 255.0, g: 0.0, b: 0.0}, mode: 2, time: 500}"
ros2 service call /set_emotion pinky_interfaces/srv/Emotion "{emotion: 'happy'}"
```

## 소개

- PinkLAB — <https://pinklab.art>
- 문의: contact@pinklab.art

import glob

from setuptools import find_packages, setup

package_name = 'basic_turtlesim'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pw',
    maintainer_email='pinkwink.korea@gmail.com',
    description='Basic turtlesim pub/sub and service examples',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turtle_pose_cmd = basic_turtlesim.turtle_pose_cmd:main',
            'turtle_service_client = basic_turtlesim.turtle_service_client:main',
        ],
    },
)

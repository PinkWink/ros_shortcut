import glob

from setuptools import find_packages, setup

package_name = 'basic_turtlesim3'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.*')),
        ('share/' + package_name + '/config', glob.glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pw',
    maintainer_email='pinkwink.korea@gmail.com',
    description='Basic turtlesim service server, action server, parameter and launch examples',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turtle_service_server = basic_turtlesim3.turtle_service_server:main',
            'turtle_action_server = basic_turtlesim3.turtle_action_server:main',
        ],
    },
)

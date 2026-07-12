import glob

from setuptools import find_packages, setup

package_name = 'urdf_basic'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/launch', glob.glob('launch/*.launch.*')),
        ('share/' + package_name + '/urdf', glob.glob('urdf/*.urdf')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='pw',
    maintainer_email='contact@pinklab.art',
    description='Basic URDF example: cart-pole free-fall experiment in Gazebo',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'joint_state_plotter = urdf_basic.joint_state_plotter:main',
            'web_monitor = urdf_basic.web_monitor:main',
        ],
    },
)

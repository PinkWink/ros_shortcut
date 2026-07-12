import glob

from setuptools import find_packages, setup

package_name = 'basic_turtlesim4'

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
    maintainer_email='contact@pinklab.art',
    description='Basic turtlesim examples using custom interfaces',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'turtle_info_pub = basic_turtlesim4.turtle_info_pub:main',
            'multi_spawn_server = basic_turtlesim4.multi_spawn_server:main',
        ],
    },
)

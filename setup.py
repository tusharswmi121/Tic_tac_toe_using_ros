from setuptools import find_packages, setup

package_name = 'tic_tac_toe'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Your Name',
    maintainer_email='you@example.com',
    description='Tic Tac Toe game with ROS 2 and Pygame',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'tic_tac_toe = tic_tac_toe.tictactoe_enhanced:main',
            'tic_tac_toe_ros = tic_tac_toe.tic_tac_toe_ros:main',
        ],
    },
)

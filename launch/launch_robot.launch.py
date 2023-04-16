import os

from ament_index_python.packages import get_package_share_directory


from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, TimerAction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, FindExecutable, PathJoinSubstitution
from launch.actions import RegisterEventHandler
from launch.event_handlers import OnProcessStart
from launch.actions import ExecuteProcess, LogInfo, RegisterEventHandler
from launch.substitutions import FindExecutable, LaunchConfiguration

from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare



def generate_launch_description():


    # Include the robot_state_publisher launch file, provided by our own package. Force sim time to be enabled
    # !!! MAKE SURE YOU SET THE PACKAGE NAME CORRECTLY !!!

    package_name='goose_busters'  

    rsp = IncludeLaunchDescription(
                PythonLaunchDescriptionSource([os.path.join(
                    get_package_share_directory(package_name),'launch','rsp.launch.py'
                )]), launch_arguments={'use_sim_time': 'false', 'use_ros2_control': 'true'}.items()
    )
    
    robot_description = Command(
        [
            PathJoinSubstitution([FindExecutable(name="xacro")]),
            " ",
            PathJoinSubstitution(
                [FindPackageShare(package_name), "description", "robot.urdf.xacro"]
            ),
        ]
    )

    power_service = Node(
        package="power_service",
        executable="service"

    )

    power_on = ExecuteProcess(
        cmd=[
        [
                FindExecutable(name="ros2"),
                " service call ",
                "/motor_power",
                "robot_interfaces/srv/MotorPower ",
                '"{on: 1}"'
        ]
        ],
        shell=True,
    )

    button_on = ExecuteProcess(
        cmd=[
        [
                FindExecutable(name="ros2"),
                " service call ",
                "/motor_button",
                "robot_interfaces/srv/MotorButtonOn ",
        ]
        ],
        shell=True,
    )

    controller_params_file = os.path.join(get_package_share_directory(package_name),'config','my_controllers.yaml')
 
    controller_manager = Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[{'robot_description': robot_description},
                    controller_params_file]
    )
    
    delayed_controller_manager = TimerAction(period=3.0, actions=[controller_manager])

    diff_drive_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["diff_cont"],
    )

    delayed_diff_drive_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[diff_drive_spawner],
        )
    )   

    joint_broad_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_broad"],
    )

    delayed_joint_broad_spawner = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=controller_manager,
            on_start=[joint_broad_spawner],
        )
    )

    # Launch them all!
    return LaunchDescription([
        power_service,

        rsp,
        controller_manager,
        delayed_diff_drive_spawner,
        delayed_joint_broad_spawner
    ])

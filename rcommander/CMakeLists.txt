cmake_minimum_required(VERSION 2.8.3)
project(rcommander)

## Find catkin macros and libraries

find_package(catkin REQUIRED COMPONENTS
  message_generation
  rospy
  nodebox_qt
  smach
  smach_ros
  actionlib
  geometry_msgs
  tf
  tf_broadcast_server
)

catkin_python_setup()

# Declare the message files to be built
add_message_files(FILES
  Trigger.msg
)
# Actually generate the language-specific message and service files
generate_messages(DEPENDENCIES std_msgs)

catkin_package(
  CATKIN_DEPENDS message_runtime std_msgs
)

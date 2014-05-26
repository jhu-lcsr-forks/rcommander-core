cmake_minimum_required(VERSION 2.8.3)
project(tf_broadcast_server)

## Find catkin macros and libraries

find_package(catkin REQUIRED COMPONENTS
  tf
  geometry_msgs
)

catkin_python_setup()

#######################################
## Declare ROS messages and services ##
#######################################

# Declare the message files to be built
add_service_files(FILES
  BroadcastTransform.srv
  ClearTransforms.srv
  GetTransforms.srv
  RemoveTransform.srv
)

# Actually generate the language-specific message and service files
generate_messages(DEPENDENCIES std_msgs geometry_msgs)

catkin_package(
  CATKIN_DEPENDS message_runtime std_msgs geometry_msgs
)

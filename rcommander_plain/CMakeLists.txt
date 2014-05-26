cmake_minimum_required(VERSION 2.8.3)
project(rcommander_plain)

## Find catkin macros and libraries
find_package(catkin REQUIRED COMPONENTS
  rospy
  rcommander
)

catkin_python_setup()
catkin_package()

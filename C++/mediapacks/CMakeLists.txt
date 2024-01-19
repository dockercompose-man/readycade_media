cmake_minimum_required(VERSION 3.5)

project(MediaPackSelector)

find_package(Qt5 COMPONENTS Core Widgets REQUIRED)

set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)

add_executable(MediaPackSelector main.cpp)

target_link_libraries(MediaPackSelector PRIVATE Qt5::Core Qt5::Widgets)
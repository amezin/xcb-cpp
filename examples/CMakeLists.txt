find_library(XCB_RANDR_LIBRARY NAMES xcb-randr)
if(NOT XCB_RANDR_LIBRARY)
    message(FATAL_ERROR "Can't find libxcb-randr")
endif()

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++0x")
add_executable(randr_test randr_test.cpp)
target_link_libraries(randr_test xcb "${XCB_RANDR_LIBRARY}")

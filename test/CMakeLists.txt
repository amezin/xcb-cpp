find_library(XCB_LIBRARY NAMES xcb)
if(NOT XCB_LIBRARY)
    message(FATAL_ERROR "Can't find libxcb")
endif()

file(GLOB TEST_SRCS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

create_test_sourcelist(TEST_ALL_SRCS test_main.cpp ${TEST_SRCS})
add_executable(tests ${TEST_ALL_SRCS})
add_dependencies(tests headers)
target_link_libraries(tests ${XCB_LIBRARY})

foreach(test ${TEST_SRCS})
    get_filename_component(test_we "${test}" NAME_WE)
    add_test("${test_we}" tests "${test_we}")
endforeach()


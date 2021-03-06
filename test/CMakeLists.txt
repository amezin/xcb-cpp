foreach(file ${generated})
    get_filename_component(we "${file}" NAME_WE)
    set(cpp_file "${CMAKE_CURRENT_BINARY_DIR}/${we}_check_compiles.cpp")
    configure_file("${CMAKE_CURRENT_SOURCE_DIR}/check_compiles.cpp.in"
                   "${cpp_file}" @ONLY ESCAPE_QUOTES)
    add_executable("${we}_check_compiles" "${cpp_file}")
    add_dependencies("${we}_check_compiles" headers)
    target_link_libraries("${we}_check_compiles" xcb)
endforeach()

file(GLOB TEST_SRCS
     RELATIVE "${CMAKE_CURRENT_SOURCE_DIR}"
     "${CMAKE_CURRENT_SOURCE_DIR}/*.cpp")

create_test_sourcelist(TEST_ALL_SRCS test_main.cpp ${TEST_SRCS})
add_executable(tests ${TEST_ALL_SRCS})
add_dependencies(tests headers)
target_link_libraries(tests xcb)

foreach(test ${TEST_SRCS})
    get_filename_component(test_we "${test}" NAME_WE)
    add_test("${test_we}" tests "${test_we}")
endforeach()

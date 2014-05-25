foreach(XCB_HEADER ${XCB_HEADERS})
    get_filename_component(XCB_HEADER_BASENAME "${XCB_HEADER}" NAME_WE)
    configure_file("${CMAKE_CURRENT_SOURCE_DIR}/test_syntax.cpp.in"
                   "${CMAKE_CURRENT_BINARY_DIR}/test_syntax_${XCB_HEADER_BASENAME}.cpp"
                   @ONLY)
    add_executable(test_syntax_${XCB_HEADER_BASENAME} EXCLUDE_FROM_ALL
                   "${CMAKE_CURRENT_BINARY_DIR}/test_syntax_${XCB_HEADER_BASENAME}.cpp")
    add_test(test_syntax_${XCB_HEADER_BASENAME}
             ${CMAKE_COMMAND}
             --build ${CMAKE_BINARY_DIR}
             --target test_syntax_${XCB_HEADER_BASENAME})
endforeach()

set(TEST_SRCS
    unchecked_atom_intern.cpp
    checked_atom_intern.cpp
   )

create_test_sourcelist(TEST_ALL_SRCS test_main.cpp ${TEST_SRCS})
add_executable(tests ${TEST_ALL_SRCS})
target_link_libraries(tests xcb)

foreach(test ${TEST_SRCS})
    string(REGEX REPLACE "\\.[0-9a-zA-Z]+$" "" test_we "${test}")
    add_test("${test_we}" tests "${test_we}")
endforeach()

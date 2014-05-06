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

project(xcb-cpp)
cmake_minimum_required(VERSION 2.6)

find_package(PythonInterp REQUIRED)

set(XCB_SKIP "ge;xf86vidmode" CACHE STRING "Exclude some extensions")

find_path(XCB_PROTO_DIR "xcb.xsd" PATHS /usr/share PATH_SUFFIXES xcb)
file(GLOB XCB_PROTO_XMLS "${XCB_PROTO_DIR}/*.xml")

function(generate output xml)
    if(xml STREQUAL "")
        unset(extra_args)
        unset(extra_dep)
    else()
        set(extra_args --xml "${xml}")
        set(extra_dep "${xml}")
    endif()
    add_custom_command(OUTPUT "${output}"
                       COMMAND "${PYTHON_EXECUTABLE}"
                               "${CMAKE_CURRENT_SOURCE_DIR}/cxx_client.py"
                               ${extra_args}
                               "${output}"
                       DEPENDS "${CMAKE_CURRENT_BINARY_DIR}/c_client.py"
                               "${CMAKE_CURRENT_SOURCE_DIR}/cxx_client.py"
                               ${extra_dep})
endfunction()

add_custom_command(OUTPUT "${CMAKE_CURRENT_BINARY_DIR}/c_client.py"
                   COMMAND "${CMAKE_COMMAND}"
                           -DINPUT="${CMAKE_CURRENT_SOURCE_DIR}/libxcb/src/c_client.py"
                           -DOUTPUT="${CMAKE_CURRENT_BINARY_DIR}/c_client.py"
                           -P "${CMAKE_CURRENT_SOURCE_DIR}/make_c_client.cmake"
                   DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/make_c_client.cmake"
                           "${CMAKE_CURRENT_SOURCE_DIR}/libxcb/src/c_client.py")

foreach(file ${XCB_PROTO_XMLS})
    get_filename_component(name "${file}" NAME_WE)
    list(FIND XCB_SKIP "${name}" skip)
    if(skip EQUAL -1)
        generate("${CMAKE_CURRENT_BINARY_DIR}/${name}.hpp" "${file}")
        set(generated ${generated} "${CMAKE_CURRENT_BINARY_DIR}/${name}.hpp")
    else()
        message(STATUS "Skipping ${name}")
    endif()
endforeach()

generate("${CMAKE_CURRENT_BINARY_DIR}/xcb.hpp" "")
set(generated ${generated} "${CMAKE_CURRENT_BINARY_DIR}/xcb.hpp")

add_custom_target(headers ALL DEPENDS ${generated})

include(CTest)
if(BUILD_TESTING)
    include_directories("${CMAKE_CURRENT_BINARY_DIR}")
    add_subdirectory(test)
endif()

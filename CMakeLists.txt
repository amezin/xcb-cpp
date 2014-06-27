cmake_minimum_required(VERSION 2.8)
project(xcb-cpp)

find_package(PythonInterp 3 REQUIRED)

find_path(XCB_INCLUDE_DIR xcb/xcb.h)
if(NOT XCB_INCLUDE_DIR)
    message(FATAL_ERROR "Can't find XCB headers")
endif()

set(xcb_headers
    bigreq.h
    composite.h
    damage.h
    dpms.h
    dri2.h
    dri3.h
    glx.h
    present.h
    randr.h
    record.h
    render.h
    res.h
    screensaver.h
    shape.h
    shm.h
    sync.h
    xc_misc.h
    xevie.h
    xf86dri.h
    xfixes.h
    xinerama.h
    xinput.h
    xkb.h
    xprint.h
    xproto.h
    xselinux.h
    xtest.h
    xv.h
    xvmc.h
   )

unset(generated_headers)
foreach(header ${xcb_headers})
    if(EXISTS "${XCB_INCLUDE_DIR}/xcb/${header}")
        add_custom_command(OUTPUT "${header}pp"
                           COMMAND "${PYTHON_EXECUTABLE}"
                                   "${CMAKE_CURRENT_SOURCE_DIR}/generator/cxx_client.py"
                                   "${XCB_INCLUDE_DIR}/xcb/${header}"
                           DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/generator/ast_util.py"
                                   "${CMAKE_CURRENT_SOURCE_DIR}/generator/cxx_client.py"
                                   "${CMAKE_CURRENT_SOURCE_DIR}/generator/namespaces.py"
                                   "${CMAKE_CURRENT_SOURCE_DIR}/generator/parse.py"
                                   "${CMAKE_CURRENT_SOURCE_DIR}/generator/template.h")
        list(APPEND generated_headers "${header}pp")
    else()
        message("Header ${header} isn't found, skipping")
    endif()
endforeach()

add_definitions(-Wall)
add_custom_target(headers ALL DEPENDS ${generated_headers})

include(CTest)
if(BUILD_TESTING)
    include_directories("${CMAKE_CURRENT_BINARY_DIR}"
                        "${CMAKE_CURRENT_SOURCE_DIR}"
                        "${XCB_INCLUDE_DIR}")
    add_subdirectory(test)
endif()

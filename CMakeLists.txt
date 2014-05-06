project(xcb-cpp)
cmake_minimum_required(VERSION 2.8)

find_path(XCB_INCLUDE_DIR xcb/xcb.h)

file(GLOB XCB_HEADERS RELATIVE "${XCB_INCLUDE_DIR}" "${XCB_INCLUDE_DIR}/xcb/*.h")

file(READ "${CMAKE_CURRENT_SOURCE_DIR}/reply.hpp.in" REPLY_TEMPLATE)
file(READ "${CMAKE_CURRENT_SOURCE_DIR}/void_call.hpp.in" VOID_CALL_TEMPLATE)

function(generate_call OUTPUT XCB_CALL_NAME TEMPLATE ORIGINAL_CONTENT)
    string(REGEX REPLACE "^xcb_" "" CALL_NAME "${XCB_CALL_NAME}")

    string(REGEX MATCH "${XCB_CALL_NAME}[ \\t\\r\\n]*\\([^)]*\\)" SIGNATURE "${ORIGINAL_CONTENT}")
    string(REGEX REPLACE "^${XCB_CALL_NAME}[ \\t\\r\\n]*\\(" "" CALL_ARGS "${SIGNATURE}")
    string(REGEX REPLACE "\\)$" "" CALL_ARGS "${CALL_ARGS}")
    string(REGEX MATCHALL "[^,)]+" CALL_ARGS_LIST "${CALL_ARGS}")

    unset(CONN_ARG)
    foreach(CALL_ARG ${CALL_ARGS_LIST})
        string(STRIP "${CALL_ARG}" CALL_ARG)
        string(REGEX MATCHALL "[a-z_]+" IDENTIFIERS "${CALL_ARG}")
        list(GET IDENTIFIERS -1 ARG_NAME)
        if(NOT ARG_NAMES)
            set(ARG_NAMES "${ARG_NAME}")

            list(FIND IDENTIFIERS "xcb_connection_t" CONN_FOUND)
            if(CONN_FOUND EQUAL -1)
                break()
            else()
                set(CONN_ARG "${ARG_NAME}")
            endif()
        else()
            set(ARG_NAMES "${ARG_NAMES}, ${ARG_NAME}")
        endif()
    endforeach()

    if(CONN_ARG)
        string(CONFIGURE "${TEMPLATE}" CONFIGURED @ONLY)
        set(${OUTPUT} "${CONFIGURED}" PARENT_SCOPE)
    else()
        set(${OUTPUT} "" PARENT_SCOPE)
    endif()
endfunction()

foreach(XCB_HEADER ${XCB_HEADERS})
    unset(ORIGINAL_CONTENT)

    file(READ "${XCB_INCLUDE_DIR}/${XCB_HEADER}" ORIGINAL_CONTENT)
    string(REGEX REPLACE "/\\*([^*]|(\\*+[^*/]))*\\*+/" ""
           ORIGINAL_CONTENT "${ORIGINAL_CONTENT}")
    string(REGEX REPLACE "{[^}]*}" ""
           ORIGINAL_CONTENT "${ORIGINAL_CONTENT}")

    unset(REPLY_TYPES)
    string(REGEX MATCHALL "[a-z_]+_reply_t" REPLY_TYPES "${ORIGINAL_CONTENT}")
    list(REMOVE_DUPLICATES REPLY_TYPES)

    unset(CONTENT)
    foreach(REPLY_TYPE ${REPLY_TYPES})
        string(REGEX REPLACE "_reply_t$" "" XCB_CALL_NAME "${REPLY_TYPE}")
        generate_call(REPLY "${XCB_CALL_NAME}" "${REPLY_TEMPLATE}" "${ORIGINAL_CONTENT}")
        set(CONTENT "${CONTENT}\n${REPLY}")
    endforeach()

    unset(VOID_CALLS)
    string(REGEX MATCHALL "[a-z_]+_checked" VOID_CALLS "${ORIGINAL_CONTENT}")
    list(REMOVE_DUPLICATES VOID_CALLS)
    foreach(XCB_CALL_NAME ${VOID_CALLS})
        generate_call(VOID_CALL "${XCB_CALL_NAME}" "${VOID_CALL_TEMPLATE}" "${ORIGINAL_CONTENT}")
        set(CONTENT "${CONTENT}\n${VOID_CALL}")
    endforeach()

    get_filename_component(XCB_HEADER_BASENAME "${XCB_HEADER}" NAME_WE)

    configure_file("${CMAKE_CURRENT_SOURCE_DIR}/template.hpp.in"
                   "${CMAKE_CURRENT_BINARY_DIR}/${XCB_HEADER_BASENAME}.hpp")
endforeach()

include_directories(SYSTEM "${XCB_INCLUDE_DIR}")
include_directories("${CMAKE_CURRENT_SOURCE_DIR}")
include_directories("${CMAKE_CURRENT_BINARY_DIR}")

include(CTest)
if(BUILD_TESTING)
    add_subdirectory(test)
endif()

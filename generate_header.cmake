set(ENV{PYTHONPATH} "${PYTHONPATH}:$ENV{PYTHONPATH}")
if(XML)
    execute_process(COMMAND "${PYTHON_EXECUTABLE}"
                            "${CXX_CLIENT}"
                            --xml "${XML}"
                            "${OUTPUT}"
                    RESULT_VARIABLE result)
else()
    execute_process(COMMAND "${PYTHON_EXECUTABLE}"
                            "${CXX_CLIENT}"
                            "${OUTPUT}"
                    RESULT_VARIABLE result)
endif()
if(NOT result EQUAL 0)
    message(FATAL_ERROR "Errors while generating ${OUTPUT}")
endif()

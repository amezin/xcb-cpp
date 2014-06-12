file(READ "${INPUT}" contents)
string(FIND "${contents}" "# Boilerplate below this point" end_of_lib)
string(SUBSTRING "${contents}" 0 ${end_of_lib} contents)
file(WRITE "${OUTPUT}" "${contents}")

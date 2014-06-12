#include "xproto.hpp"

#include <cassert>
#include <cstring>

int intern_atom(int, char **)
{
    xcb_connection_t *conn = xcb_connect(0, 0);
    const char *atom_name = "PRIMARY";
    xcb::intern_atom atom(1, std::strlen(atom_name), atom_name, conn);
    assert(atom->atom);
    return EXIT_SUCCESS;
}

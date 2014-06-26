#include "xproto.hpp"

#include <cassert>

int intern_atom(int, char **)
{
    xcb_connection_t *conn = xcb_connect(0, 0);
    const char *atom_name = "PRIMARY";
    xcb::intern_atom atom(conn, 1, atom_name);
    assert(atom->atom());
    return EXIT_SUCCESS;
}


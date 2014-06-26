#include "xproto.hpp"

#include <cassert>

int exception(int, char **)
{
    xcb_connection_t *c = xcb_connect(0, 0);
    xcb::get_atom_name name(c, -1);
    try {
        name->name();
        assert(!"No exception thrown");
    } catch (xcb::request_error &) {
        return EXIT_SUCCESS;
    }
    return EXIT_FAILURE;
}


#include <cassert>
#include <cstring>

#include "test_connection.hpp"

#include "xproto.hpp"

int checked_atom_intern(int, char **)
{
    const char *name = "Device Enabled";
    uint16_t size = std::strlen(name);

    test_connection conn;
    xcb::intern_atom atom(conn, 1, size, name);
    assert(atom.reply());
    assert(!atom.error());
    assert(atom->atom);

    return EXIT_SUCCESS;
}

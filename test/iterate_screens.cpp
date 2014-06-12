#include "xproto.hpp"

#include <cassert>
#include <vector>
#include <iterator>

int iterate_screens(int, char **)
{
    xcb_connection_t *conn = xcb_connect(0, 0);
    xcb_screen_iterator_t i = xcb_setup_roots_iterator(xcb_get_setup(conn));
    std::vector<xcb_screen_t> screens;
    std::copy(i, xcb::end(i), std::back_inserter(screens));
    assert(screens.size() == xcb_setup_roots_length(xcb_get_setup(conn)));
    return EXIT_SUCCESS;
}

#include "xproto.hpp"

#include <vector>
#include <cassert>

int list(int, char **)
{
    xcb_connection_t *c = xcb_connect(0, 0);
    xcb::get_modifier_mapping modmap(c);
    std::vector<xcb::keycode_t> keycodes;
    std::copy(modmap->keycodes().begin(), modmap->keycodes().end(),
              std::back_inserter(keycodes));
    assert(static_cast<int>(keycodes.size()) == modmap->keycodes().size());
    for (int i = 0; i < modmap->keycodes().size(); i++) {
        assert(modmap->keycodes()[i] == keycodes[i]);
    }
    return EXIT_SUCCESS;
}


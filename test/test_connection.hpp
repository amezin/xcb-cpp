#pragma once

#include <cassert>

#include <xcb/xcb.h>

class test_connection
{
public:
    test_connection()
        : connection_(xcb_connect(NULL, NULL))
    {
        assert(connection_);
    }

    ~test_connection()
    {
        xcb_disconnect(connection_);
    }

    operator xcb_connection_t *() const
    {
        return connection_;
    }

private:
    test_connection(const test_connection &);
    test_connection &operator =(const test_connection &);

    xcb_connection_t *connection_;
};

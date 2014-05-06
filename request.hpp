#pragma once

#include <algorithm>
#include <cassert>

#include <xcb/xcb.h>

namespace xcb
{

namespace detail
{

template<typename Cookie>
class cookie_wrapper
{
public:
    cookie_wrapper()
        : connection_(NULL)
    {
        invalidate();
    }

    cookie_wrapper(xcb_connection_t *connection, Cookie cookie)
        : connection_(connection), cookie_(cookie)
    {
    }

    xcb_connection_t *connection() const
    {
        return connection_;
    }

    void discard()
    {
        if (valid()) {
            xcb_discard_reply(connection_, sequence());
            invalidate();
        }
    }

protected:

    Cookie cookie() const
    {
        return cookie_;
    }

    unsigned int sequence() const
    {
        return cookie_.sequence;
    }

    bool valid() const
    {
        return sequence() != 0U;
    }

    void invalidate()
    {
        cookie_.sequence = 0U;
    }

    ~cookie_wrapper()
    {
        discard();
    }

    void swap(cookie_wrapper<Cookie> &rhs)
    {
        std::swap(connection_, rhs.connection_);
        std::swap(cookie_, rhs.cookie_);
    }

private:
    cookie_wrapper(const cookie_wrapper &);
    cookie_wrapper &operator =(const cookie_wrapper &);

    xcb_connection_t *connection_;
    Cookie cookie_;
};

class unchecked_error_policy
{
protected:
    ~unchecked_error_policy()
    {
    }

    void swap(unchecked_error_policy &)
    {
    }

    xcb_generic_error_t **error_storage()
    {
        return NULL;
    }
};

class checked_error_policy
{
protected:
    checked_error_policy()
        : error_(NULL)
    {
    }

    ~checked_error_policy()
    {
        std::free(error_);
    }

    xcb_generic_error_t **error_storage()
    {
        return &error_;
    }

    void swap(checked_error_policy &rhs)
    {
        std::swap(error_, rhs.error_);
    }

private:
    checked_error_policy(const checked_error_policy &);
    checked_error_policy &operator =(const checked_error_policy &);

    xcb_generic_error_t *error_;
};

template<typename Reply>
struct reply_traits;

template<typename Reply, class ErrorPolicy>
class request_base
        : public cookie_wrapper<typename reply_traits<Reply>::cookie_type>,
          protected ErrorPolicy
{
public:
    typedef reply_traits<Reply> traits_type;
    typedef typename traits_type::cookie_type cookie_type;

    request_base(xcb_connection_t *connection, cookie_type cookie)
        : cookie_wrapper<cookie_type>(connection, cookie), reply_(NULL)
    {
    }

    const Reply *reply()
    {
        fetch();
        return reply_;
    }

    const Reply *operator ->()
    {
        return reply();
    }

    const Reply &operator *()
    {
        return *reply();
    }

    void swap(request_base<Reply, ErrorPolicy> &rhs)
    {
        std::swap(reply_, rhs.reply_);
        cookie_wrapper<cookie_type>::swap(rhs);
        ErrorPolicy::swap(rhs);
    }

protected:
    ~request_base()
    {
        std::free(reply_);
    }

    void fetch()
    {
        if (cookie_wrapper<cookie_type>::valid()) {
            reply_ = traits_type::get_reply(cookie_wrapper<cookie_type>::connection(),
                                            cookie_wrapper<cookie_type>::cookie(),
                                            ErrorPolicy::error_storage());
            cookie_wrapper<cookie_type>::invalidate();
        }
    }

private:
    request_base(const request_base<Reply, ErrorPolicy> &);
    request_base<Reply, ErrorPolicy> &operator =(const request_base<Reply, ErrorPolicy> &);

    Reply *reply_;
};

template<>
class request_base<void, unchecked_error_policy>
{
};

template<>
class request_base<void, checked_error_policy>
        : public cookie_wrapper<xcb_void_cookie_t>,
          protected checked_error_policy
{
public:
    typedef xcb_void_cookie_t cookie_type;

    request_base(xcb_connection_t *connection, cookie_type cookie)
        : cookie_wrapper<cookie_type>(connection, cookie)
    {
    }

    void swap(request_base<void, checked_error_policy> &rhs)
    {
        cookie_wrapper<xcb_void_cookie_t>::swap(rhs);
        checked_error_policy::swap(rhs);
    }

protected:
    ~request_base()
    {
    }

    void fetch()
    {
        if (cookie_wrapper<cookie_type>::valid()) {
            *checked_error_policy::error_storage() =
                    xcb_request_check(cookie_wrapper<cookie_type>::connection(),
                                      cookie_wrapper<cookie_type>::cookie());
            cookie_wrapper<cookie_type>::invalidate();
        }
    }
};

}

template<typename Reply>
class unchecked
        : public detail::request_base<Reply, detail::unchecked_error_policy>
{
private:
    typedef detail::request_base<Reply, detail::unchecked_error_policy> base_type;

public:
    typedef typename base_type::cookie_type cookie_type;

    unchecked(xcb_connection_t *connection, cookie_type cookie)
        : base_type(connection, cookie)
    {
    }
};

template<>
class unchecked<void>
{
};

template<typename Reply>
class checked
        : public detail::request_base<Reply, detail::checked_error_policy>
{
private:
    typedef detail::request_base<Reply, detail::checked_error_policy> base_type;

public:
    typedef typename base_type::cookie_type cookie_type;

    checked(xcb_connection_t *connection, cookie_type cookie)
        : base_type(connection, cookie)
    {
    }

    const xcb_generic_error_t *error()
    {
        base_type::fetch();
        return *detail::checked_error_policy::error_storage();
    }
};

}

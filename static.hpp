#pragma once

#include <cstdlib>
#include <algorithm>
#include <limits>
#include <string>
#include <exception>
#include <iterator>

#include <xcb/xcb.h>

namespace xcb
{

template<typename T> class ref;

template<typename T>
ref<T> make_ref(const T *ptr)
{
    return ref<T>(ptr);
}

template<typename T, typename Size=int, typename Reference=const T &>
class list
{
public:
    list()
        : data_(NULL), size_(0)
    {
    }

    list(const T *data, Size size)
        : data_(data), size_(size)
    {
    }

    const T *data() const
    {
        return data_;
    }

    Size size() const
    {
        return size_;
    }

    Size length() const
    {
        return size_;
    }

    Reference operator[](std::ptrdiff_t off) const
    {
        return Reference(data_[off]);
    }

    class iterator : public std::iterator<std::random_access_iterator_tag,
                                          T,
                                          std::ptrdiff_t,
                                          const T*,
                                          Reference>
    {
    public:
        iterator(const T *ptr = NULL)
            : ptr_(ptr)
        {
        }

        Reference operator *() const
        {
            return *ptr_;
        }

        iterator operator +(std::ptrdiff_t off)
        {
            return iterator(ptr_ + off);
        }

        iterator operator -(std::ptrdiff_t off)
        {
            return iterator(ptr_ - off);
        }

        iterator &operator +=(std::ptrdiff_t off)
        {
            return *this = *this + off;
        }

        iterator operator -=(std::ptrdiff_t off)
        {
            return *this = *this - off;
        }

        iterator &operator ++()
        {
            return *this += 1;
        }

        iterator &operator --()
        {
            return *this -= 1;
        }

        iterator &operator ++(int)
        {
            iterator old(this);
            *this += 1;
            return old;
        }

        iterator &operator --(int)
        {
            iterator old(this);
            *this -= 1;
            return old;
        }

        std::ptrdiff_t operator -(iterator r)
        {
            return ptr_ - r.ptr_;
        }

        bool operator ==(const iterator &r) const
        {
            return ptr_ == r.ptr_;
        }

        bool operator !=(const iterator &r) const
        {
            return ptr_ != r.ptr_;
        }

        bool operator <=(const iterator &r) const
        {
            return ptr_ <= r.ptr_;
        }

        bool operator >=(const iterator &r) const
        {
            return ptr_ >= r.ptr_;
        }

        bool operator <(const iterator &r) const
        {
            return ptr_ < r.ptr_;
        }

        bool operator >(const iterator &r) const
        {
            return ptr_ > r.ptr_;
        }
    private:
        const T *ptr_;
    };

    iterator begin() const
    {
        return data_;
    }

    iterator end() const
    {
        return data_ + size_;
    }

private:
    const T *data_;
    Size size_;
};

template<typename Size=int>
class string : public list<char, Size>
{
public:
    string()
    {
    }

    string(const char *data)
        : list<char, Size>(data, strlen(data))
    {
    }

    string(const char *data, Size size)
        : list<char, Size>(data, size)
    {
    }

    string(const std::string &s)
        : list<char, Size>(s.c_str(), to_size(s.size()))
    {
    }

    operator std::string() const
    {
        return std::string(list<char, Size>::data(), list<char, Size>::size());
    }

private:
    static Size strlen(const char *data)
    {
        Size len = 0;
        while (data[len] && len < std::numeric_limits<Size>::max()) {
            ++len;
        }
        return len;
    }

    static Size to_size(std::string::size_type s)
    {
        if (s > std::numeric_limits<Size>::max()) {
            return std::numeric_limits<Size>::max();
        } else {
            return static_cast<Size>(s);
        }
    }
};

xcb_connection_t *default_connection();

class error : public std::exception
{
public:
    const char *what() const throw()
    {
        return "xcb::error";
    }
};

class connection_error : public error
{
public:
    explicit connection_error(int error_code)
        : error_code_(error_code)
    {
    }

    const char *what() const throw()
    {
        return "xcb::connection_error";
    }

    int error_code() const throw()
    {
        return error_code_;
    }

    static void check_connection(xcb_connection_t *c)
    {
        int result = xcb_connection_has_error(c);
        if (result) {
            throw connection_error(result);
        }
    }
private:
    int error_code_;
};

class request_error : public error
{
public:
    explicit request_error(const xcb_generic_error_t &error)
        : error_(error)
    {
    }

    const char *what() const throw()
    {
        return "xcb::request_error";
    }

    const xcb_generic_error_t &error() const throw()
    {
        return error_;
    }
private:
    xcb_generic_error_t error_;
};

}


//template header(header, root, fixes)
#pragma once

#include <xcb/xcb.h>

//{if header.file_name != 'xcb.h':
extern "C"
{
//{for name, fix in fixes.items():
#define $name $fix
//}
#include <xcb/${header.file_name}>
//{for name in fixes.keys():
#undef $name
//}
}
//}

#include "static.hpp"

$root
//end template

//template typedef(name)
typedef ::${name.full} ${name.short};
//end template

//template struct_ref(name, methods, lists, fields)
template<>
class ref< ${name.qualified} >
{
public:

    ref(const ${name.qualified} *ptr = NULL)
        : ptr_(ptr)
    {
    }

    explicit ref(const ${name.qualified} &r)
        : ptr_(&r)
    {
    }

    operator const ${name.qualified} *() const
    {
        return ptr_;
    }

//{for method in methods.values():
    ${method.return_type} ${method.name}() const
    {
        return ${method.call_name}(ptr_);
    }
//}
//{for field in fields:
    ${field.return_type} ${field.name}() const
    {
        return ptr_->${field.call_name};
    }
//}
//{for field in lists:
    ${field.return_type} ${field.name}() const
    {
        return ${field.return_type}(${field.call_name}(ptr_),
                                    ${field.call_name}_length(ptr_));
    }
//}

private:
    const ${name.qualified} *ptr_;
};
//end template

//template request_ctor(func_name, args, call_args, checked, reply_type, with_connection)
    ${func_name.short}(${'xcb_connection_t *c' if with_connection else ''}
        ${', ' if with_connection and args else ''}${', '.join(str(arg) for arg in args)})
        : connection_(${'c' if with_connection else '::xcb::default_connection()'})
        , cookie_(${func_name.full}(connection_${', ' if call_args else ''}${', '.join(call_args)}))
//{if checked:
        , error_(NULL)
//}
//{if reply_type:
        , reply_(NULL)
//}
    {
        ::xcb::connection_error::check_connection(connection_);
    }
//end template

//template request(func_name, args, call_args, checked, cookie_type, reply_type, reply_func)
class ${func_name.short}
{
public:
${request_ctor(func_name, args, call_args, checked, reply_func, True)}
${request_ctor(func_name, args, call_args, checked, reply_func, False)}

    ~${func_name.short}()
    {
        if (!done()) {
            xcb_discard_reply(connection_, cookie_.sequence);
        }
//{if checked:
        std::free(error_);
//}
//{if reply_type:
        std::free(reply_);
//}
    }

    void swap(${func_name.short} &r)
    {
        std::swap(connection_, r.connection_);
        std::swap(cookie_, r.cookie_);
//{if checked:
        std::swap(error_, r.error_);
//}
//{if reply_type:
        std::swap(reply_, r.reply_);
//}
    }

    ${cookie_type} cookie() const
    {
        return cookie_;
    }

    xcb_connection_t *connection() const
    {
        return connection_;
    }

    bool done() const
    {
        return cookie_.sequence == 0;
    }

    bool success()
    {
//{if checked:
        if (error()) {
            return false;
        }
//}
//{if reply_type:
        if (reply()) {
            return true;
        }
//}
        return !xcb_connection_has_error(connection_);
    }

//{if checked:
    const xcb_generic_error_t *error()
    {
        process();
        return error_;
    }

    xcb_generic_error_t *take_error()
    {
        process();
        xcb_generic_error_t *v = error_;
        error_ = NULL;
        return v;
    }
//}

//{if reply_type:
    ${reply_type} reply()
    {
        process();
        return reply_;
    }

    ${reply_type.base_type} *take_reply()
    {
        process();
        ${reply_type.base_type} *v = reply_;
        reply_ = NULL;
        return v;
    }

    ${reply_type} operator *()
    {
        process();
        throw_if_error();
        return reply_;
    }

    const ${reply_type} *operator ->()
    {
        **this;
        return reinterpret_cast< ${reply_type} *>(&reply_); /* Ugly hack */
    }
//}


private:
    void process()
    {
        if (!done()) {
//{if checked and not reply_type:
            error_ = xcb_request_check(connection_, cookie_);
//}
//{if reply_type and reply_func:
            reply_ = ${reply_func.full}(connection_, cookie_,
                                        ${'&error_' if checked else 'NULL'});
//}
            cookie_.sequence = 0;
        }
    }

    void throw_if_error()
    {
//{if checked:
        if (error_) {
            throw ::xcb::request_error(*error_);
        }
//}
        ::xcb::connection_error::check_connection(connection_);
    }

    ${func_name.short}(const ${func_name.short} &);
    ${func_name.short} &operator =(const ${func_name.short} &);

    xcb_connection_t *connection_;
    ${cookie_type} cookie_;
//{if checked:
    xcb_generic_error_t *error_;
//}
//{if reply_type:
    ${reply_type.base_type} *reply_;
//}
};
//end template


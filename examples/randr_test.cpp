#include "xproto.hpp"
#include "render.hpp"
#include "randr.hpp"

#include <iostream>
#include <string>
#include <map>

struct output_info {
    output_info()
    {
    }

    output_info(xcb::randr::output_t output, uint32_t mm_width, uint32_t mm_height, const std::string &name)
        : output(output), mm_width(mm_width), mm_height(mm_height), name(name)
    {
    }

    xcb::randr::output_t output;
    uint32_t mm_width, mm_height;
    std::string name;
};

struct crtc_info {
    crtc_info()
    {
    }

    crtc_info(xcb::randr::crtc_t crtc, int16_t x, int16_t y, uint16_t width, uint16_t height)
        : crtc(crtc), x(x), y(y), width(width), height(height), outputs()
    {
    }

    xcb::randr::crtc_t crtc;
    int16_t x, y;
    uint16_t width, height;

    std::map<xcb::randr::output_t, output_info> outputs;
};

static xcb::screen_t *screen;
static std::map<xcb::randr::crtc_t, crtc_info> crtc_infos;

static void die(const char *c)
{
    fputs(c, stderr);
    exit(1);
}

static void update_output(crtc_info& crtc, xcb::randr::output_t output)
{
    xcb::randr::get_output_info info(output, XCB_CURRENT_TIME);
    if (!info.success())
        die("GetOutputInfo failed");

#warning Should an array of uint8_t be converted to string?
    crtc.outputs[output] = output_info(output, info->mm_width(), info->mm_height(),
                                       std::string((const char *)info->name().data(), info->name().size()));
}

static struct output_info *find_output_any(xcb::randr::output_t output, crtc_info **crtc)
{
    for (auto info_pair : crtc_infos) {
        auto it = info_pair.second.outputs.find(output);
        if (it != info_pair.second.outputs.end()) {
            *crtc = &info_pair.second;
            return &it->second;
        }
    }
    return NULL;
}

static void print_state()
{
    std::cout << "Current state:\n";
    for (auto info_pair : crtc_infos) {
        auto crtc = &info_pair.second;
        std::cout << "  CRTC " << crtc->crtc << " at (" << crtc->x << ", " << crtc->y << ") with size ("
                  << crtc->width << ", " << crtc->height << ") and outputs ";
        for (auto info_pair2 : crtc->outputs) {
            auto output = &info_pair2.second;
            std::cout << "[" << output->output << " with size in mm (" << output->mm_width << ", "
                      << output->mm_height << ") and name \"" << output->name << "\"] ";
        }
        std::cout << "\n";
    }
    std::cout << std::flush;
}

static void handle_crtc_change(xcb::randr::crtc_change_t *event)
{
    if (event->mode == XCB_NONE) {
        /* CRTC disabled */
        crtc_infos.erase(event->crtc);

        printf("CRTC 0x%08x disabled\n", event->crtc);
    } else {
        auto it = crtc_infos.find(event->crtc);
        /* CRTC enabled/changed */
        if (it != crtc_infos.end()) {
            auto& info = it->second;
            info.x = event->x;
            info.y = event->y;
            info.width = event->width;
            info.height = event->height;
        } else
            crtc_infos[event->crtc] = crtc_info(event->crtc, event->x, event->y, event->width, event->height);

        /* Update size from event->x etc, possible need to add CRTC */
        printf("CRTC 0x%08x now has geometry (%d, %d), (%d, %d)\n",
               event->crtc, event->x, event->y, event->width, event->height);
    }
    print_state();
}

static void handle_output_change(xcb::randr::output_change_t *event)
{
    struct crtc_info *crtc;
    struct output_info *output = find_output_any(event->output, &crtc);
    if (!output) {
        if (event->crtc == XCB_NONE) {
            fprintf(stderr, "ERROR: Unknown output 0x%08x now disconnected\n", event->output);
            return;
        }
        auto it = crtc_infos.find(event->crtc);
        if (it == crtc_infos.end()) {
            fprintf(stderr, "ERROR: Got output change event for output 0x%08x connected to unknown CRTC 0x%08x\n",
                    event->output, event->crtc);
            return;
        }
        update_output(it->second, event->output);
    } else {
        if (event->crtc != XCB_NONE) {
            auto it = crtc_infos.find(event->crtc);
            if (it == crtc_infos.end()) {
                fprintf(stderr, "ERROR: Output 0x%08x moved to unknown CRTC 0x%08x\n",
                        event->output, event->crtc);
                /* Remove from old CRTC */
                crtc->outputs.erase(event->output);
                return;
            }
            it->second.outputs[event->output] = *output;
            update_output(it->second, event->output);
        }
        /* Remove from old CRTC */
        crtc->outputs.erase(event->output);
    }

    printf("output 0x%08x on CRTC 0x%08x changed\n", event->output, event->crtc);
    print_state();
}

static void handle_event(xcb_generic_event_t *ev)
{
    const xcb_query_extension_reply_t *randr;
    uint8_t type = ev->response_type & 0x7f;
    int sent = !!(ev->response_type & 0x80);

#warning Can this be made nicer?
    randr = xcb_get_extension_data(xcb::default_connection(), &xcb_randr_id);
    if (type == randr->first_event + XCB_RANDR_NOTIFY) {
        xcb_randr_notify_event_t *event = (xcb_randr_notify_event_t *) ev;
        switch (event->subCode) {
        case XCB_RANDR_NOTIFY_CRTC_CHANGE:
            handle_crtc_change(&event->u.cc);
            break;
        case XCB_RANDR_NOTIFY_OUTPUT_CHANGE:
            handle_output_change(&event->u.oc);
            break;
        default:
            fprintf(stderr, "Unhandled RandR Notify event of subcode %d\n", event->subCode);
        }
        return;
    }

    fprintf(stderr, "Unhandled event of type %d%s\n", type, sent ? " (generated)" : "");
}

static void query_state(void)
{
    xcb::randr::get_screen_resources screen_res(screen->root);
    if (!screen_res.success() || screen_res->num_crtcs() < 1)
        die("Something wrong with GetScreenResources");

    for(auto crtc : screen_res->crtcs()) {
        xcb::randr::get_crtc_info crtc_info(crtc, screen_res->config_timestamp());
        if (!crtc_info.success())
            die("GetCRTCInfo failed");
        /* Only if the CRTC is active */
        if (crtc_info->mode() != XCB_NONE) {
            struct crtc_info info(crtc, crtc_info->x(), crtc_info->y(), crtc_info->width(), crtc_info->height());
            for(auto output : crtc_info->outputs()) {
                update_output(info, output);
            }
            crtc_infos[crtc] = info;
        }
    }
}

static void setup_randr(void)
{
    const xcb_query_extension_reply_t *query;

    query = xcb_get_extension_data(xcb::default_connection(), &xcb_randr_id);
    if (!query || !query->present)
        die("RandR not present");

    xcb::randr::query_version version(XCB_RANDR_MAJOR_VERSION, XCB_RANDR_MINOR_VERSION);
    if (!version.reply() || version->major_version() < 1 || (version->major_version() == 1 && version->minor_version() < 2))
        die("RandR too old");

    xcb::randr::select_input req(screen->root, XCB_RANDR_NOTIFY_MASK_CRTC_CHANGE | XCB_RANDR_NOTIFY_MASK_OUTPUT_CHANGE);
}

namespace xcb
{
xcb_connection_t *default_connection()
{
    static xcb_connection_t *c = xcb_connect(NULL, NULL);
    return c;
}
}

int main(void)
{
    xcb_generic_event_t *ev;

    if (xcb_connection_has_error(xcb::default_connection())) {
        die("Error while connecting");
    }

    screen = xcb_setup_roots_iterator(xcb_get_setup(xcb::default_connection())).data;
    setup_randr();
    query_state();
    print_state();
    xcb_flush(xcb::default_connection());

    while ((ev = xcb_wait_for_event(xcb::default_connection())) != NULL) {
        handle_event(ev);
        free(ev);
    }

    xcb_disconnect(xcb::default_connection());
    return 0;
}

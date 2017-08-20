import sublime
import sublime_plugin
import sys
from SublimeLinter import sublimelinter, lint

persist = lint.persist

# Each line index points to (view, line, col) or None
active_line_mapping = []
SLD = "SublimeLinterDashboard"
show_warnings = True
show_help = False


def ensure_dashboard_is_cleared():
    for window in sublime.windows():
        linting_view = window.find_output_panel(SLD)

        if linting_view:
            linting_view.run_command("sublime_linter_dashboard_write", {
                "text": "<Loading>"}
            )


def build_view_by_id_map_for_window(window):
    mapping = {}
    linting_view = None
    for view in window.views():
        mapping[view.id()] = view

    return mapping


def format_file_path(path):
    parts = path.split("/")
    parts.reverse()
    return "/".join(parts)


def show_dashboard():
    active_window = sublime.active_window()
    mapping = build_view_by_id_map_for_window(
        active_window
    )
    syntax_file = 'Packages/SublimeLinter-Dashboard/dashboard.sublime-syntax'

    linting_view = active_window.find_output_panel(SLD)
    if linting_view is None:
        linting_view = active_window.create_output_panel(SLD, False)
        linting_view.set_read_only(True)
        linting_view.set_scratch(True)
        linting_view.set_name(SLD)

        linting_view.set_syntax_file(syntax_file)
        linting_view.sel().clear()
        linting_view.sel().add(sublime.Region(0, 0))

    active_window.run_command("show_panel", {"panel": "output." + SLD})
    active_window.focus_view(linting_view)

    return mapping, linting_view


def focus_error_by_sel(sel_view):

    regions = sel_view.sel()
    if len(regions) == 0:
        return
    row, col = sel_view.rowcol(regions[0].a)

    if row >= len(active_line_mapping):
        return

    if active_line_mapping[row] is None:
        return

    (view, line_number, col_number) = active_line_mapping[row]
    view.window().focus_view(view)
    if line_number is not None:
        point = view.text_point(line_number, col_number)
        view.show_at_center(point)

        view.sel().clear()
        view.sel().add(sublime.Region(point, point))


def get_help():

    return [
      "h:       Toggle help",
      "escape:  Close dashboard",
      "u:       Unfocus dashboard",
      "enter:   Jump to error/warning under cursor (same as double clicking)",
      "s:       Show error/warning under cursor (without focus)",
      "w:       Toggle linter warnings"
    ]


def refresh_dashboard():
    mapping = build_view_by_id_map_for_window(
        sublime.active_window()
    )
    linting_view = sublime.active_window().find_output_panel(SLD)
    if linting_view is None:
        return

    lines = []
    lines.append("Press h for help regarding shortcuts")
    lines.append("")
    global active_line_mapping
    active_line_mapping = ["", ""]

    if show_help:
        lines = lines + get_help()
    else:
        empty_line_length = len(lines)
        for vid, errors in persist.errors.items():
            if len(errors.items()) == 0:
                continue
            if vid not in mapping:
                continue

            view = mapping[vid]
            lines.append(format_file_path(view.file_name()) + ":")
            active_line_mapping.append((view, None, None))

            view_highlights = persist.highlights[vid].all
            for line_number, lineErrors in errors.items():
                highlight_type = None
                for highlight in view_highlights:
                    highlight_set = highlight.lines
                    if line_number in highlight_set:
                        highlight_type = highlight_set[line_number]
                        break

                marker = "!" if highlight_type == "error" else " "
                if show_warnings or highlight_type == "error":
                    for error in lineErrors:
                        col_number, msg = error
                        indent = " " + marker + "  "
                        lines.append(
                            indent + str(line_number + 1) + ": " + msg
                        )
                        active_line_mapping.append(
                            (view, line_number, col_number)
                        )

            lines.append("")
            active_line_mapping.append(None)

        if len(lines) == empty_line_length:
            lines.append("No errors or warnings found!")

    text = "\n".join(lines)

    linting_view.run_command("sublime_linter_dashboard_write", {"text": text})


def unfocus_panel(view):
    window = view.window()
    window.focus_group(window.active_group())


class SublimeLinterDashboard(sublime_plugin.EventListener):

    def on_post_save_async(self, view):
        refresh_dashboard()


class SublimeLinterDashboardWrite(sublime_plugin.TextCommand):

    def run(self, edit, **args):
        self.view.set_read_only(False)
        self.view.replace(
            edit,
            sublime.Region(0, self.view.size()),
            args["text"]
        )
        self.view.set_read_only(True)


class SublimeLinterDashboardEnterCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        unfocus_panel(self.view)
        focus_error_by_sel(self.view)


class SublimeLinterDashboardShowCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        focus_error_by_sel(self.view)


class SublimeLinterDashboardEscCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        self.view.window().destroy_output_panel(SLD)


class SublimeLinterDashboardToggleWarningsCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global show_warnings
        show_warnings = not show_warnings
        refresh_dashboard()


class SublimeLinterDashboardHelpCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        global show_help
        show_help = not show_help
        refresh_dashboard()


class SublimeLinterDashboardUnfocusCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        unfocus_panel(self.view)


class SublimeLinterDashboardDoubleclickCommand(sublime_plugin.TextCommand):
    def run_(self, view, args):
        isDashboard = self.view.name() == SLD

        if isDashboard:
            focus_error_by_sel(self.view)
        else:
            system_command = args["command"] if "command" in args else None
            if system_command:
                system_args = dict({"event": args["event"]}.items())
                system_args.update(dict(args["args"].items()))
                self.view.run_command(system_command, system_args)


class SublimeLinterDashboardOpen(sublime_plugin.WindowCommand):

    def run(self):
        show_dashboard()
        refresh_dashboard()


# Monkey patch SublimeLinter's highlight function so that we receive updates
class Patcher:
    original_highlight = None

    @staticmethod
    def patch_linter():
        Patcher.original_highlight = sublimelinter.SublimeLinter.highlight

        def replacement(self, view, linters, hit_time):
            Patcher.original_highlight(self, view, linters, hit_time)
            refresh_dashboard()

        sublimelinter.SublimeLinter.highlight = replacement

    @staticmethod
    def unpatch_linter():
        if Patcher.original_highlight:
            sublimelinter.SublimeLinter.highlight = Patcher.original_highlight


def plugin_loaded():
    Patcher.patch_linter()
    ensure_dashboard_is_cleared()
    refresh_dashboard()


def plugin_unloaded():
    Patcher.unpatch_linter()

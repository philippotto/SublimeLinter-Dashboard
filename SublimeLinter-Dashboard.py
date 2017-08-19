import sublime
import sublime_plugin
import sys

# from .lint import highlight, linter, persist, util
# slInstance = SublimeLinter.sublimelinter.SublimeLinter()
from SublimeLinter import sublimelinter, lint
# SublimeLinter = sys.modules["SublimeLinter"]
# persist = SublimeLinter.lint.persist
persist = lint.persist

# Each line index points to (view, line, col) or None
active_line_mapping = []

def ensure_dashboard_is_cleared():
	for window in sublime.windows():
		_, linting_view = build_view_by_id_map_for_window(window)
		if linting_view:
			linting_view.run_command("sublime_linter_dashboard_write", {"text": "<Loading>"})


def build_view_by_id_map_for_window(window):
	mapping = {}
	linting_view = None
	for view in window.views():
		mapping[view.id()] = view
		if view.name() == "SublimeLinterDashboard":
			linting_view = view

	return (mapping, linting_view)


def format_file_path(path):
	parts = path.split("/")
	parts.reverse()
	return "/".join(parts)

def show_dashboard():
	mapping, linting_view = build_view_by_id_map_for_window(sublime.active_window())

	if linting_view is None:
		linting_view = sublime.active_window().new_file()
		linting_view.set_read_only(True)
		linting_view.set_scratch(True)
		linting_view.set_name("SublimeLinterDashboard")

		linting_view.set_syntax_file('Packages/SublimeLinter-Dashboard/dashboard.sublime-syntax')
		

	sublime.active_window().focus_view(linting_view)

	return mapping, linting_view

def focus_error_by_sel(selView):

	regions = selView.sel()
	if len(regions) > 0:
		(row, col) = selView.rowcol(regions[0].a)
		if row < len(active_line_mapping) and active_line_mapping[row] is not None:
			(view, line_number, colNumber) = active_line_mapping[row]
			view.window().focus_view(view)
			if line_number is not None:
				point = view.text_point(line_number, colNumber)
				view.show(point)

				view.sel().clear()
				view.sel().add(sublime.Region(point, point))

def refresh_dashboard():

	mapping, linting_view = build_view_by_id_map_for_window(sublime.active_window())
	if linting_view is None:
		return

	lines = []
	global active_line_mapping
	active_line_mapping = []
	sublime.ttt = persist

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
			for error in lineErrors:
				col_number = error[0]
				lines.append(" " + marker + "  " + str(line_number) + ": " + error[1])
				active_line_mapping.append((view, line_number, col_number))

		lines.append("\n")
		active_line_mapping.append(None)
	text = "\n".join(lines)

	linting_view.run_command("sublime_linter_dashboard_write", {"text": text})


class SublimeLinterDashboard(sublime_plugin.EventListener):

	def on_post_save_async(self, view):

		refresh_dashboard()


class SublimeLinterDashboardWrite(sublime_plugin.TextCommand):

	def run(self, edit, **args):
		self.view.set_read_only(False)
		self.view.replace(edit, sublime.Region(0, self.view.size()), args["text"])
		self.view.set_read_only(True)

class SublimeLinterDashboardEnterCommand(sublime_plugin.TextCommand):
	
	def run(self, view):
		focus_error_by_sel(self.view)

class SublimeLinterDashboardDoubleclickCommand(sublime_plugin.TextCommand):
	def run_(self, view, args):
		isDashboard = self.view.name() == "SublimeLinterDashboard"

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



# Monkey patch sublime linter so that we get updates
original_highlight = None

def patch_linter():
	global original_highlight

	original_highlight = sublimelinter.SublimeLinter.highlight

	def replacement(self, view, linters, hit_time):
		original_highlight(self, view, linters, hit_time)
		refresh_dashboard()

	sublimelinter.SublimeLinter.highlight = replacement

def unpatch_linter():
	global original_highlight

	if original_highlight:
		sublimelinter.SublimeLinter.highlight = original_highlight

def plugin_loaded():
	patch_linter()
	ensure_dashboard_is_cleared()
	refresh_dashboard()

def plugin_unloaded():
	unpatch_linter()

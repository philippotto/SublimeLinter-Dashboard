# SublimeLinter-Dashboard

Provides a dashboard like user interface for the [SublimeLinter](https://packagecontrol.io/packages/SublimeLinter) package.
The dashboard is a new view which contains a list of all linting errors/warnings in all views of the active window.
Switching to an warning/error is as simple as double clicking or pressing enter on a line of the view.

# Demo

Screenshots:
![Screenshot](https://github.com/philippotto/SublimeLinter-Dashboard/raw/master/img/Screenshot-Linter-Dashboard.png)
![Screenshot](https://github.com/philippotto/SublimeLinter-Dashboard/raw/master/img/Screenshot-Linter-Dashboard-Help.png)

Screencast:
![Screencast](https://github.com/philippotto/SublimeLinter-Dashboard/raw/master/img/linter-dashboard-screencast.gif)

# Installation

- Ensure that you have [SublimeLinter](https://packagecontrol.io/packages/SublimeLinter) installed for Sublime Text 3 and that it works
- Clone this repository into the package folder of your ST3 installation
- Open "SublimeLinter Dashboard: Open" in the command palette

# Shortcuts

If you want to create a shortcut for opening the dashboard, you can open Preferences > Key Bindings and add the following line:

```
{ "keys": ["alt+shift+d"], "command": "sublime_linter_dashboard_open"}
```

You might want to adapt the shortcut so that it doesn't conflict with existing ones.

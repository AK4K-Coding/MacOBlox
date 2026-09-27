"""GTK 4 / libadwaita interface of the Mac O’ Blox launcher."""

import json
import os
import threading

import gi

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Adw, Gdk, Gio, GLib, Gtk  # noqa: E402

from . import __version__, author, core, dns, i18n, studio  # noqa: E402
from .i18n import _  # noqa: E402

APP_ID = "xyz.narez.MacOBlox"

# Common fast flags. Roblox only honours flags on its client allowlist, so
# some of these may have no effect in a given client version.
PRESETS = [
    {"title": "FPS limit", "subtitle": "GlobalBasicSettings_13 / DFIntTaskSchedulerTargetFps",
     "flag": "DFIntTaskSchedulerTargetFps", "kind": "fps", "default": 144, "min": 30, "max": 1000},
    {"title": "Graphics quality", "subtitle": "DFIntDebugFRMQualityLevelOverride, 1–21",
     "flag": "DFIntDebugFRMQualityLevelOverride", "kind": "number", "default": 10, "min": 1, "max": 21},
    {"title": "MSAA", "subtitle": "FIntDebugForceMSAASamples: 0, 1, 2, 4, 8",
     "flag": "FIntDebugForceMSAASamples", "kind": "number", "default": 4, "min": 0, "max": 8},
    {"title": "No shadows", "subtitle": "FIntRenderShadowIntensity = 0",
     "flag": "FIntRenderShadowIntensity", "kind": "fixed", "value": 0},
    {"title": "No grass", "subtitle": "FIntFRMMinGrassDistance / FIntFRMMaxGrassDistance = 0",
     "flag": ["FIntFRMMinGrassDistance", "FIntFRMMaxGrassDistance"], "kind": "fixed", "value": 0},
    {"title": "Disable post-processing", "subtitle": "FFlagDisablePostFx = True",
     "flag": "FFlagDisablePostFx", "kind": "fixed", "value": True},
    {"title": "Low quality terrain", "subtitle": "FIntTerrainArraySliceSize = 0",
     "flag": "FIntTerrainArraySliceSize", "kind": "fixed", "value": 0},
    {"title": "Disable global wind", "subtitle": "FFlagGlobalWindControl = False",
     "flag": "FFlagGlobalWindControl", "kind": "fixed", "value": False},
    {"title": "Force Voxel lighting", "subtitle": "DFFlagDebugRenderForceTechnologyVoxel = True",
     "flag": "DFFlagDebugRenderForceTechnologyVoxel", "kind": "fixed", "value": True},
    {"title": "Disable telemetry", "subtitle": "FFlagDebugDisableTelemetry = True",
     "flag": "FFlagDebugDisableTelemetry", "kind": "fixed", "value": True},
    {"title": "Texture quality override", "subtitle": "DFIntTextureQualityOverride: 0–3",
     "flag": "DFIntTextureQualityOverride", "kind": "number", "default": 3, "min": 0, "max": 3},
]

DNS_CHOICES = [
    ("system", "System (Darling default)"),
    ("quad9", "Quad9 (9.9.9.9, encrypted)"),
    ("cloudflare", "Cloudflare (1.1.1.1, encrypted)"),
    ("google", "Google (8.8.8.8, encrypted)"),
    ("custom", "Custom"),
]


def _toast(overlay, text):
    toast = Adw.Toast.new(text)
    # Error texts contain <, > and & (compiler output, paths); as markup they
    # would turn the toast empty.
    toast.set_use_markup(False)
    overlay.add_toast(toast)


def _button_row(title):
    """A clickable row; Adw.ButtonRow needs libadwaita 1.6 (Ubuntu 24.04 has 1.5)."""
    if hasattr(Adw, "ButtonRow"):
        return Adw.ButtonRow(title=title)
    return Adw.ActionRow(title=title, activatable=True)


def _error_dialog(window, heading, details):
    """Shows the whole error text, selectable and with a copy button, so
    people can send it. Also kept in ~/.cache/macoblox/last-error.txt."""
    try:
        core.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        (core.CACHE_DIR / "last-error.txt").write_text(f"Mac O’ Blox {__version__}\n{heading}\n\n{details}\n")
    except OSError:
        pass
    dialog = Adw.AlertDialog(heading=heading)
    view = Gtk.TextView(editable=False, monospace=True, wrap_mode=Gtk.WrapMode.WORD_CHAR,
                        top_margin=8, bottom_margin=8, left_margin=8, right_margin=8)
    view.get_buffer().set_text(details)
    scroller = Gtk.ScrolledWindow(child=view, min_content_height=160, max_content_height=360,
                                  propagate_natural_height=True)
    scroller.add_css_class("card")
    dialog.set_extra_child(scroller)
    dialog.add_response("copy", _("Copy"))
    dialog.add_response("close", _("Close"))
    dialog.set_default_response("close")

    def response(_dialog, result):
        if result == "copy":
            window.get_clipboard().set(f"Mac O’ Blox {__version__}\n{heading}\n\n{details}")

    dialog.connect("response", response)
    dialog.present(window)


class PlayPage(Adw.Bin):
    def __init__(self, window):
        super().__init__()
        self.window = window
        toolbar_view = Adw.ToolbarView()

        status = Adw.StatusPage()
        status.set_icon_name("macoblox")
        status.set_title("Mac O’ Blox")
        self.status = status

        center_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12,
                             halign=Gtk.Align.CENTER)

        self.log_button = Gtk.Button(label=_("Open last log"))
        self.log_button.add_css_class("flat")
        self.log_button.set_visible(False)
        self.log_button.connect("clicked", lambda *_args: window.open_last_log())
        center_box.append(self.log_button)

        links = Gtk.Box(spacing=6, halign=Gtk.Align.CENTER, margin_top=14)
        for title, icon, uri in _links():
            button = Gtk.Button(icon_name=icon, tooltip_text=title)
            button.add_css_class("flat")
            button.add_css_class("circular")
            button.connect("clicked", lambda *_args, u=uri: _open_uri(window, u))
            links.append(button)
        center_box.append(links)

        status.set_child(center_box)
        toolbar_view.set_content(status)

        action_bar = Gtk.ActionBar()

        version = Gtk.Label(label=f"Mac O’ Blox {__version__}")
        version.add_css_class("dim-label")
        version.add_css_class("caption")
        action_bar.pack_start(version)

        self.studio_progress = Gtk.ProgressBar(show_text=True, visible=False)
        self.studio_progress.set_size_request(160, -1)
        action_bar.pack_start(self.studio_progress)

        self.play = Gtk.Button(label=_("Play"))
        self.play.add_css_class("suggested-action")
        self.play.add_css_class("pill")
        self.play.set_size_request(130, -1)
        self.play.connect("clicked", lambda *_args: window.play_clicked())
        action_bar.pack_end(self.play)

        self.stop = Gtk.Button(label=_("Stop Roblox"))
        self.stop.add_css_class("destructive-action")
        self.stop.add_css_class("pill")
        self.stop.set_size_request(130, -1)
        self.stop.set_visible(False)
        self.stop.connect("clicked", lambda *_args: window.stop())
        action_bar.pack_end(self.stop)

        self.studio = Gtk.Button(label=_("Roblox Studio"))
        self.studio.add_css_class("pill")
        self.studio.set_size_request(130, -1)
        self.studio.connect("clicked", lambda *_args: window.studio_clicked())
        # Studio needs Wine, which the Flatpak does not have yet.
        self.studio.set_visible(not os.path.exists("/.flatpak-info"))
        action_bar.pack_end(self.studio)

        toolbar_view.add_bottom_bar(action_bar)
        self.set_child(toolbar_view)
        self.refresh()

    def refresh(self):
        running = self.window.session is not None
        busy = self.window.busy
        version = core.installed_version()
        parts = [_("Roblox {version}", version=version) if version else _("Roblox not found")]
        parts.append(_("Darling running") if core.darlingserver_running()
                     else _("Darling starts with the game"))
        if version and not running and not core.signed_in():
            parts.append(_("Sign in with Quick Login"))
        self.status.set_description(" · ".join(parts))
        self.play.set_sensitive(not running and not busy)
        if running:
            self.play.set_label(_("Roblox is running"))
        elif busy == "starting":
            self.play.set_label(_("Starting…"))
        else:
            self.play.set_label(_("Play") if version else _("Install Roblox"))
        self.stop.set_visible(running)
        self.log_button.set_visible(self.window.last_log is not None and not running)


class FlagsPage(Adw.PreferencesPage):
    def __init__(self, window):
        super().__init__(title=_("Fast flags"), icon_name="preferences-other-symbolic")
        self.window = window
        self.flags = core.load_fast_flags()
        self.preset_flags = set()
        self.preset_setters = {}  # flag -> function(value) that shows it in its row
        self._save_timer = 0

        presets = Adw.PreferencesGroup(
            title=_("Popular"),
            description=_("Roblox only applies flags from its allowlist, some flags may have no effect."))
        for preset in PRESETS:
            presets.add(self._preset_row(preset))
        self.add(presets)

        self.custom = Adw.PreferencesGroup(title=_("Custom flags"))
        add_button = Gtk.Button(icon_name="list-add-symbolic", valign=Gtk.Align.CENTER)
        add_button.add_css_class("flat")
        add_button.set_tooltip_text(_("Add flag"))
        add_button.connect("clicked", lambda *_args: self._add_custom_row("", ""))
        import_button = Gtk.Button(label=_("Import JSON"), valign=Gtk.Align.CENTER)
        import_button.add_css_class("flat")
        import_button.connect("clicked", lambda *_args: self._import_dialog())
        suffix = Gtk.Box(spacing=6)
        suffix.append(import_button)
        suffix.append(add_button)
        self.custom.set_header_suffix(suffix)
        self.add(self.custom)
        self.custom_rows = []
        for name, value in self.flags.items():
            if name not in self.preset_flags:
                self._add_custom_row(name, core.format_flag_value(value))

        file_group = Adw.PreferencesGroup()
        path_row = Adw.ActionRow(title=_("File"), subtitle=str(core.FAST_FLAGS))
        path_row.set_subtitle_selectable(True)
        file_group.add(path_row)
        self.add(file_group)

    # -- presets
    def _preset_row(self, preset):
        names = preset["flag"] if isinstance(preset["flag"], list) else [preset["flag"]]
        self.preset_flags.update(names)
        enabled = all(name in self.flags for name in names)
        if preset["kind"] == "fps":
            row = Adw.SpinRow.new_with_range(preset["min"], preset["max"], 1)
            row.set_title(_(preset["title"]))
            row.set_subtitle(preset["subtitle"])
            cap = core.load_framerate_cap(preset["default"])
            current = self.flags.get(names[0], cap)
            row.set_value(float(current) if str(current).lstrip("-").isdigit() else preset["default"])
            enabled = bool(names[0] in self.flags or cap > 0)
            switch = Gtk.Switch(active=enabled, valign=Gtk.Align.CENTER)
            row.add_suffix(switch)

            def apply(*_args):
                if switch.get_active():
                    val = int(row.get_value())
                    core.save_framerate_cap(val)
                    for name in names:
                        self.flags[name] = val
                else:
                    core.save_framerate_cap(-1)
                    for name in names:
                        self.flags.pop(name, None)
                self._save()

            switch.connect("notify::active", apply)
            row.connect("notify::value", lambda *_args: switch.get_active() and apply())

            def set_fps(value):
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return False
                row.set_value(value)
                switch.set_active(True)
                apply()
                return True

            for name in names:
                self.preset_setters[name] = set_fps
            return row
        if preset["kind"] == "number":
            row = Adw.SpinRow.new_with_range(preset["min"], preset["max"], 1)
            row.set_title(_(preset["title"]))
            row.set_subtitle(preset["subtitle"])
            current = self.flags.get(names[0], preset["default"])
            row.set_value(float(current) if str(current).lstrip("-").isdigit() else preset["default"])
            switch = Gtk.Switch(active=enabled, valign=Gtk.Align.CENTER)
            row.add_suffix(switch)

            def apply(*_args):
                for name in names:
                    if switch.get_active():
                        self.flags[name] = int(row.get_value())
                    else:
                        self.flags.pop(name, None)
                self._save()

            switch.connect("notify::active", apply)
            row.connect("notify::value", lambda *_args: switch.get_active() and apply())

            def set_number(value):
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    return False
                row.set_value(value)
                switch.set_active(True)
                apply()
                return True

            for name in names:
                self.preset_setters[name] = set_number
            return row
        row = Adw.SwitchRow(title=_(preset["title"]), subtitle=preset["subtitle"], active=enabled)

        def toggle(*_args):
            for name in names:
                if row.get_active():
                    self.flags[name] = preset["value"]
                else:
                    self.flags.pop(name, None)
            self._save()

        row.connect("notify::active", toggle)

        def set_fixed(value, name):
            if value == preset["value"]:
                row.set_active(True)
            else:
                # Not this preset's value: keep it as a plain flag.
                self.flags[name] = value
                self._save()
            return True

        for name in names:
            self.preset_setters[name] = lambda value, n=name: set_fixed(value, n)
        return row

    # -- custom flags
    def _add_custom_row(self, name, value):
        row = Adw.ExpanderRow(title=name or _("New flag"), subtitle=value)
        name_row = Adw.EntryRow(title=_("Name"))
        name_row.set_text(name)
        value_row = Adw.EntryRow(title=_("Value"))
        value_row.set_text(value)
        remove = Gtk.Button(label=_("Remove"), halign=Gtk.Align.END, margin_top=6, margin_bottom=6,
                            margin_end=12)
        remove.add_css_class("destructive-action")
        row.add_row(name_row)
        row.add_row(value_row)
        holder = Gtk.ListBoxRow(activatable=False, selectable=False)
        holder.set_child(remove)
        row.add_row(holder)
        entry = {"row": row, "name": name_row, "value": value_row}

        def changed(*_args):
            row.set_title(name_row.get_text() or _("New flag"))
            row.set_subtitle(value_row.get_text())
            self._sync_custom()

        name_row.connect("changed", changed)
        value_row.connect("changed", changed)

        def delete(*_args):
            self.custom.remove(row)
            self.custom_rows.remove(entry)
            self._sync_custom()

        remove.connect("clicked", delete)
        self.custom.add(row)
        self.custom_rows.append(entry)
        if not name:
            row.set_expanded(True)

    def _sync_custom(self):
        for name in [n for n in self.flags if n not in self.preset_flags]:
            del self.flags[name]
        for entry in self.custom_rows:
            name = entry["name"].get_text().strip()
            if name and name not in self.preset_flags:
                self.flags[name] = core.parse_flag_value(entry["value"].get_text())
        self._save()

    def _import_dialog(self):
        dialog = Adw.AlertDialog(
            heading=_("Import fast flags"),
            body=_('Paste JSON like {"Flag": value}. Flags are added to the current ones.'))
        view = Gtk.TextView(wrap_mode=Gtk.WrapMode.CHAR, monospace=True)
        view.set_size_request(420, 220)
        scroller = Gtk.ScrolledWindow(child=view, min_content_height=220)
        scroller.add_css_class("card")
        dialog.set_extra_child(scroller)
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("import", _("Import"))
        dialog.set_response_appearance("import", Adw.ResponseAppearance.SUGGESTED)

        def response(_dialog, result):
            if result != "import":
                return
            buffer = view.get_buffer()
            text = buffer.get_text(buffer.get_start_iter(), buffer.get_end_iter(), False)
            try:
                data = json.loads(text)
                if not isinstance(data, dict):
                    raise ValueError
            except ValueError:
                _toast(self.window.toasts, _("This is not a JSON object with flags"))
                return
            existing = {entry["name"].get_text(): entry for entry in self.custom_rows}
            imported = 0
            for name, value in data.items():
                if name in self.preset_flags:
                    # Popular flags live in their own rows above.
                    imported += self.preset_setters[name](value)
                    continue
                if name in existing:
                    existing[name]["value"].set_text(core.format_flag_value(value))
                else:
                    self._add_custom_row(name, core.format_flag_value(value))
                imported += 1
            self._sync_custom()
            _toast(self.window.toasts, _("Imported flags: {count}", count=imported))

        dialog.connect("response", response)
        dialog.present(self.window)

    def _save(self):
        """Save shortly after the last change: typing a value or spinning a
        number would otherwise rewrite the file on every keystroke."""
        if self._save_timer:
            GLib.source_remove(self._save_timer)
        self._save_timer = GLib.timeout_add(300, self._save_now)

    def _save_now(self):
        self._save_timer = 0
        try:
            core.save_fast_flags(self.flags)
        except OSError as error:
            _toast(self.window.toasts, _("Could not save flags: {error}", error=error))
        return False

    def flush(self):
        """Write a pending change now (Roblox reads the file when it starts)."""
        if self._save_timer:
            GLib.source_remove(self._save_timer)
            self._save_now()


class SettingsPage(Adw.Bin):
    def __init__(self, window):
        super().__init__()
        self.window = window
        settings = window.settings

        toolbar_view = Adw.ToolbarView()
        self.stack = Adw.ViewStack()

        # 1. Environment page (Interface, Game, DNS, Diagnostics)
        self.env_page = Adw.PreferencesPage()

        interface = Adw.PreferencesGroup(title=_("Interface"))
        codes = list(i18n.LANGUAGES)
        language = Adw.ComboRow(title=_("Language"),
                                model=Gtk.StringList.new(list(i18n.LANGUAGES.values())))
        language.set_selected(codes.index(i18n.language()))
        language.connect("notify::selected", lambda row, _pspec: window.set_language(
            codes[row.get_selected()]))
        interface.add(language)
        self.env_page.add(interface)

        game = Adw.PreferencesGroup(title=_("Game"))
        sensitivity = Adw.SpinRow.new_with_range(0.1, 5.0, 0.05)
        sensitivity.set_digits(2)
        sensitivity.set_title(_("Camera sensitivity"))
        sensitivity.set_subtitle(_("Mouse movement multiplier while rotating the camera"))
        sensitivity.set_value(settings["mouse_sensitivity"])
        sensitivity.connect("notify::value", lambda row, _pspec: window.set_setting(
            "mouse_sensitivity", round(row.get_value(), 2)))
        game.add(sensitivity)
        menu_bar = Adw.SwitchRow(title=_("Hide the macOS menu bar"),
                                 subtitle=_("The Roblox, Edit, Window… strip at the top of the game window"),
                                 active=settings["hide_menu_bar"])
        menu_bar.connect("notify::active", lambda row, _pspec: window.set_setting(
            "hide_menu_bar", row.get_active()))
        game.add(menu_bar)
        reopen = Adw.SwitchRow(title=_("Show the launcher after Roblox exits"),
                               active=settings["show_launcher_after_exit"])
        reopen.connect("notify::active", lambda row, _pspec: window.set_setting(
            "show_launcher_after_exit", row.get_active()))
        game.add(reopen)
        self.env_page.add(game)

        dns_group = Adw.PreferencesGroup(
            title=_("DNS for Roblox"),
            description=_("Only Roblox uses this server, the rest of the system keeps its own DNS. "
                          "Helps when some Roblox images or servers do not load."))
        dns_codes = [code for code, _label in DNS_CHOICES]
        server = Adw.ComboRow(title=_("DNS server"),
                              model=Gtk.StringList.new([_(label) for _code, label in DNS_CHOICES]))
        current = settings.get("dns", "system")
        server.set_selected(dns_codes.index(current) if current in dns_codes else 0)
        custom = Adw.EntryRow(title=_("Custom server"))
        custom.set_text(settings.get("dns_custom", ""))
        custom.set_show_apply_button(True)
        custom.set_tooltip_text(_("IP address, optionally with :port. Plain DNS, not encrypted."))
        custom.set_visible(current == "custom")

        def dns_changed(row, _pspec):
            code = dns_codes[row.get_selected()]
            window.set_setting("dns", code)
            custom.set_visible(code == "custom")

        def custom_applied(row):
            text = row.get_text().strip()
            try:
                dns.parse_server(text)
            except ValueError as error:
                row.add_css_class("error")
                _toast(window.toasts, str(error))
                return
            row.remove_css_class("error")
            window.set_setting("dns_custom", text)

        server.connect("notify::selected", dns_changed)
        custom.connect("apply", custom_applied)
        dns_group.add(server)
        dns_group.add(custom)
        self.env_page.add(dns_group)

        diagnostics = Adw.PreferencesGroup(
            title=_("Diagnostics"),
            description=_("Detailed logs for debugging. They slow the game down, enable only when needed."))
        for key, title in [("diagnostic_signals", "Backtrace on crashes"),
                           ("trace_udp", "Network tracing (UDP)"),
                           ("trace_lock", "Mouse lock tracing"),
                           ("trace_events", "Mouse event tracing"),
                           ("trace_gl", "OpenGL tracing"),
                           ("trace_keys", "Keyboard tracing"),
                           ("fps_log", "Frame rate in the log")]:
            row = Adw.SwitchRow(title=_(title), subtitle=core.TRACE_ENV[key], active=settings[key])
            row.connect("notify::active", lambda r, _pspec, k=key: window.set_setting(k, r.get_active()))
            diagnostics.add(row)
        logs = _button_row(_("Open logs folder"))
        logs.connect("activated", lambda *_args: self.open_logs())
        diagnostics.add(logs)
        rebuild = _button_row(_("Rebuild shim"))
        rebuild.connect("activated", lambda *_args: self.rebuild())
        diagnostics.add(rebuild)
        restart = _button_row(_("Restart Darling"))
        restart.connect("activated", lambda *_args: self.restart_darling())
        diagnostics.add(restart)
        self.env_page.add(diagnostics)

        self.stack.add_titled_with_icon(self.env_page, "env", _("Environment"), "preferences-system-symbolic")

        # 2. Roblox page (Download, updates, version, account)
        self.roblox_page = Adw.PreferencesPage()

        roblox = Adw.PreferencesGroup(title="Roblox")
        self.version_row = Adw.ActionRow(title=_("Installed version"),
                                         subtitle=core.installed_version() or _("not found"))
        self.update_button = Gtk.Button(label=_("Check for updates"), valign=Gtk.Align.CENTER)
        self._update_handler = self.update_button.connect("clicked", lambda *_args: self.check_updates())
        self.version_row.add_suffix(self.update_button)
        roblox.add(self.version_row)
        self.progress = Gtk.ProgressBar(show_text=True, margin_top=6, margin_bottom=6,
                                        margin_start=12, margin_end=12, visible=False)
        progress_row = Gtk.ListBoxRow(activatable=False, selectable=False, child=self.progress)
        roblox.add(progress_row)
        self.roblox_page.add(roblox)

        account = Adw.PreferencesGroup(title=_("Account"))
        logout = _button_row(_("Sign out"))
        logout.add_css_class("destructive-action")
        logout.connect("activated", lambda *_args: self.logout())
        account.add(logout)
        self.roblox_page.add(account)

        self.stack.add_titled_with_icon(self.roblox_page, "roblox", "Roblox", "application-x-executable-symbolic")

        # 3. Fast flags page
        self.flags_page = FlagsPage(window)
        self.stack.add_titled_with_icon(self.flags_page, "flags", _("Fast flags"), "preferences-other-symbolic")

        top_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        top_box.set_margin_top(10)
        top_box.set_margin_bottom(10)
        switcher = Adw.ViewSwitcher(stack=self.stack, policy=Adw.ViewSwitcherPolicy.WIDE)
        switcher.set_halign(Gtk.Align.CENTER)
        top_box.append(switcher)
        toolbar_view.add_top_bar(top_box)
        toolbar_view.set_content(self.stack)

        self.set_child(toolbar_view)

    def set_tab(self, tab):
        self.stack.set_visible_child_name(tab)

    def flush(self):
        self.flags_page.flush()

    def open_logs(self):
        try:
            core.LOGS.mkdir(parents=True, exist_ok=True)  # none before the first game
            Gio.AppInfo.launch_default_for_uri(core.LOGS.as_uri(), None)
        except (OSError, GLib.Error) as error:
            _toast(self.window.toasts, _("Could not open the logs folder: {error}", error=error))

    def _in_thread(self, work, done):
        def run():
            try:
                result = work()
                GLib.idle_add(done, result, None)
            except Exception as error:  # shown to the user
                GLib.idle_add(done, None, error)
        threading.Thread(target=run, daemon=True).start()

    def _set_update_action(self, label, action):
        self.update_button.set_label(label)
        self.update_button.disconnect(self._update_handler)
        self._update_handler = self.update_button.connect("clicked", lambda *_args: action())

    def check_updates(self, install=False):
        """Looks for a newer client; with install=True also installs it
        (the first install from the Play page)."""
        self.update_button.set_sensitive(False)
        self.update_button.set_label(_("Checking…"))

        def done(result, error):
            self.update_button.set_sensitive(True)
            if error:
                self.update_button.set_label(_("Check for updates"))
                _toast(self.window.toasts, _("Could not check: {error}", error=error))
                return
            version, upload = result
            if version == core.installed_version():
                self.update_button.set_label(_("Check for updates"))
                _toast(self.window.toasts, _("The latest version is installed"))
                return
            self._set_update_action(_("Update to {version}", version=version),
                                    lambda: self.install_update(upload))
            if install:
                self.install_update(upload)

        self._in_thread(core.latest_version, done)

    def install_update(self, upload):
        if not self.window.begin("updating"):
            return
        self.update_button.set_sensitive(False)
        self.progress.set_visible(True)
        shown = [-1.0, ""]

        def progress(fraction, text):
            # One update per half percent, not two per 64 KiB chunk.
            if fraction - shown[0] < 0.005 and text[:12] == shown[1][:12] and fraction < 1:
                return
            shown[:] = [fraction, text]
            GLib.idle_add(self.progress.set_fraction, fraction)
            GLib.idle_add(self.progress.set_text, text)

        def done(backup, error):
            self.window.end()
            self.update_button.set_sensitive(True)
            self._set_update_action(_("Check for updates"), self.check_updates)
            self.progress.set_visible(False)
            self.version_row.set_subtitle(core.installed_version() or _("not found"))
            self.window.play_page.refresh()
            if error:
                _error_dialog(self.window, _("Update failed"), str(error) or repr(error))
            else:
                _toast(self.window.toasts, _("Roblox updated, the old version is in backups/") if backup
                       else _("Roblox installed"))

        self._in_thread(lambda: core.update_roblox(upload, progress), done)

    def logout(self):
        dialog = Adw.AlertDialog(
            heading=_("Sign out?"),
            body=_("The saved Roblox session will be deleted, you will need to sign in again next time."))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("logout", _("Sign out of Roblox"))
        dialog.set_response_appearance("logout", Adw.ResponseAppearance.DESTRUCTIVE)

        def response(_dialog, result):
            # A running game would write its session back on the next cookie change.
            if result != "logout" or not self.window.begin("signing out"):
                return

            def done(gone, error):
                self.window.end()
                if gone:
                    _toast(self.window.toasts, _("Session deleted"))
                else:
                    _error_dialog(self.window, _("Could not sign out"),
                                  str(error) if error else
                                  _("The saved session is still there. Press Restart Darling in "
                                    "Diagnostics and try again."))

            self._in_thread(core.logout, done)

        dialog.connect("response", response)
        dialog.present(self.window)

    def rebuild(self):
        if not self.window.begin("building"):
            return
        _toast(self.window.toasts, _("Building the shim…"))

        def done(result, error):
            self.window.end()
            ok, output = result if result else (False, str(error))
            if ok:
                _toast(self.window.toasts, _("Shim built"))
            else:
                _error_dialog(self.window, _("Could not build the shim"), output)

        self._in_thread(core.build_shim, done)

    def restart_darling(self):
        if not self.window.begin("restarting"):
            return

        def done(_result, error):
            self.window.end()
            if error:
                _toast(self.window.toasts, _("Could not restart Darling: {error}", error=error))
            else:
                _toast(self.window.toasts, _("Darling stopped, it starts with the next game"))

        self._in_thread(core.restart_darling, done)


ABOUT = ("Mac O’ Blox runs the real Roblox client for macOS on Linux through Darling. "
         "It is not made by Roblox and is not affiliated with it.")


def _links():
    """(title, icon, uri) of the project's community pages."""
    links = [("Discord", "macoblox-discord-symbolic", author.DISCORD_URL)]
    if author.GITHUB_URL:
        links.append(("GitHub", "macoblox-github-symbolic", author.GITHUB_URL))
    return links


def _open_uri(window, uri):
    Gtk.UriLauncher.new(uri).launch(window, None, None, None)


class InfoPage(Adw.PreferencesPage):
    def __init__(self, window):
        super().__init__(title=_("Info"), icon_name="help-about-symbolic")
        self.window = window

        about = Adw.PreferencesGroup(title="Mac O’ Blox", description=_(ABOUT))
        self.add(about)

        community = Adw.PreferencesGroup(title=_("Community"))
        for title, icon, uri in _links():
            row = Adw.ActionRow(title=title, activatable=True)
            row.add_prefix(Gtk.Image(icon_name=icon))
            row.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
            row.connect("activated", lambda *_args, u=uri: _open_uri(window, u))
            community.add(row)
        self.add(community)

        made_by = Adw.PreferencesGroup(title=_("Authors"))
        self.avatar = Adw.Avatar(size=48, text=author.NAME, show_initials=True)
        profile = Adw.ActionRow(title=author.NAME, activatable=True,
                                subtitle=_("{user} on Roblox", user="@" + author.ROBLOX_USER))
        profile.add_prefix(self.avatar)
        profile.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        profile.connect("activated", lambda *_args: _open_uri(window, author.PROFILE_URL))
        made_by.add(profile)
        maintainer_avatar = Adw.Avatar(size=48, text=author.MAINTAINER, show_initials=True)
        try:
            maintainer_avatar.set_custom_image(
                Gdk.Texture.new_from_filename(str(author.MAINTAINER_AVATAR)))
        except GLib.Error:
            pass
        maintainer = Adw.ActionRow(title=author.MAINTAINER, activatable=True,
                                   subtitle=_("Maintains this version: stability and performance fixes"))
        maintainer.add_prefix(maintainer_avatar)
        maintainer.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        maintainer.connect("activated", lambda *_args: _open_uri(window, author.MAINTAINER_URL))
        made_by.add(maintainer)

        self.ui_contributor_avatar = Adw.Avatar(size=48, text=author.UI_CONTRIBUTOR, show_initials=True)
        ui_contributor = Adw.ActionRow(title=author.UI_CONTRIBUTOR, activatable=True,
                                       subtitle="Modern UI (vibecoded too)")
        ui_contributor.add_prefix(self.ui_contributor_avatar)
        ui_contributor.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        ui_contributor.connect("activated", lambda *_args: _open_uri(window, author.UI_CONTRIBUTOR_URL))
        made_by.add(ui_contributor)

        claude = Adw.ActionRow(title=_("Made with Claude Opus 5.5"), activatable=True,
                               subtitle=_("Anthropic's AI wrote the code together with the authors"))
        claude.add_suffix(Gtk.Image(icon_name="adw-external-link-symbolic"))
        claude.connect("activated", lambda *_args: _open_uri(window, "https://www.anthropic.com/claude"))
        made_by.add(claude)
        self.add(made_by)

        settings = dict(window.settings)
        threading.Thread(target=lambda: GLib.idle_add(self._show_avatar, author.avatar(settings)),
                         daemon=True).start()
        threading.Thread(target=lambda: GLib.idle_add(self._show_tinytosha_avatar, author.tinytosha_avatar()),
                         daemon=True).start()

    def _show_avatar(self, path):
        if path:
            try:
                self.avatar.set_custom_image(Gdk.Texture.new_from_filename(str(path)))
            except GLib.Error:
                pass
        return False

    def _show_tinytosha_avatar(self, path):
        if path:
            try:
                self.ui_contributor_avatar.set_custom_image(Gdk.Texture.new_from_filename(str(path)))
            except GLib.Error:
                pass
        return False


class LauncherWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Mac O’ Blox")
        self.set_default_size(760, 580)
        self.set_resizable(True)
        self.settings = core.load_settings()
        i18n.set_language(self.settings.get("language", "en"))
        self.session = None
        # One long operation at a time: starting, updating, building,
        # restarting Darling or signing out. They share the client and Darling.
        self.busy = None
        self.quit_when_idle = False  # the window was closed during an operation
        self.last_log = None
        # MACOBLOX_PAGE opens another tab first (for screenshots).
        self.build(os.environ.get("MACOBLOX_PAGE", "play"))

    def build(self, page):
        """(Re)create the interface, e.g. after the language changes."""
        if getattr(self, "settings_page", None):
            self.settings_page.flush()  # the new page reads the file
        self.toasts = Adw.ToastOverlay()
        self.stack = Adw.ViewStack()
        self.play_page = PlayPage(self)
        self.stack.add_titled_with_icon(self.play_page, "play", _("Play"), "media-playback-start-symbolic")
        self.settings_page = SettingsPage(self)
        self.stack.add_titled_with_icon(self.settings_page, "settings", _("Settings"), "emblem-system-symbolic")
        self.info_page = InfoPage(self)
        self.stack.add_titled_with_icon(self.info_page, "info", _("Info"), "help-about-symbolic")
        self.flags_page = self.settings_page.flags_page

        if page in ("flags", "env", "roblox"):
            self.stack.set_visible_child_name("settings")
            self.settings_page.set_tab(page)
        else:
            self.stack.set_visible_child_name(page)

        # Official Libadwaita Split View layout
        self.split = Adw.OverlaySplitView()
        self.split.set_min_sidebar_width(200)
        self.split.set_max_sidebar_width(260)
        self.split.set_sidebar_width_fraction(0.28)
        self.split.set_show_sidebar(self.settings.get("show_sidebar", True))

        # Sidebar with native ViewSwitcherSidebar
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar(show_end_title_buttons=False, show_start_title_buttons=False)
        sidebar_header.set_title_widget(Gtk.Label(label="Mac O’ Blox", css_classes=["heading"]))
        sidebar_toolbar.add_top_bar(sidebar_header)

        switcher_sidebar = Adw.ViewSwitcherSidebar()
        switcher_sidebar.set_stack(self.stack)
        sidebar_toolbar.set_content(switcher_sidebar)
        self.split.set_sidebar(sidebar_toolbar)

        # Content area
        content_view = Adw.ToolbarView()
        header = Adw.HeaderBar()

        sidebar_toggle = Gtk.Button(icon_name="sidebar-show-symbolic")
        sidebar_toggle.add_css_class("flat")
        sidebar_toggle.set_tooltip_text(_("Toggle sidebar"))
        sidebar_toggle.connect("clicked", lambda *_args: self.toggle_sidebar())
        header.pack_start(sidebar_toggle)

        content_view.add_top_bar(header)
        self.toasts.set_child(self.stack)
        content_view.set_content(self.toasts)
        content_view.set_hexpand(True)
        content_view.set_vexpand(True)
        self.split.set_content(content_view)

        self.set_content(self.split)

    def toggle_sidebar(self):
        show = not self.split.get_show_sidebar()
        self.split.set_show_sidebar(show)
        self.set_setting("show_sidebar", show)

    def begin(self, what):
        """Claim the launcher for one long operation; False, with a message,
        while the game runs or another operation is under way."""
        if self.session or self.busy:
            _toast(self.toasts, _("Close Roblox first") if self.session else
                   _("Please wait, the launcher is busy"))
            return False
        self.busy = what
        self.play_page.refresh()
        return True

    def end(self):
        self.busy = None
        if self.quit_when_idle:
            self.get_application().quit()
            return
        self.play_page.refresh()

    def set_setting(self, key, value):
        self.settings[key] = value
        core.save_settings(self.settings)

    def set_language(self, code):
        if code == i18n.language():
            return
        self.set_setting("language", code)
        i18n.set_language(code)
        # Rebuild after the combo row finished handling its own signal.
        GLib.idle_add(lambda: self.build("settings") and False)

    def _captcha_dialog(self):
        dialog = Adw.AlertDialog(
            heading=_("Roblox closed at the captcha"),
            body=_("Signing up and signing in with a password show a captcha in a built-in browser, "
                   "which does not work here yet. Create the account on roblox.com, then sign in "
                   "with Quick Login: Roblox shows a code, enter it on a phone or in a browser "
                   "where you are already signed in."))
        dialog.add_response("ok", _("OK"))
        dialog.present(self)

    def play_clicked(self):
        if core.installed_version():
            self.launch()
        else:
            self.stack.set_visible_child_name("settings")
            self.settings_page.set_tab("roblox")
            self.settings_page.check_updates(install=True)

    def studio_clicked(self):
        if studio.running():
            _toast(self.toasts, _("Roblox Studio is already running"))
            return
        if not studio.needs_install():
            self._update_and_start_studio()
            return
        dialog = Adw.AlertDialog(
            heading=_("Install Roblox Studio?"),
            body=_("Studio runs in its Windows version through Wine. Mac O’ Blox downloads Wine, "
                   "DXVK and Studio, about 800 MB."))
        dialog.add_response("cancel", _("Cancel"))
        dialog.add_response("install", _("Install"))
        dialog.set_response_appearance("install", Adw.ResponseAppearance.SUGGESTED)
        dialog.connect("response", lambda _d, result: result == "install" and self._update_and_start_studio())
        dialog.present(self)

    def _update_and_start_studio(self):
        """Installs or updates Studio when needed, then starts it."""
        page = self.play_page
        page.studio.set_sensitive(False)
        page.studio.set_label(_("Checking…"))

        def progress(fraction, text):
            GLib.idle_add(page.studio_progress.set_visible, True)
            GLib.idle_add(page.studio_progress.set_fraction, fraction)
            GLib.idle_add(page.studio_progress.set_text, text)

        def work():
            try:
                studio.install(progress)
            except Exception as error:
                if studio.needs_install():
                    raise
                # Offline or Roblox unreachable: start the installed version.
                print("Studio update skipped:", error)
            studio.launch()

        def done(_result, error):
            page.studio.set_sensitive(True)
            page.studio.set_label(_("Roblox Studio"))
            page.studio_progress.set_visible(False)
            if error:
                _error_dialog(self, _("Could not start Roblox Studio"), str(error) or repr(error))
            else:
                _toast(self.toasts, _("Starting Roblox Studio…"))

        def run():
            try:
                work()
                GLib.idle_add(done, None, None)
            except Exception as error:
                GLib.idle_add(done, None, error)

        threading.Thread(target=run, daemon=True).start()

    def launch(self):
        if not self.begin("starting"):
            return
        self.settings_page.flush()
        session = core.RobloxSession(dict(self.settings))

        def start():
            try:
                session.start()  # cleans up after itself when it fails
                GLib.idle_add(self._started, session, None)
            except Exception as error:
                GLib.idle_add(self._started, None, error)

        threading.Thread(target=start, daemon=True).start()

    def _started(self, session, error):
        self.busy = None
        self.quit_when_idle = False  # a game or an error to show: stay
        if error:
            self.set_visible(True)
            self.play_page.refresh()
            _error_dialog(self, _("Could not start Roblox"), str(error) or repr(error))
            return
        self.session = session
        self.last_log = session.log_path
        self.play_page.refresh()
        # Hide once the game window has had time to appear.
        GLib.timeout_add_seconds(3, self._hide_while_playing)
        GLib.timeout_add(1000, self._watch)

    def _hide_while_playing(self):
        if self.session:
            self.set_visible(False)
        return False

    def _watch(self):
        if not self.session:
            return False
        try:
            status = self.session.poll()
        except Exception as error:  # an exception here would stop this timer for good
            print("Watching the game failed:", error)
            self.session.finish()
            status = -1
        if status is None:
            return True
        self.session = None
        self.play_page.refresh()
        failed = status not in (0, -1)
        # A failure is always shown, even with the launcher set to stay closed.
        if failed or self.settings.get("show_launcher_after_exit", True):
            self.set_visible(True)
            self.present()
        else:
            self.get_application().quit()
        if failed:
            if core.exit_reason(self.last_log) == "captcha":
                self._captcha_dialog()
            else:
                _toast(self.toasts, _("Roblox exited with code {status}", status=status))
        return False

    def stop(self):
        threading.Thread(target=core.stop_roblox, daemon=True).start()

    def open_last_log(self):
        if self.last_log:
            try:
                Gio.AppInfo.launch_default_for_uri(self.last_log.as_uri(), None)
            except GLib.Error as error:
                _toast(self.toasts, str(error))


class LauncherApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.window = None

    def do_activate(self):
        if not self.window:
            Gtk.Window.set_default_icon_name("macoblox")
            Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).add_search_path(
                str(core.PROJECT / "launcher" / "icons"))
            self.window = LauncherWindow(self)
            # Keep running while the window is hidden during a game.
            self.hold()
            self.window.connect("close-request", self._close)
        self.window.set_visible(True)
        self.window.present()
        if os.environ.get("MACOBLOX_PAGE"):
            # Screenshots: no focused field.
            GLib.timeout_add(300, lambda: self.window.set_focus(None) and False)

    def _close(self, window):
        window.settings_page.flush()
        if window.session or window.busy:
            # Closing during a game only hides the launcher. Closing during an
            # update, build or start hides it until that is done: quitting
            # would stop the work half way (a half unpacked client).
            window.set_visible(False)
            window.quit_when_idle = window.busy is not None
            return True
        self.release()
        self.quit()
        return False


def main():
    return LauncherApp().run(None)

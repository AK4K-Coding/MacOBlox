# MacOBlox

Roblox Client for macOS (x86_64) on Linux via Darling. As of
2026-09-23: The main menu, login (Quick Login), avatar, and games are working.

## Launch

Launcher: `launcher/install.sh` adds the “Mac O Blox” entry to the Applications menu
and the `macoblox` command. That includes game launching, fast flags, and DNS specifically for Roblox,
Camera sensitivity, client update, diagnostics. The settings are located in
`~/.config/macoblox/settings.json`, logs in `logs/`.

Priorities: Darling runs with a nice value of −4, while darlingserver, the Darling daemons, and
pw-cat inherits the launcher's nice value (+10 if the desktop launches it that way) and
They remain idle while the game uses all the cores. The launcher starts darlingserver with
daemons to -5 and pw-cat to -11, as far as RLIMIT_NICE allows.

## What does the shim (build/libMacOBloxShims.dylib) do?

`build_debug_shim.sh` is built from:

- `libMacOBloxShims.m` — AppKit/GL/input: returns the GL context after
  CALayerContext, macOS-style mouse button numbers, mouse capture for the camera,
  cursors, missing methods for NSEvent/NSTextView/NSButton/CNContactStore,
  a cookie saved to disk (`~/Library/MacOBlox/Cookies.plist` inside
  the Darling prefix), hiding the menu bar, window icon.
- `missing_symbols.c` — functions that Roblox imports but Darling does not.
- `net_trace.c` — reliable UDP reception and a watchdog for frozen RakNet threads.
- `darling_fixes.c` — mutexes without Darling wake-up losses; `usleep` and
  `nanosleep` run directly on Linux (in Darling, each one involves two requests to `darlingserver`).
- `memory_stats.c` — system and game memory (`phys_footprint` for “Mem”).
- `thread_kick.c` — “kick” (SIGURG) for threads stuck waiting for Darling:
  UDP watchdog and long mutex waits; the location of the deadlock is logged.
- `xfixes_raw.c` — hiding the cursor via XFixes over its own X11 socket.
- `dns_override.c` — DNS for Roblox via the launcher’s local proxy.
- `xattr_compat.c`, `exit_compat.c` — from previous stages.

The `MACOBLOX_*` variables (tracing, DNS, sensitivity) are set by
the launcher. `run_debug.sh` is still there for manual debugging.

## Important Note About Darling

Do not delete or modify files in `~/.darling` from the host while
darlingserver is running: the Darling overlay will stop showing new files to the host.
Delete files from within the shell (`darling shell rm ...`) or while the server is stopped.

## History

## Diagnostic Run

From a regular Linux terminal:

```bash
cd MacOBlox
./run_debug.sh
```

The script compiles the library from `libMacOBloxShims.m` in `build/`, launches
the client from the project folder within an existing Darling prefix, and writes
the output to a separate file in `logs/launch-*.log`. Arguments are passed to the client.
The launch itself requires a running Darling outside the restricted Codex environment.
The launch script has not yet been tested in a running Darling instance.

Build only: `./build_debug_shim.sh`. You can set `DARLING_SYSROOT`.
The old libraries in the root directory and inside `.app` are preserved; the new one is selected
via `DYLD_INSERT_LIBRARIES` and `DYLD_LIBRARY_PATH`.

## Changes 2026-09-21

- Fixed the signature of the `NSWindow initWithContentRect:…` interceptor:
  The rectangle is passed by value; the flag uses the x86_64 BOOL ABI.
  Signature: https://developer.apple.com/documentation/appkit/nswindow/init(contentrect:stylemask:backing:defer:)
- Removed the call to the assumed `what()` method for arbitrary C++ exceptions.
  A thrown object does not necessarily have a virtual table.
- Added separate scripts for building and diagnostic runs.
- The source code and old library are preserved in `backups/before-codex-20260921/`.
- Cross-compilation succeeded; shell script syntax was verified.
- The Codex environment launch check fails in Darling before Roblox starts:
  `binary is not setuid root, which is mandatory`. In this environment, the owner
  of the system binary is listed as nobody. This does not prove that the
  installation on the host is broken and is not a reason to change system permissions.

## Changes 2026-09-26

Tested with a suite of tests under Darling (network, mutexes, waits, sound,
cookies); the old build fails the new tests, while the new one passes them all.

- Timeout waits in Darling return 0 instead of ETIMEDOUT (100 ms
  wait — 0 after 100 ms). Therefore, the wait segments in `darling_fixes.c`
  never grew (each 50-ms segment — a request to darlingserver), and
  the caller never saw a timeout. Now, the elapsed time is determined by the clock;
  for `pthread_cond_timedwait_relative_np` (which Roblox imports), the time
  of segments already waited out is subtracted; otherwise, waits longer than a second
  would never end.
- kqueue: Roblox closes sockets using `close$NOCANCEL` without EV_DELETE, and
  the socket entry remained: the next socket with the same number received
  events from the old owner (the thread loops, a use-after-free is possible in
  Asio). `close`/`close$NOCANCEL` have been intercepted; entries are checked against the inode.
- The “is there data” check is now done via `poll`, not `recv(MSG_PEEK)`:
  any receive operation, even a peek, retrieves the socket error (ICMP “port unreachable”),
  and after that, `recv(MSG_DONTWAIT)` on a blocking socket would hang indefinitely.
- UDP watcher pins—only for network sockets (AF_INET/AF_INET6), not for
  local pairs used by threads to wake each other up; the thread waiting on the mutex
  is checked again before the pin.
- Cookies: `cookiesForURL:` Darling ignores the URL, and `setCookies:forURL:…`
  does nothing. Storage is now managed in-house: domain, path, Secure, and expiration time
  are checked (login credentials no longer go to third-party hosts or over HTTP), the new
  value replaces the old one, file writing is atomic, immediately set to 0600; session
  cookies are stored only in memory; third-party domains in Set-Cookie are rejected.
- Event queue: “no event” — type 100, as in Darling (NSApplication
  compares it to 0x64). Type 13 was a real event at point (0,0).
- Keys: on FocusOut, the table of pressed keys is reset (Alt+Tab with
  W held down no longer leaves it “pressed” for CGEventSourceKeyState).
- Mouse capture: while our warp is active, movement events are not merged; if
  the movement from the warp never arrives, centering resumes after 8
  events (previously it was disabled until the end of the capture).
- The XFixes stream sleeps on the pipe instead of polling every 5 ms via usleep
  Darling (400 requests to darlingserver per second); it starts at launch.
- getaddrinfo: pause between attempts without blocking; retry only in case of
  temporary errors; wait using Linux direct sleep.
- Exception hooks, makeCurrentContext, flushBuffer: getenv and dlsym are called once,
  rather than on every throw or frame (Lua errors in games are C++ exceptions).
- Shaders: the Mesa fix applies to all shaders (not just the
  first 8192); source code is stored only with `MACOBLOX_TRACE_GL=1`.
- `fast_libc.c`: SSE loops instead of `rep movsb/stosb` where those are slower
  (short copies, 4K aliasing, more L2), fast memchr/strlen/strcmp,
  memset_pattern4/8/16 have been reimplemented.
- `MACOBLOX_*=0` flags now mean “disabled.”

## Changes September 26, 2026, evening: locks without darlingserver

- In Darling, mutexes and conditional variables (psynch) are waited on via
  darlingserver: every lock acquisition under load, every wait, and every signal—
  a request to the server (40% of the game’s CPU usage)—wakes are lost, and conditional
  variables break (the timeout arrives as a wake, counters
  diverging, followed by “psync_cvwait; invalid sequence numbers” and EINVAL on
  every wait—12,874 times in 7 minutes in the server log).
- Now, in `darling_fixes.c`, a busy mutex waits on a Linux futex (the table
  at the mutex’s address, woken by `pthread_mutex_unlock`), while the condition variables
  are separate: a queue of waiters, each with its own futex; a signal wakes exactly one,
  a broadcast wakes exactly the number of waiters, and process signals do not interrupt the wait.
  Conditional variables created by Darling itself (tag ‘COND’/0x434F4E45,
  process-shared) remain its own. “Queue” test: 13.6 s and 18.5 s CPU
  darlingserver → 0.13 s and 0.04 s.
- `PTHREAD_MUTEX_USE_ULOCK=1` (libpthread mode using ulock) is not suitable:
  its condition variables call `__ulock_wait2` (syscall 544), which is not
  present in Darling—the process crashes on the first wait.
- Launcher: “Restart Darling” stops the entire container (launchd and
  daemons—which are not children of darlingserver and remained orphaned with ~250 MB), and upon
  startup, it terminates Darling processes without a running server and waits until
  the previous game closes (otherwise, both would share the same server and crash together).

## What to Check Next

We need a recent startup log from a regular terminal. Use it to determine where
the client is crashing: the loader, NIB loading, window creation, or rendering.
According to the owner’s recollection, the engine used to start up, but there was no image;
an old log confirming this has not yet been found.

There are still potential issues in the old code: some fatal signals
are suppressed, and the error handler manually parses the context and stack trace. These areas
require separate verification. Cocoa string constants have been updated to NSString.
`build_shims.py` is an old script that directly modifies the frameworks
in `~/.darling`; the new scripts do not run it automatically.
In `ffmpeg_compat/`, there are links between different ABI versions; compatibility
has not been verified, and the new build does not add this folder to the library path.

Accessing host files via `/Volumes/SystemRoot` is described in the documentation:
https://docs.darlinghq.org/internals/basics/containerization.html

## Blocker on the host after lifting Codex restrictions

2026-09-21: The kernel was updated at 16:12 to 7.2.6-1-cachyos, but 7.2.0-1-cachyos is running. The module directory for the running kernel is missing; OverlayFS
is not registered in /proc/filesystems, and `modinfo overlay` fails.
This explains the `Cannot mount overlay: No such device` error before Roblox starts.
The update log confirms that the new kernel’s initramfs was successfully generated.
The next step is a normal reboot into the installed kernel, followed by running
`run_debug.sh`. An automatic reboot did not occur.
The script now detects this situation before Darling starts.

## Post-reboot check, 2026-09-21 16:21–16:29

## Blocker on the host after lifting Codex restrictions

2026-09-21: The kernel was updated at 16:12 to 7.2.6-1-cachyos, but 7.2.0-1-cachyos is running. The module directory for the running kernel is missing; OverlayFS
is not registered in /proc/filesystems, and `modinfo overlay` fails.
This explains the `Cannot mount overlay: No such device` error before Roblox starts.
The update log confirms that the new kernel’s initramfs was successfully generated.
The next step is a normal reboot into the installed kernel, followed by running
`run_debug.sh`. An automatic reboot did not occur.
The script now detects this situation before Darling starts.

## Post-reboot check, September 21, 2026, 4:21–4:29 PM

Confirmed by log: MainMenu.nib loaded, RBXWindow created,
RobloxPlayerAppDelegate assigned, NSApplication run called.
Window/image display and game engine functionality NOT confirmed.

Next blocker: `Failed to initialize crash reporter`, std::runtime_error
from RobloxPlayer at return address 0x105606b21, called from 0x10002f4aa.
This was initially preceded by getxattr/setxattr errors. In xattr_compat.c
an adapter has been added only for org.chromium.crashpad.* and com.googlecode.crashpad.*:
Linux namespace user., access via fd, ENODATA is converted to ENOATTR.
Other names and non-zero position/options remain with Darling.
Data is actually written to the attributes; success is not faked.
After applying the adapter, xattr messages have disappeared, but the reporter initialization still
fails with an unspecified error. The cause of the subsequent crash has not been determined.
RobloxCrashHandler, using the same library, reaches the argument parsing stage
(`--crashCounter must be specified` when running --help); it does not load without the shim.

Logs: logs/touch-types.log (xattr errors), logs/xattr-compat.log (after the fix),
logs/crash-handler-with-shim.log. The launch time and exit code are also recorded
in separate logs/launch-*.log files.

The xattr test for a separate dylib and tests/xattr_compat_probe.c in Darling passed:
missing attribute, write/read, size query, small buffer,
missing path, passing an arbitrary name to the source function.
The original Roblox binary has not been modified. The libraries in the root directory and the .app file have been preserved;
the active build is located in build/.

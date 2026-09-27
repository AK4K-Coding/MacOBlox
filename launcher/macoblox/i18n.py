"""Interface strings. English is the source language; set_language("ru")
switches to Russian."""

LANGUAGES = {"en": "English", "ru": "Русский"}

_language = "en"

RU = {
    # Pages
    "Play": "Играть",
    "Fast flags": "Фастфлаги",
    "Settings": "Настройки",
    "Environment": "Окружение",
    "Info": "Инфо",
    "Collapse sidebar": "Свернуть панель",
    "Expand sidebar": "Развернуть панель",
    "Toggle sidebar": "Свернуть/развернуть панель",
    # Launcher update
    "Update available": "Доступно обновление",
    "A new version of Mac O’ Blox ({version}) is available. Update now?":
        "Доступна новая версия Mac O’ Blox ({version}). Обновить сейчас?",
    "Later": "Позже",
    "Update": "Обновить",
    "Launcher version": "Версия лаунчера",
    "Force update": "Принудительное обновление",
    "Mac O’ Blox is up to date": "Установлена последняя версия Mac O’ Blox",
    "Update {version} available": "Доступно обновление {version}",
    "Pulling latest version…": "Загрузка последней версии…",
    "Building shim…": "Сборка шима…",
    "Updating launcher shortcuts…": "Обновление ярлыков лаунчера…",
    "Mac O’ Blox updated successfully": "Mac O’ Blox успешно обновлён",
    "Mac O’ Blox updated. Restart it to use the new version.":
        "Mac O’ Blox обновлён. Перезапусти его, чтобы открыть новую версию.",
    "Could not update the files in {path}:\n{output}": "Не удалось обновить файлы в {path}:\n{output}",
    # Play page
    "Roblox {version}": "Roblox {version}",
    "Roblox not found": "Roblox не найден",
    "Darling running": "Darling запущен",
    "Darling starts with the game": "Darling запустится при старте",
    "Roblox is running": "Roblox запущен",
    "Starting…": "Запускаю…",
    "Stop Roblox": "Остановить Roblox",
    "Could not start Roblox": "Не удалось запустить Roblox",
    "Update failed": "Обновление не удалось",
    "Copy": "Скопировать",
    "Install these first: {programs}": "Сначала установи: {programs}",
    "Close": "Закрыть",
    "Install Roblox": "Установить Roblox",
    "Sign in with Quick Login": "Входи через Quick Login",
    "Roblox closed at the captcha": "Roblox закрылся на капче",
    "Signing up and signing in with a password show a captcha in a built-in browser. "
    "The launcher shows it in a window of its own when WebKitGTK 6.0 is installed "
    "(webkitgtk-6.0, gir1.2-webkit-6.0 or webkitgtk6.0). Without it, create the "
    "account on roblox.com, then sign in with Quick Login: Roblox shows a code, "
    "enter it on a phone or in a browser where you are already signed in.":
        "Регистрация и вход по паролю показывают капчу во встроенном браузере. Лаунчер "
        "открывает её в своём окне, если установлен WebKitGTK 6.0 (webkitgtk-6.0, "
        "gir1.2-webkit-6.0 или webkitgtk6.0). Без него создай аккаунт на roblox.com, потом "
        "войди через Quick Login: Roblox покажет код, введи его на телефоне или в браузере, "
        "где ты уже вошёл.",
    "Back": "Назад",
    "Forward": "Вперёд",
    "Reload": "Обновить",
    "Back to Roblox": "Вернуться в Roblox",
    "Close": "Закрыть",
    "OK": "Понятно",
    "Roblox Studio": "Roblox Studio",
    "Roblox Studio is already running": "Roblox Studio уже запущен",
    "Install Roblox Studio?": "Установить Roblox Studio?",
    "Studio runs in its Windows version through Wine. Mac O’ Blox downloads Wine, "
    "DXVK and Studio, about 800 MB.":
        "Studio запускается в Windows-версии через Wine. Mac O’ Blox скачает Wine, "
        "DXVK и Studio, это около 800 МБ.",
    "Install": "Установить",
    "Could not start Roblox Studio": "Не удалось запустить Roblox Studio",
    "Starting Roblox Studio…": "Запускаю Roblox Studio…",
    "{label}: {done} of {total} MB": "{label}: {done} из {total} МБ",
    "Unpacking Wine": "Распаковываю Wine",
    "Preparing Wine": "Готовлю Wine",
    "Roblox Studio: {done} of {total} MB": "Roblox Studio: {done} из {total} МБ",
    "Unknown Studio package manifest format": "Неизвестный формат манифеста пакетов Studio",
    "{name} failed its checksum": "{name} не прошёл проверку контрольной суммы",
    "Open last log": "Открыть последний лог",
    "Roblox exited with code {status}": "Roblox завершился с кодом {status}",
    # Fast flags
    "FPS limit": "Лимит FPS",
    "Graphics quality": "Качество графики",
    "No shadows": "Без теней",
    "No grass": "Без травы",
    "Low quality terrain": "Упрощённый рельеф",
    "Texture quality override": "Качество текстур",
    "Popular": "Популярные",
    "Roblox only applies flags from its allowlist, some flags may have no effect.":
        "Roblox применяет только флаги из своего списка разрешённых, часть флагов может не действовать.",
    "Custom flags": "Свои флаги",
    "Add flag": "Добавить флаг",
    "Import JSON": "Импорт JSON",
    "File": "Файл",
    "New flag": "Новый флаг",
    "Name": "Название",
    "Value": "Значение",
    "Remove": "Удалить",
    "Import fast flags": "Импорт фастфлагов",
    'Paste JSON like {"Flag": value}. Flags are added to the current ones.':
        'Вставь JSON вида {"Флаг": значение}. Флаги добавятся к текущим.',
    "Cancel": "Отмена",
    "Import": "Импортировать",
    "This is not a JSON object with flags": "Это не JSON-объект с флагами",
    "Imported flags: {count}": "Импортировано флагов: {count}",
    "Could not save flags: {error}": "Не удалось сохранить флаги: {error}",
    # Settings: game
    "Game": "Игра",
    "Camera sensitivity": "Чувствительность камеры",
    "Mouse movement multiplier while rotating the camera":
        "Множитель движения мыши при вращении камеры",
    "Show the launcher after Roblox exits": "Показывать лаунчер после выхода из Roblox",
    "Hide the macOS menu bar": "Скрывать полоску меню macOS",
    "The Roblox, Edit, Window… strip at the top of the game window":
        "Полоска Roblox, Edit, Window… сверху окна игры",
    # Settings: DNS
    "DNS for Roblox": "DNS для Roblox",
    "Only Roblox uses this server, the rest of the system keeps its own DNS. "
    "Helps when some Roblox images or servers do not load.":
        "Этот сервер использует только Roblox, остальная система остаётся на своём DNS. "
        "Помогает, если не грузятся картинки или сервера Roblox.",
    "DNS server": "DNS-сервер",
    "System (Darling default)": "Системный (как в Darling)",
    "Quad9 (9.9.9.9, encrypted)": "Quad9 (9.9.9.9, шифрованный)",
    "Cloudflare (1.1.1.1, encrypted)": "Cloudflare (1.1.1.1, шифрованный)",
    "Google (8.8.8.8, encrypted)": "Google (8.8.8.8, шифрованный)",
    "Custom": "Свой",
    "Custom server": "Свой сервер",
    "IP address, optionally with :port. Plain DNS, not encrypted.":
        "IP-адрес, можно с :портом. Обычный DNS, без шифрования.",
    "Custom DNS server must look like 9.9.9.9, 9.9.9.9:53 or [2620:fe::fe]:53":
        "Свой DNS-сервер пишется так: 9.9.9.9, 9.9.9.9:53 или [2620:fe::fe]:53",
    # Settings: language
    "Interface": "Интерфейс",
    "Language": "Язык",
    # Settings: Roblox
    "Installed version": "Установленная версия",
    "not found": "не найдена",
    "Check for updates": "Проверить обновления",
    "Checking…": "Проверяю…",
    "Updating…": "Обновляю…",
    "Could not check: {error}": "Не удалось проверить: {error}",
    "The latest version is installed": "Установлена последняя версия",
    "Update to {version}": "Обновить до {version}",
    "Close Roblox first": "Сначала закрой Roblox",
    "Please wait, the launcher is busy": "Подожди, лаунчер ещё занят",
    "Darling could not create its prefix in {path}": "Darling не смог создать префикс в {path}",
    "Roblox updated, the old version is in backups/": "Roblox обновлён, старая версия в backups/",
    "Roblox installed": "Roblox установлен",
    "Downloading {done} of {total} MB": "Загрузка {done} из {total} МБ",
    "Unpacking": "Распаковка",
    "Done": "Готово",
    "The download is not a zip archive": "Скачанный файл не является zip-архивом",
    "The archive has no RobloxPlayer.app": "В архиве нет RobloxPlayer.app",
    # Settings: account
    "Account": "Аккаунт",
    "Sign out": "Выйти из аккаунта",
    "Sign out?": "Выйти из аккаунта?",
    "The saved Roblox session will be deleted, you will need to sign in again next time.":
        "Сохранённая сессия Roblox будет удалена, при следующем запуске нужно будет войти заново.",
    "Sign out of Roblox": "Выйти",
    "Session deleted": "Сессия удалена",
    "Could not sign out": "Не удалось выйти",
    "The saved session is still there. Press Restart Darling in Diagnostics and try again.":
        "Сохранённая сессия осталась на месте. Нажми «Перезапустить Darling» в разделе «Диагностика» "
        "и попробуй ещё раз.",
    # Settings: diagnostics
    "Diagnostics": "Диагностика",
    "Detailed logs for debugging. They slow the game down, enable only when needed.":
        "Подробные логи для отладки. Замедляют игру, включай только когда нужно.",
    "Backtrace on crashes": "Бэктрейс при крашах",
    "Network tracing (UDP)": "Трассировка сети (UDP)",
    "Mouse lock tracing": "Трассировка захвата мыши",
    "Mouse event tracing": "Трассировка событий мыши",
    "OpenGL tracing": "Трассировка OpenGL",
    "Frame rate in the log": "FPS в логе",
    "Keyboard tracing": "Трассировка клавиатуры",
    "Open logs folder": "Открыть папку с логами",
    "Could not open the logs folder: {error}": "Не удалось открыть папку с логами: {error}",
    "Rebuild shim": "Пересобрать шим",
    "Building the shim…": "Собираю шим…",
    "Shim built": "Шим собран",
    "The shim comes built with this package": "Шим в этом пакете уже собран",
    "Could not build the shim": "Не удалось собрать шим",
    "Could not build the shim:\n{output}": "Не удалось собрать шим:\n{output}",
    "Restart Darling": "Перезапустить Darling",
    "Darling stopped, it starts with the next game": "Darling остановлен, запустится при следующей игре",
    "Could not restart Darling: {error}": "Не удалось перезапустить Darling: {error}",
    # Info
    "Mac O’ Blox runs the real Roblox client for macOS on Linux through Darling. "
    "It is not made by Roblox and is not affiliated with it.":
        "Mac O’ Blox запускает настоящий клиент Roblox для macOS на Linux через Darling. "
        "Его делает не Roblox, и с Roblox он никак не связан.",
    "Community": "Сообщество",
    "Authors": "Авторы",
    "{user} on Roblox": "{user} в Roblox",
    "Maintains this version: stability and performance fixes":
        "Поддерживает эту версию: стабильность и скорость",
    "Made with Claude Opus 5.5": "Сделано с Claude Opus 5.5",
    "Anthropic's AI wrote the code together with the authors": "ИИ от Anthropic писал код вместе с авторами",
}


def set_language(code):
    global _language
    _language = code if code in LANGUAGES else "en"


def language():
    return _language


def _(text, **values):
    if _language == "ru":
        text = RU.get(text, text)
    return text.format(**values) if values else text

"""Per-user documented Windows registration; never writes UserChoice."""

import ctypes
import sys
import winreg
from pathlib import Path

EXTENSIONS = (
    ".zip",
    ".7z",
    ".rar",
    ".tar",
    ".gz",
    ".tgz",
    ".bz2",
    ".tbz2",
    ".xz",
    ".txz",
    ".alz",
    ".egg",
    ".cab",
    ".iso",
    ".cbz",
)
CAPABILITIES = r"Software\Crow Science Lab\Crow Pack\Capabilities"
CLASSES = r"Software\Classes"
COMMANDS = [
    ("zip", "ZIP으로 압축"),
    ("7z", "7Z로 압축"),
    ("private", "개인정보 보호 압축"),
    ("compress", "Crow Pack으로 압축"),
]
ARCHIVE_COMMANDS = [
    ("open", "Crow Pack으로 열기"),
    ("here", "여기에 풀기"),
    ("smart", "알아서 풀기"),
    ("folder", "새 폴더에 풀기"),
    ("batch", "일괄 해제"),
    ("test", "무결성 검사"),
    ("convertzip", "ZIP으로 변환"),
    ("convert7z", "7Z로 변환"),
]


def launcher():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    pythonw = Path(sys.executable).with_name("pythonw.exe")
    return f'"{pythonw if pythonw.exists() else sys.executable}" "{Path(__file__).resolve().parents[2] / "main.py"}"'


def _set(path, name, value):
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, path) as key:
        winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)


def _delete_tree(path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0, winreg.KEY_READ | winreg.KEY_WRITE) as key:
            children = []
            index = 0
            while True:
                try:
                    children.append(winreg.EnumKey(key, index))
                    index += 1
                except OSError:
                    break
        for child in children:
            _delete_tree(path + "\\" + child)
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, path)
    except FileNotFoundError:
        pass


def register(menu=True):
    if menu:
        # Rebuild our own tree so removed commands do not survive an upgrade.
        unregister_menu()
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2])) / "assets"
    command = launcher()
    for ext in EXTENSIONS:
        kind = ext[1:].upper()
        prog = "CrowPack." + kind
        icon = base / (kind.lower() + ".ico")
        if not icon.exists():
            icon = base / "crow_pack.ico"
        _set(CLASSES + "\\" + prog, "", "Crow Pack " + kind)
        _set(CLASSES + "\\" + prog + r"\DefaultIcon", "", f'"{icon}",0')
        _set(CLASSES + "\\" + prog + r"\shell\open\command", "", command + ' "%1"')
        _set(CAPABILITIES + r"\FileAssociations", ext, prog)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CLASSES + "\\" + ext + r"\OpenWithProgids") as key:
            winreg.SetValueEx(key, prog, 0, winreg.REG_NONE, b"")
        # Only fill the legacy fallback if neither a user choice nor merged handler exists.
        current = ""
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext) as key:
                current = winreg.QueryValueEx(key, "")[0]
        except OSError:
            pass
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                rf"Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{ext}\UserChoice",
            ) as key:
                current = winreg.QueryValueEx(key, "ProgId")[0] or current
        except OSError:
            pass
        if not current:
            _set(CLASSES + "\\" + ext, "", prog)
    _set(CAPABILITIES, "ApplicationName", "Crow Pack")
    _set(CAPABILITIES, "ApplicationDescription", "Crow Science Lab file packaging tools")
    _set(CAPABILITIES, "ApplicationIcon", f'"{base / "crow_pack.ico"}",0')
    _set(r"Software\RegisteredApplications", "Crow Pack", CAPABILITIES)
    appkey = CLASSES + r"\Applications\CrowPack.exe"
    _set(appkey, "FriendlyAppName", "Crow Pack")
    _set(appkey + r"\shell\open\command", "", command + ' "%1"')
    for ext in EXTENSIONS:
        _set(appkey + r"\SupportedTypes", ext, "")
    if menu:
        roots = [(r"*", COMMANDS), ("Directory", COMMANDS)]
        roots += [(rf"SystemFileAssociations\{ext}", ARCHIVE_COMMANDS) for ext in EXTENSIONS]
        for root, commands in roots:
            menu_key = CLASSES + "\\" + root + r"\shell\CrowPack"
            _set(menu_key, "MUIVerb", "Crow Pack")
            _set(menu_key, "Icon", str(base / "crow_pack.ico"))
            _set(menu_key, "SubCommands", "")
            for index, (action, label) in enumerate(commands):
                key = menu_key + rf"\shell\{index:02d}{action}"
                _set(key, "", label)
                _set(key, "MultiSelectModel", "Document")
                _set(key + r"\command", "", command + f' --shell {action} "%1"')
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def unregister_menu():
    for root in ["*", "Directory"] + [rf"SystemFileAssociations\{ext}" for ext in EXTENSIONS]:
        _delete_tree(CLASSES + "\\" + root + r"\shell\CrowPack")


def unregister():
    unregister_menu()
    for ext in EXTENSIONS:
        prog = "CrowPack." + ext[1:].upper()
        _delete_tree(CLASSES + "\\" + prog)
        for suffix, name in [("", ""), (r"\OpenWithProgids", prog)]:
            try:
                with winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER, CLASSES + "\\" + ext + suffix, 0, winreg.KEY_ALL_ACCESS
                ) as key:
                    if suffix or winreg.QueryValueEx(key, "")[0] == prog:
                        winreg.DeleteValue(key, name)
            except OSError:
                pass
    _delete_tree(CAPABILITIES)
    _delete_tree(CLASSES + r"\Applications\CrowPack.exe")
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, r"Software\RegisteredApplications", 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, "Crow Pack")
    except OSError:
        pass
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def association_status():
    # AssocQueryStringW returns the effective friendly application name.
    query = ctypes.windll.shlwapi.AssocQueryStringW
    rows = []
    for ext in EXTENSIONS:
        buf = ctypes.create_unicode_buffer(1024)
        size = ctypes.c_ulong(len(buf))
        result = query(0, 4, ext, None, buf, ctypes.byref(size))
        rows.append({"extension": ext, "handler": buf.value if result == 0 else ""})
    return rows

"""Per-user documented Windows registration; never writes UserChoice."""

import ctypes
import os
import sys
import tempfile
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
CAPABILITIES = r"Software\Crow Science Lab\CrowPack\Capabilities"
CLASSES = r"Software\Classes"
STORE_AUMID = '170231F2.CrowPack_9fbspzvkgt7f8!CrowPack'
COMMANDS = [
    ("zip", "ZIP으로 압축"),
    ("7z", "7Z로 압축"),
    ("private", "파일명까지 암호화"),
    ("compress", "CrowPack으로 압축"),
]
ARCHIVE_COMMANDS = [
    ("open", "CrowPack으로 열기"),
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


def is_registered_installation():
    if not getattr(sys, 'frozen', False):
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, CLASSES + r'\Applications\CrowPack.exe\shell\open\command') as key:
            return winreg.QueryValueEx(key, '')[0] == launcher() + ' "%1"'
    except OSError:
        return False


def _can_set_legacy_default(extension):
    choice_key = rf'Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\{extension}\UserChoice'
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, choice_key):
            return False
    except FileNotFoundError:
        pass
    try:
        with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, extension) as key:
            return not winreg.QueryValueEx(key, '')[0] and not _association_value(extension, 20)
    except FileNotFoundError:
        return not _association_value(extension, 20)


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
            icon = base / "CrowPack.ico"
        _set(CLASSES + "\\" + prog, "", "CrowPack " + kind)
        _set(CLASSES + "\\" + prog + r"\DefaultIcon", "", f'"{icon}",0')
        _set(CLASSES + "\\" + prog + r"\shell\open\command", "", command + ' "%1"')
        _set(CAPABILITIES + r"\FileAssociations", ext, prog)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, CLASSES + "\\" + ext + r"\OpenWithProgids") as key:
            winreg.SetValueEx(key, prog, 0, winreg.REG_NONE, b"")
        # Only fill the legacy fallback if neither a user choice nor merged handler exists.
        if _can_set_legacy_default(ext):
            _set(CLASSES + "\\" + ext, "", prog)
    _set(CAPABILITIES, "ApplicationName", "CrowPack")
    _set(CAPABILITIES, "ApplicationDescription", "Crow Science Lab file packaging tools")
    _set(CAPABILITIES, "ApplicationIcon", f'"{base / "CrowPack.ico"}",0')
    _set(r"Software\RegisteredApplications", "CrowPack", CAPABILITIES)
    appkey = CLASSES + r"\Applications\CrowPack.exe"
    _set(appkey, "FriendlyAppName", "CrowPack")
    _set(appkey + r"\shell\open\command", "", command + ' "%1"')
    for ext in EXTENSIONS:
        _set(appkey + r"\SupportedTypes", ext, "")
    if menu:
        roots = [(r"*", COMMANDS), ("Directory", COMMANDS)]
        roots += [(rf"SystemFileAssociations\{ext}", ARCHIVE_COMMANDS) for ext in EXTENSIONS]
        for root, commands in roots:
            menu_key = CLASSES + "\\" + root + r"\shell\CrowPack"
            _set(menu_key, "MUIVerb", "CrowPack")
            _set(menu_key, "Icon", str(base / "CrowPack.ico"))
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
            winreg.DeleteValue(key, "CrowPack")
    except OSError:
        pass
    ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)


def _association_value(extension, field):
    query = ctypes.windll.shlwapi.AssocQueryStringW
    query.argtypes = [ctypes.c_uint32, ctypes.c_uint32, ctypes.c_wchar_p, ctypes.c_wchar_p,
                      ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_ulong)]
    query.restype = ctypes.c_long
    buffer = ctypes.create_unicode_buffer(32768)
    size = ctypes.c_ulong(len(buffer))
    return buffer.value if query(0, field, extension, None, buffer, ctypes.byref(size)) == 0 else ''


def association_status(packaged):
    rows = []
    executable = Path(sys.executable)
    for ext in EXTENSIONS:
        handler = _association_value(ext, 4)  # ASSOCSTR_FRIENDLYAPPNAME
        target = _association_value(ext, 2)  # ASSOCSTR_EXECUTABLE
        app_id = _association_value(ext, 21)  # ASSOCSTR_APPID
        prog_id = _association_value(ext, 20)  # ASSOCSTR_PROGID
        current = (bool(target) and Path(target) == executable) or (packaged and app_id.casefold() == STORE_AUMID.casefold())
        assigned = any((handler, target, app_id, prog_id))
        rows.append({"extension": ext, "handler": handler, "is_crowpack": current, "assigned": assigned})
    return rows


def create_desktop_shortcut(desktop: Path, packaged: bool):
    """Create a Shell link without replacing a shortcut already on the desktop."""
    import pythoncom
    from win32com.shell import shell

    path = desktop / ('CrowPack (Microsoft Store).lnk' if packaged else 'CrowPack.lnk')
    pythoncom.CoInitialize()
    try:
        link = pythoncom.CoCreateInstance(shell.CLSID_ShellLink, None, pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
        persistence = link.QueryInterface(pythoncom.IID_IPersistFile)
        identity = shell.SHParseDisplayName('shell:AppsFolder\\' + STORE_AUMID, 0)[0] if packaged else None
        if path.exists():
            persistence.Load(str(path))
            matches = (link.GetIDList() == identity if packaged else Path(link.GetPath(0)[0]) == Path(sys.executable))
            if matches:
                return 'exists'
            raise FileExistsError(str(path))
        if packaged:
            link.SetIDList(identity)
        else:
            link.SetPath(sys.executable)
            link.SetIconLocation(sys.executable, 0)
            link.SetWorkingDirectory(str(Path(sys.executable).parent))
        link.SetDescription('CrowPack — Crow Science Lab')
        with tempfile.NamedTemporaryFile(dir=desktop, suffix='.lnk', delete=False) as staged:
            staged_path = Path(staged.name)
        try:
            persistence.Save(str(staged_path), False)
            os.rename(staged_path, path)
        finally:
            staged_path.unlink(missing_ok=True)
        return 'created'
    finally:
        pythoncom.CoUninitialize()

"""Explorer receives selected directory roots, never a flattened list of leaves."""
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from PySide6.QtCore import Qt

from src.bridge.core_bridge import CoreBridge
from src.engine.archive_manager import ArchiveManager
from src.engine.packaging_tools import DragExportManager


class DragTreeTests(unittest.TestCase):
    def test_native_drag_transfers_directory_urls_as_copy_only(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            (root / 'folder').mkdir()
            bridge = CoreBridge()
            messages = []
            bridge.dragStatus.connect(messages.append)
            with patch('src.bridge.tools_bridge.QApplication.mouseButtons', return_value=Qt.LeftButton), \
                    patch('src.bridge.tools_bridge.QDrag') as drag:
                drag.return_value.exec.return_value = Qt.CopyAction
                bridge._finish_drag(__import__('json').dumps({'paths':[str(root / 'folder')]}))
                mime = drag.return_value.setMimeData.call_args.args[0]
                self.assertEqual([url.toLocalFile() for url in mime.urls()], [str(root / 'folder').replace('\\', '/')])
                drag.return_value.exec.assert_called_once_with(Qt.CopyAction, Qt.CopyAction)
            self.assertIn('전달', messages[-1])

    def test_released_button_does_not_silently_start_native_drag(self):
        bridge = CoreBridge()
        messages = []
        bridge.dragStatus.connect(messages.append)
        with patch('src.bridge.tools_bridge.QApplication.mouseButtons', return_value=Qt.NoButton), \
                patch('src.bridge.tools_bridge.QDrag') as drag:
            bridge._finish_drag('{"paths":["unused"]}')
            drag.assert_not_called()
        self.assertIn('다시', messages[-1])

    def test_nested_export_across_formats_and_passwords(self):
        for fmt, password in [('ZIP', None), ('7Z', None), ('7Z', 'secret'), ('TAR', None), ('TAR.GZ', None), ('TAR.XZ', None)]:
            with self.subTest(format=fmt, encrypted=bool(password)), tempfile.TemporaryDirectory() as work:
                root = Path(work)
                tree = root / '자료'
                for folder, content in [('a', b'one'), ('b', b'two')]:
                    (tree / folder).mkdir(parents=True)
                    (tree / folder / 'same.txt').write_bytes(content)
                archive = root / ('source.' + fmt.lower())
                ArchiveManager.create_archive([str(tree)], str(archive), fmt, password=password)
                paths = DragExportManager(root / 'drag').prepare(str(archive), ['자료/'], password)
                self.assertEqual(len(paths), 1)
                self.assertEqual((Path(paths[0]) / 'a/same.txt').read_bytes(), b'one')
                self.assertEqual((Path(paths[0]) / 'b/same.txt').read_bytes(), b'two')

    def test_empty_directory_mixed_and_overlapping_selection(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root / 'mixed.zip'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('root/empty/', b'')
                archive.writestr('root/a/sub/data.txt', b'a')
                archive.writestr('root/b/data.txt', b'b')
                archive.writestr('other/no.txt', b'no')
            manager = DragExportManager(root / 'drag')
            paths = manager.prepare(str(source), ['root/empty/', 'root/a/', 'root/a/sub/data.txt', 'root/b/data.txt'])
            self.assertEqual({Path(p).name for p in paths}, {'empty', 'a', 'data.txt'})
            self.assertEqual(len(paths), 3)
            folder = next(Path(p) for p in paths if Path(p).name == 'a')
            self.assertEqual((folder / 'sub/data.txt').read_bytes(), b'a')
            self.assertFalse((folder.parent.parent / 'other').exists())
            with self.assertRaises(FileNotFoundError):
                manager.prepare(str(source), ['root/a/', 'missing.txt'])

    def test_nested_iso_directory(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            tree = root / 'pictures'
            (tree / 'one').mkdir(parents=True)
            (tree / 'one/image.txt').write_bytes(b'iso')
            archive = root / 'disc.iso'
            ArchiveManager.create_iso([str(tree)], str(archive))
            paths = DragExportManager(root / 'drag').prepare(str(archive), ['pictures/'])
            self.assertEqual([Path(p).name for p in paths], ['pictures'])
            self.assertEqual((Path(paths[0]) / 'one/image.txt').read_bytes(), b'iso')

    def test_implicit_directory_retains_complete_tree(self):
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root / 'implicit.zip'
            with zipfile.ZipFile(source, 'w') as archive:
                archive.writestr('project/a/readme.txt', b'a')
                archive.writestr('project/b/readme.txt', b'b')
            manager = DragExportManager(root / 'drag')
            paths = manager.prepare(str(source), ['project/'])
            self.assertEqual([Path(p).name for p in paths], ['project'])
            self.assertEqual((Path(paths[0]) / 'a/readme.txt').read_bytes(), b'a')
            self.assertEqual((Path(paths[0]) / 'b/readme.txt').read_bytes(), b'b')


if __name__ == '__main__':
    unittest.main()

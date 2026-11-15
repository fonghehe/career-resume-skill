"""Failed output writes preserve old artifacts and permit safe retries."""

from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

from career_resume.build_career import build as build_career
from career_resume.build_timeline import build as build_timeline
from career_resume.create_demo import create
from career_resume.export_share import export as export_share
from career_resume.import_git_activity import write_report
from career_resume.init_profile import initialize
from career_resume.package import export


class PartialWrite:
    def __init__(self, stream):
        self.stream = stream

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return self.stream.__exit__(*args)

    def __getattr__(self, name):
        return getattr(self.stream, name)

    def write(self, data):
        self.stream.write(data[:8])
        self.stream.flush()
        raise OSError('simulated full disk')


class WriteRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'source'
        export(ROOT, self.root, directory=True)

    def tearDown(self):
        self.temp.cleanup()

    def test_failed_generated_artifact_replacement_preserves_old_output(self):
        for build in (build_career, build_timeline):
            with self.subTest(build=build.__module__):
                target = build(self.root)
                original = target.read_bytes()
                existing = set(target.parent.iterdir())
                with patch('os.replace', side_effect=PermissionError('output temporarily locked')):
                    with self.assertRaises(PermissionError):
                        build(self.root)
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(set(target.parent.iterdir()), existing)
                self.assertEqual(build(self.root), target)

    def test_failed_exclusive_report_write_cleans_partial_file_and_can_retry(self):
        target = self.base / 'activity.json'
        original_open = Path.open

        def fail_write(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return PartialWrite(stream) if path == target else stream

        with patch.object(Path, 'open', fail_write):
            with self.assertRaises(OSError):
                write_report({'scope': 'fictional-test-only'}, target)
        self.assertFalse(target.exists())
        write_report({'scope': 'fictional-test-only'}, target)
        original = target.read_bytes()
        with self.assertRaises(FileExistsError):
            write_report({'scope': 'must-not-replace'}, target)
        self.assertEqual(target.read_bytes(), original)

    def test_failed_template_write_cleans_partial_file_and_preserves_existing_profile(self):
        runtime = self.base / 'runtime'
        export(self.root, runtime, directory=True, runtime=True)
        target = runtime / '.gitignore'
        profile = runtime / 'local/references/profile.md'
        profile.parent.mkdir(parents=True)
        profile.write_text('Fictional existing personal notes')
        original_open = Path.open

        def fail_write(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return PartialWrite(stream) if path == target else stream

        with patch.object(Path, 'open', fail_write):
            with self.assertRaises(OSError):
                initialize(runtime)
        self.assertFalse(target.exists())
        self.assertEqual(profile.read_text(), 'Fictional existing personal notes')
        initialize(runtime)
        self.assertEqual(target.read_bytes(), (runtime / 'assets/starter/gitignore.txt').read_bytes())

    def test_failed_write_keeps_a_newer_file_that_replaced_its_output(self):
        target = self.base / 'activity.json'
        replacement = self.base / 'newer-result.json'
        replacement.write_bytes(b'newer independent result')
        original_open = Path.open

        class ReplacedWrite(PartialWrite):
            def write(self, data):
                self.stream.write(data[:8])
                self.stream.flush()
                replacement.replace(target)
                raise OSError('original writer failed after another writer published')

        def fail_write(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return ReplacedWrite(stream) if path == target else stream

        with patch.object(Path, 'open', fail_write):
            with self.assertRaises(OSError):
                write_report({'scope': 'fictional-test-only'}, target)
        self.assertTrue(target.exists())
        self.assertEqual(target.read_bytes(), b'newer independent result')

    def test_failed_public_zip_copy_cleans_partial_export_and_can_retry(self):
        target = self.base / 'public.zip'
        original_open = Path.open

        def fail_write(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return PartialWrite(stream) if path == target else stream

        with patch.object(Path, 'open', fail_write):
            with self.assertRaises(OSError):
                export(self.root, target)
        self.assertFalse(target.exists())
        export(self.root, target)
        self.assertTrue(target.is_file())

    def test_failed_share_render_does_not_leave_an_empty_export(self):
        create(self.root, self.base / 'demo')
        target = self.base / 'demo/output/shares/review.html'
        with patch('career_resume.export_share.render_html', side_effect=ValueError('render failed')):
            with self.assertRaises(ValueError):
                export_share(self.base / 'demo', ['P03'], target)
        self.assertFalse(target.exists())
        export_share(self.base / 'demo', ['P03'], target)
        self.assertIn('timeline-data', target.read_text())

    def test_timeline_rejects_sources_symlinks_and_handwritten_html(self):
        profile = self.root / 'local/references/profile.md'
        original = profile.read_bytes()
        with self.assertRaises(ValueError):
            build_timeline(self.root, profile)
        self.assertEqual(profile.read_bytes(), original)
        handwritten = self.base / 'notes.html'
        handwritten.write_text('<p>Fictional handwritten notes</p>')
        with self.assertRaises(ValueError):
            build_timeline(self.root, handwritten)
        self.assertEqual(handwritten.read_text(), '<p>Fictional handwritten notes</p>')
        link = self.base / 'linked.html'
        link.symlink_to(handwritten)
        with self.assertRaises(ValueError):
            build_timeline(self.root, link)
        self.assertEqual(handwritten.read_text(), '<p>Fictional handwritten notes</p>')


if __name__ == '__main__':
    unittest.main()

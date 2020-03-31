# -*- coding: utf-8 -*-

# Copyright 2012 Mats Ekberg
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from __future__ import with_statement
import sys, os, unittest, tempfile, shutil

TMPDIR=tempfile.gettempdir()

if __name__ == '__main__':
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import common

class TestGetTree(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix=u'testcommon_gettreeÅÄÖ_', dir=TMPDIR)
        self.testdir = os.path.join(self.tmpdir, u"testdirÅÄÖ")
        os.mkdir(self.testdir)

        # Ensure that this directory contains at least one file, so
        # that we notice if the scan erronously includes this
        # directory.
        open(os.path.join(self.tmpdir, u"NOT_INCLUDED_IN_TEST.MARKER"), "w")

        self.old_cwd = os.getcwd()
        os.chdir(self.tmpdir)

    def tearDown(self):
        os.chdir(self.old_cwd)
        shutil.rmtree(self.tmpdir, ignore_errors = True)

    def fullpath(self, fn):
        assert not os.path.isabs(fn)
        fn = fn.replace("/", os.sep)
        return os.path.join(self.testdir, fn)

    def addFile(self, fn, data = None):
        assert not os.path.isabs(fn)
        if data == None:
            data = fn
        if type(data) == unicode:
            data = data.encode('utf8')
        dirname = os.path.dirname(fn)
        if dirname:
            os.makedirs(self.fullpath(dirname))
        open(self.fullpath(fn), 'w').write(data)

    def assertTreeEquals(self, tree, expected):
        #print tree
        #print expected
        self.assertEquals(sorted(tree), sorted(expected))

    def assertTreeExists(self, tree, root=None):
        for fn in tree:
            if root:
                self.assertFalse(os.path.isabs(fn))
                fn = root + os.sep + fn # No os.path.join - too clever
            self.assertTrue(os.path.exists(fn), fn)

    def testTestTools(self):
        self.assertTrue(os.path.isabs(self.fullpath(u'test1.txt')))

    def testSimple(self):
        self.addFile('test1.txt')
        self.addFile('subdir/test2.txt')
        self.addFile(u'räksmörgåsar/räksmörgås.txt')

        tree = common.get_tree(self.testdir)
        self.assertTreeEquals(tree, [u'test1.txt',
                                     u'subdir' + os.sep + 'test2.txt',
                                     u'räksmörgåsar' + os.sep + u'räksmörgås.txt'])
        self.assertTreeExists(tree, root=self.testdir)

    def testSkip(self):
        self.addFile('test1.txt')
        self.addFile('subdir/test2.txt')
        self.addFile(u'räksmörgåsar/räksmörgås.txt')

        tree = common.get_tree(self.testdir, skip=['subdir'])
        self.assertTreeEquals(tree, [u'test1.txt',
                                     u'räksmörgåsar' + os.sep + u'räksmörgås.txt'])

        tree = common.get_tree(self.testdir, skip=['test2.txt', u'räksmörgåsar'])
        self.assertTreeEquals(tree, [u'test1.txt'])

    def testSimpleWithRelativeRoot(self):
        self.addFile('test1.txt')
        self.addFile('subdir/test2.txt')
        self.addFile(u'räksmörgåsar/räksmörgås.txt')

        self.assertTrue(os.path.exists(u'testdirÅÄÖ'))
        tree = common.get_tree(u'testdirÅÄÖ')
        self.assertTreeEquals(tree, [u'test1.txt',
                                     u'subdir' + os.sep + 'test2.txt',
                                     u'räksmörgåsar' + os.sep + u'räksmörgås.txt'])
        self.assertTreeExists(tree, root=self.testdir)

    def testAbsolute(self):
        self.addFile('test1.txt')
        self.addFile('subdir/test2.txt')
        self.addFile(u'räksmörgåsar/räksmörgås.txt')

        tree = common.get_tree(self.testdir, absolute_paths = True)
        self.assertTreeEquals(tree, [self.fullpath(u'test1.txt'),
                                     self.fullpath(u'subdir' + os.sep + 'test2.txt'),
                                     self.fullpath(u'räksmörgåsar' + os.sep + u'räksmörgås.txt')])
        self.assertTreeExists(tree)

    def testAbsoluteWithRelativeRoot(self):
        self.addFile('test1.txt')
        self.addFile('subdir/test2.txt')
        self.addFile(u'räksmörgåsar/räksmörgås.txt')

        tree = common.get_tree(u'testdirÅÄÖ', absolute_paths = True)
        self.assertTreeEquals(tree, [self.fullpath(u'test1.txt'),
                                     self.fullpath(u'subdir' + os.sep + 'test2.txt'),
                                     self.fullpath(u'räksmörgåsar' + os.sep + u'räksmörgås.txt')])
        self.assertTreeExists(tree)

class TestStrictFileWriterBasics(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='testcommon_', dir=TMPDIR)
        self.filename = os.path.join(self.tmpdir, "test.txt")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors = True)

    def testEmptyFile(self):
        sfw = common.StrictFileWriter(self.filename, "d41d8cd98f00b204e9800998ecf8427e", 0)
        sfw.close()
        self.assertEquals("", open(self.filename).read())

    def testWithHappy(self):
        with common.StrictFileWriter(self.filename, "6118fda28fbc20966ba8daafdf836683", len("avocado")) as sfw:
            sfw.write("avocado")

    def testWithTooShort(self):
        def dotest():
            with common.StrictFileWriter(self.filename, "6118fda28fbc20966ba8daafdf836683", len("avocado")) as sfw:
                sfw.write("avocad")
        self.assertRaises(common.ConstraintViolation, dotest)

    def testWithTooShort2(self):
        def dotest():
            with common.StrictFileWriter(self.filename, "6118fda28fbc20966ba8daafdf836683", len("avocado")) as sfw:
                pass
        self.assertRaises(common.ConstraintViolation, dotest)


class TestStrictFileWriterEnforcement(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix='testcommon_', dir=TMPDIR)
        self.filename = os.path.join(self.tmpdir, "avocado.txt")
        self.sfw = common.StrictFileWriter(self.filename, "6118fda28fbc20966ba8daafdf836683", len("avocado"))

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors = True)

    def testExisting(self):
        self.sfw.write("avocado")
        self.sfw.close()
        self.assertRaises(common.ConstraintViolation, common.StrictFileWriter, self.filename, \
                              "fe01d67a002dfa0f3ac084298142eccd", len("orange"))
        self.assertEquals("avocado", open(self.filename).read())

    def testExistingOverwrite(self):
        self.sfw.write("avocado")
        self.sfw.close()
        with common.StrictFileWriter(self.filename, "fe01d67a002dfa0f3ac084298142eccd", \
                                         len("orange"), overwrite = True) as sfw2:
            sfw2.write("orange")
        self.assertEquals("orange", open(self.filename).read())

    def testOverrun(self):
        self.assertRaises(common.ConstraintViolation, self.sfw.write, "avocadoo")

    def testOverrun2(self):
        self.sfw.write("avo")
        self.sfw.write("cad")
        self.sfw.write("o")
        self.assertRaises(common.ConstraintViolation, self.sfw.write, "o")

    def testUnderrun(self):
        self.sfw.write("avocad")
        self.assertRaises(common.ConstraintViolation, self.sfw.close)

    def testHappyPath(self):
        self.sfw.write("avocado")
        self.sfw.close()
        self.assertEquals("avocado", open(self.filename).read())

    def testHappyPath2(self):
        self.sfw.write("")
        self.sfw.write("avo")
        self.sfw.write("cad")
        self.sfw.write("")
        self.sfw.write("o")
        self.sfw.write("")
        self.sfw.close()
        self.assertEquals("avocado", open(self.filename).read())

    def testWrongChecksum(self):
        self.assertRaises(common.ConstraintViolation, self.sfw.write, "avocato")

    def testWithHappyPath(self):
        with self.sfw:
            self.sfw.write("avocado")
        self.assertTrue(self.sfw.is_closed())
        self.assertEquals("avocado", open(self.filename).read())

    def testWithContentViolation(self):
        try:
            with self.sfw:
                self.sfw.write("AVOCADO")
            assert False, "Should throw an exception"
        except Exception, e:
            # Must be a content violation
            self.assertEquals(type(e), common.ContentViolation)
        self.assertTrue(self.sfw.is_closed())

    def testWithUnderrunViolation(self):
        try:
            with self.sfw:
                self.sfw.write("AVO")
            assert False, "Should throw an exception"
        except Exception, e:
            # Must be a size violation
            self.assertEquals(type(e), common.SizeViolation)
        self.assertTrue(self.sfw.is_closed())

    def testWithOverrunViolation(self):
        try:
            with self.sfw:
                self.sfw.write("avocados")
            assert False, "Should throw an exception"
        except Exception, e:
            # Must be a size violation
            self.assertEquals(type(e), common.SizeViolation)
        self.assertTrue(self.sfw.is_closed())

class TestStripPathOffset(unittest.TestCase):
    def testSimple(self):
        self.assertEquals("b", common.strip_path_offset("/a", "/a/b"))
        self.assertEquals("", common.strip_path_offset("/a", "/a"))

    def testArgumentChecks(self):
        # Offset must not end with slash.
        self.assertRaises(AssertionError, common.strip_path_offset, "/a/", "/a/b/")
        # The child path must start with the offset
        self.assertRaises(AssertionError, common.strip_path_offset, "/b", "/a")

class TestTailBuffer(unittest.TestCase):
    def test_large_buffer(self):
        tb = common.TailBuffer()
        ONE_HUNDRED_MB = "x" * (100 * 2**20)
        for n in range(50): # 5GB should be enough for anyone
            tb.append(ONE_HUNDRED_MB)
            size = tb.virtual_size()
            self.assertTrue(isinstance(size, (int, long)))
            tb.release(size)
        self.assertEqual(tb.virtual_size(), 50 * 100 * 2**20)

class TestMisc(unittest.TestCase):
    def test_common_tail(self):
        def test(s1, s2, expected):
            result = common.common_tail(s1, s2)
            self.assertEquals(expected, result)
        test("abc", "abc", "abc")
        test("c", "abc", "c")
        test("abc", "c", "c")
        test("bc", "abc", "bc")
        test("abc", "bc", "bc")
        test("abc", "a", "")
        test("a", "abc", "")

    def test_invert_dict(self):
        inv_d = common.invert_dict({
            "k1": "v1",
            "kx": "v2",
            "k2": "v2",
            "k3": "v3",
        })

        self.assertEqual(sorted(inv_d.keys()), ["v1", "v2", "v3"])
        self.assertEqual(inv_d["v1"], ["k1"])
        self.assertEqual(set(inv_d["v2"]), set(["k2", "kx"]))
        self.assertEqual(inv_d["v3"], ["k3"])


if __name__ == '__main__':
    unittest.main()


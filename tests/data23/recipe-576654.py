#!/usr/bin/python

# This is for different methods to do unittests.
# Should serve as a handy reference and quick-lookup instead of digging into the
# docs.

import unittest

def raises_error(*args, **kwargs):
    print(args, kwargs)
    raise ValueError("Invalid Value:" + str(args), str(kwargs))

class UnitTestExamples(unittest.TestCase):

    def setUp(self):
        print('In setUp()')
        self.fixture = list(range(1,10))

    def tearDown(self):
        print('In tearDown()')
        del self.fixture

    # The following 3 Testcases are Same.

    def testAssertAlmostEqual(self):
        self.assertAlmostEqual(3.1, 4.24-1.1, places=1,msg="Upto 1 decimal place.")

    def testAssertAlmostEquals(self):
        self.assertAlmostEqual(3.1, 4.24-1.1, places=1,msg="Upto 1 decimal place.")

    def testFailUnlessAlmostEqual(self):
        self.assertAlmostEqual(3.1, 4.24-1.1, places=1,msg="Upto 1 decimal place.")

    # The following 3 Testcases are same.

    def testAssertEqual(self):
        self.assertEqual(True,True)
        self.assertEqual(False,False)

    def testAssertEquals(self):
        self.assertEqual(True,True)
        self.assertEqual(False,False)

    def testFailUnlessEqual(self):
        self.assertEqual(True,True)
        self.assertEqual(False,False)

    # The following 2 testcases are same.

    def testAssertFalse(self):
        self.assertFalse(False)

    def testFailIf(self):
        self.assertFalse(False)

    # The following 3 testcases are same.

    def testAssertNotAlmostEqual(self):
        self.assertNotAlmostEqual(1.1,1.9,places=1)

    def testAssertNotAlmostEquals(self):
        self.assertNotAlmostEqual(1.1,1.9,places=1)

    def testFailIfAlmostEqual(self):
        self.assertNotAlmostEqual(1.1,1.9,places=1)

    # The following 3 testcases are same.

    def testAssertNoEqual(self):
        self.assertNotEqual(True,False)
        self.assertNotEqual(False,True)

    def testAssertNoEquals(self):
        self.assertNotEqual(True,False)
        self.assertNotEqual(False,True)

    def testFailIfEqual(self):
        self.assertNotEqual(False,True)

    # The following 2 testcases are same.

    def testAssertRaises(self):
        self.assertRaises(ValueError, raises_error, 'a',b='c')

    def testFailUnlessRaises(self):
        self.assertRaises(ValueError, raises_error, 'a',b='c')

    # The following 3 testcases are same.

    def testAssertTrue(self):
        self.assertTrue(True)

    def testFailUnless(self):
        self.assertTrue(True)

    def testassert_(self):
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()

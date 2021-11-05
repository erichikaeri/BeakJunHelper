import os
import unittest
import sys

sys.path.insert(1, os.path.join(sys.path[0], '..'))
import Tester


Problem1005Input1 = """2
4 4
10 1 100 10
1 2
1 3
2 4
3 4
4
8 8
10 20 1 5 8 7 1 43
1 2
1 3
2 4
2 5
3 6
5 7
6 7
7 8
7"""

Problem1005Output1 = """120
39"""

Problem1005Input2 = """5
3 2
1 2 3
3 2
2 1
1
4 3
5 5 5 5
1 2
1 3
2 3
4
5 10
100000 99999 99997 99994 99990
4 5
3 5
3 4
2 5
2 4
2 3
1 5
1 4
1 3
1 2
4
4 3
1 1 1 1
1 2
3 2
1 4
4
7 8
0 0 0 0 0 0 0
1 2
1 3
2 4
3 4
4 5
4 6
5 7
6 7
7"""

Problem1005Output2 = """6
5
399990
2
0"""

Problem1018Input1 = """8 8
WBWBWBWB
BWBWBWBW
WBWBWBWB
BWBBBWBW
WBWBWBWB
BWBWBWBW
WBWBWBWB
BWBWBWBW"""

Problem1018Output1 = "1"

Problem1018Input2 = """10 13
BBBBBBBBWBWBW
BBBBBBBBBWBWB
BBBBBBBBWBWBW
BBBBBBBBBWBWB
BBBBBBBBWBWBW
BBBBBBBBBWBWB
BBBBBBBBWBWBW
BBBBBBBBBWBWB
WWWWWWWWWWBWB
WWWWWWWWWWBWB"""

Problem1018Output2 = "12"


class TestBJFetcher(unittest.TestCase):
    def setUp(self):
        self.fetcher = Tester.BJFetcher()

    def test_Fetch(self):
        self.fetcher.Fetch("1005")
        testCases = self.fetcher.GetTestCases()

        self.assertEqual(testCases[0][0], Problem1005Input1)
        self.assertEqual(testCases[0][1], Problem1005Output1)
        self.assertEqual(testCases[1][0], Problem1005Input2)
        self.assertEqual(testCases[1][1], Problem1005Output2)

        self.fetcher.Fetch("1018")
        testCases = self.fetcher.GetTestCases()

        self.assertEqual(testCases[0][0], Problem1018Input1)
        self.assertEqual(testCases[0][1], Problem1018Output1)
        self.assertEqual(testCases[1][0], Problem1018Input2)
        self.assertEqual(testCases[1][1], Problem1018Output2)


class TestTestCaseStorage(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = Tester.ExeFolderManager()
        self.testCases = [(Problem1005Input1, Problem1005Output1), (Problem1018Input2, Problem1018Output2)]

    def test_SaveLoad(self):
        storage = self.manager.CreateTestCaseStorage("123123123")
        self.assertTrue(os.path.isdir("123123123"))
        self.assertTrue(os.path.isfile("123123123/123123123.cpp"))

        storage.Save(self.testCases)
        self.assertTrue(os.path.isfile("123123123/testCases.txt"))

        storage = self.manager.GetTestCaseStorage("123123123")
        loadedTestCases = storage.GetTestCases()
        self.assertEqual(loadedTestCases, self.testCases)

        self.manager.DeleteTestCaseStorage("123123123")
        self.assertFalse(os.path.isdir("123123123"))


class TestExeTester(unittest.TestCase):
    def setUp(self) -> None:
        self.tester = Tester.ExeTester()
        self.programPath = os.path.join("Test", "MultiplyByTwo.exe")
        self.newlineProgramPath = os.path.join("Test", "PrintNewLines.exe")

    def test_TesterOK(self):
        testCases = [("1", "2"), ("2", "4"), ("3", "6")]
        testResult = self.tester.Test(self.programPath, testCases)
        self.assertTrue(testResult is None)

    def test_TesterFail(self):
        testCases = [("1", "2"), ("2", "4"), ("3", "7")]
        testResult = self.tester.Test(self.programPath, testCases)
        self.assertTrue(testResult is not None)
        self.assertEqual(testResult[0], "3")
        self.assertEqual(testResult[1], "6")
        self.assertEqual(testResult[2], "7")

    def test_TesterTrailingSpaces(self):
        # 윈도우 스타일과 리눅스 스타일을 섞어서 테스트 해본다.
        testCases = [("1", "1\r\n"), ("2", "1\r\n2\r\n"), ("3", "1\n2\n3\n")]
        testResult = self.tester.Test(self.newlineProgramPath, testCases)
        self.assertTrue(testResult is None)

    
class TestPyhonTester(TestExeTester):
    def setUp(self) -> None:
        self.tester = Tester.PythonTester()
        self.programPath = os.path.join("Test", "MultiplyByTwo.py")
        self.newlineProgramPath = os.path.join("Test", "PrintNewLines.py")

if __name__ == "__main__":
    unittest.main()
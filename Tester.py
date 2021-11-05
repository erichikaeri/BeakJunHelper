import os
import shutil
import subprocess
from typing import Tuple
import requests
from bs4 import BeautifulSoup
import json


TestCase = Tuple[str, str]


class BJFetcher:
    def __init__(self) -> None:
        self.testCases: list[TestCase] = []

    def Fetch(self, problemNumber: str) -> None:
        '''This function only fetches. Get fetch results from other functions. Throws if fetch fails.'''

        self.testCases = []
        response = requests.get("https://www.acmicpc.net/problem/{0}".format(problemNumber))
        soup = BeautifulSoup(response.text, "html.parser")
        
        i = 1
        while True:
            sampleInputSelector = "#sample-input-{0}".format(i)
            sampleOutputSelector = "#sample-output-{0}".format(i)

            sampleInput = soup.select_one(sampleInputSelector)
            sampleOutput = soup.select_one(sampleOutputSelector)

            somethingWrong = bool(sampleInput) != bool(sampleOutput)
            endOfSamples = not sampleInput

            if somethingWrong:
                raise RuntimeError("Bad BaekJun: either input or output was present but the other was not.")

            if endOfSamples:
                break

            self.testCases.append((sampleInput.text.strip(), sampleOutput.text.strip()))
            i += 1

    def GetTestCases(self) -> list[TestCase]:
        '''Returns a list of test cases as tuples in which key is input and value is expected output.'''
        return self.testCases


class TestCaseStorage:
    def __init__(self, absolutePath: str) -> None:
        self.filePath = os.path.join(absolutePath, "testCases.txt")

    def Save(self, testCases: list[TestCase]) -> None:
        '''Saves test cases to permanent storage such as the file system.'''

        with open(self.filePath, "w") as f:
            json.dump(testCases, f, indent=4)

    def GetTestCases(self) -> list[TestCase]:
        '''Returns a list of test cases as tuples in which key is input and value is expected output.'''

        with open(self.filePath, "r") as f:
            listOfLists = json.load(f)

        return list(map(lambda each: tuple(each), listOfLists))


class ExeFolderManager:
    def CreateTestCaseStorage(self, problemNumber: str) -> TestCaseStorage:
        if os.path.isdir(problemNumber):
            raise FileExistsError()

        os.mkdir(problemNumber)
        
        templateFileName = "CPPTemplate.cpp"
        templateDestFileName = "{}.cpp".format(problemNumber)
        templateDestPath = os.path.join(problemNumber, templateDestFileName)
        shutil.copyfile(templateFileName, templateDestPath)

        return TestCaseStorage(os.path.abspath(problemNumber))

    def DeleteTestCaseStorage(self, problemNumber: str) -> None:
        if not os.path.isdir(problemNumber):
            return

        shutil.rmtree(problemNumber)

    def GetTestCaseStorage(self, problemNumber: str) -> TestCaseStorage:
        if not os.path.isdir(problemNumber):
            raise FileNotFoundError("You need to call CreateProblemStorage first.")

        return TestCaseStorage(os.path.abspath(problemNumber))

    def GetProgramAbsolutePath(self, problemNumber: str) -> str:
        relPath = os.path.join(problemNumber, "{}.exe".format(problemNumber))
        return os.path.abspath(relPath)


class PythonFolderManager(ExeFolderManager):
    '''따로 구현하는 게 맞지만 귀찮으므로 상속'''
    def CreateProblemStorage(self, problemNumber: str) -> TestCaseStorage:
        pass

    def GetProgramAbsolutePath(self, problemNumber: str) -> str:
        pass


class ExeTester:
    def Test(self, programPath: str, testCases: list[TestCase]) -> Tuple[str, str, str]:
        '''Returns a tuple of ProgramInput, ProgramOutput, ExpectedOutput if test fails. None otherwise.'''

        if not os.path.isfile(programPath):
            raise FileNotFoundError("Program does not exist at {}. Did you forget to compile it?".format(programPath))

        for eachTestCase in testCases:
            programInput = self._processString(eachTestCase[0])
            programOutput = self._processString(self.RunProgram(programPath, programInput))
            expectedOutput = self._processString(eachTestCase[1])

            if programOutput != expectedOutput:
                return (programInput, programOutput, expectedOutput)

        return None

    @staticmethod
    def RunProgram(programPath, testInput) -> str:
        '''Returns program output as string.'''

        proc = subprocess.Popen(programPath, stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE)
        out, errs = proc.communicate(input=testInput.encode("utf-8"))

        return out.decode("utf-8").strip()

    @staticmethod
    def _processString(string: str):
        return string.strip().replace("\r\n", "\n")


class PythonTester:
    def Test(self, sourceFilePath: str, testCases: list[TestCase]) -> Tuple[str, str, str]:
        pass


def Init(problemNumber: str):
    fetcher = BJFetcher()
    manager = ExeFolderManager()

    while True:
        try:
            storage = manager.CreateTestCaseStorage(problemNumber)
            break
        except FileExistsError:
            pass
            
        ans = input("Directory for the problem already exists. Delete and proceed? (y/n) ").lower()

        if ans == "y":
            manager.DeleteTestCaseStorage(problemNumber)
        elif ans == "n":
            return

    try:
        fetcher.Fetch(problemNumber)
    except Exception as e:
        print(e)
        return

    storage.Save(fetcher.GetTestCases())


def Test(problemNumber: str):
    manager = ExeFolderManager()

    try:
        storage = manager.GetTestCaseStorage(problemNumber)
    except Exception as e:
        print(e)
        return

    tester = ExeTester()

    try:
        testResult = tester.Test(manager.GetProgramAbsolutePath(problemNumber), storage.GetTestCases())
    except Exception as e:
        print(e)
        return

    if testResult is None:
        print("OK!")
        return

    programInput = testResult[0]
    programOutput = testResult[1]
    expectedOutput = testResult[2]

    print("""===============
Input:
{0}
===============
Your Output:
{1}
===============
Expected:
{2}
===============""".format(programInput, programOutput, expectedOutput))


if __name__ == "__main__":
    while True:
        problemNumber = input("Problem Number: ")

        while True:
            action = input("Action (init or test or back): ")

            if action == "init":
                Init(problemNumber)
            elif action == "test":
                Test(problemNumber)
            elif action == "back":
                break
            else:
                print("Invalid Action.")
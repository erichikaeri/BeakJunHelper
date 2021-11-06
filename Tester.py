import os
from posixpath import relpath
import shutil
import subprocess
from typing import Tuple
import requests
from bs4 import BeautifulSoup
import json
from abc import ABC, abstractmethod


TestCase = Tuple[str, str]


def StripNewline(string: str):
    linuxStyle = string.replace("\r\n", "\n")
    lines = filter(None, linuxStyle.split("\n"))
    lines = map(lambda each: each.strip(), lines)
    return "\n".join(lines)


class BJFetcher:
    def __init__(self) -> None:
        self.testCases: list[TestCase] = []

    def Fetch(self, problemNumber: str) -> None:
        '''This function only fetches. Get fetch results from other functions. Throws if fetch fails.'''

        self.testCases = []
        response = requests.get(self.GetWebAddress(problemNumber))
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

    def GetWebAddress(self,  problemNumber: str) -> str:
        return "https://www.acmicpc.net/problem/{0}".format(problemNumber)


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
        return os.path.join(self.GetFolderAbsolutePath(problemNumber), self.GetProgramName(problemNumber))

    def GetFolderAbsolutePath(self, problemNumber: str) -> str:
        return os.path.abspath(problemNumber)

    def GetProgramName(self, problemNumber):
        return "{}.exe".format(problemNumber)


class PythonFolderManager(ExeFolderManager):
    '''따로 구현하는 게 맞지만 귀찮으므로 상속'''

    def CreateTestCaseStorage(self, problemNumber: str) -> TestCaseStorage:
        if os.path.isdir(problemNumber):
            raise FileExistsError()

        os.mkdir(problemNumber)
        
        templateDestFileName = self.GetProgramName(problemNumber)
        templateDestPath = os.path.join(problemNumber, templateDestFileName)

        with open(templateDestPath, "w"):
            pass

        return TestCaseStorage(os.path.abspath(problemNumber))

    def GetProgramName(self, problemNumber):
        return "{}.py".format(problemNumber)


class ExeTester:
    def Test(self, programPath: str, testCases: list[TestCase]) -> Tuple[str, str, str]:
        '''Returns a tuple of ProgramInput, ProgramOutput, ExpectedOutput if test fails. None otherwise.'''

        if not os.path.isfile(programPath):
            raise FileNotFoundError("Program does not exist at {}. Did you forget to compile it?".format(programPath))

        for eachTestCase in testCases:
            programInput = StripNewline(eachTestCase[0])
            programOutput = StripNewline(self.RunProgram(programPath, programInput))
            expectedOutput = StripNewline(eachTestCase[1])

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


class PythonTester:
    def Test(self, sourceFilePath: str, testCases: list[TestCase]) -> Tuple[str, str, str]:
        if not os.path.isfile(sourceFilePath):
            raise FileNotFoundError("Source file does not exist at {}. Did you forget to init?".format(sourceFilePath))

        for eachTestCase in testCases:
            programInput = StripNewline(eachTestCase[0])
            programOutput = StripNewline(self.RunProgram(sourceFilePath, programInput))
            expectedOutput = StripNewline(eachTestCase[1])

            if programOutput != expectedOutput:
                return (programInput, programOutput, expectedOutput)

        return None

    @staticmethod
    def RunProgram(sourceFilePath, testInput) -> str:
        command = 'python "{}"'.format(sourceFilePath)

        proc = subprocess.Popen(command, stdout=subprocess.PIPE, 
            stdin=subprocess.PIPE)
        out, errs = proc.communicate(input=testInput.encode("utf-8"))

        return out.decode("utf-8").strip()


class Factory(ABC):
    @abstractmethod
    def CreateFolderManager(self):
        pass

    @abstractmethod
    def CreateTester(self):
        pass

    def CreateFetcher(self):
        return BJFetcher()


class ExeFactory(Factory):
    def CreateFolderManager(self):
        return ExeFolderManager()

    def CreateTester(self):
        return ExeTester()


class PythonFactory(Factory):
    def CreateFolderManager(self):
        return PythonFolderManager()

    def CreateTester(self):
        return PythonTester()


def Init(factory: Factory, problemNumber: str):
    fetcher = factory.CreateFetcher()
    manager = factory.CreateFolderManager()

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


def Test(factory: Factory, problemNumber: str):
    manager = factory.CreateFolderManager()

    try:
        storage = manager.GetTestCaseStorage(problemNumber)
    except Exception as e:
        print(e)
        return

    tester = factory.CreateTester()

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

    print()
    print("Test Failed:")
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


def Web(factory: Factory, problemNumber: str):
    fetcher = factory.CreateFetcher()
    addr = fetcher.GetWebAddress(problemNumber)
    command = 'explorer "{}"'.format(addr)
    subprocess.Popen(command)


def Folder(factory: Factory, problemNumber: str):
    folderManager = factory.CreateFolderManager()

    try:
        folderManager.GetTestCaseStorage(problemNumber)
    except FileNotFoundError:
        print("No folder found for problem {}. Did you forget to init?".format(problemNumber))
        return

    folderPath = folderManager.GetFolderAbsolutePath(problemNumber)
    command = 'explorer "{}"'.format(folderPath)
    subprocess.Popen(command)


if __name__ == "__main__":
    while True:
        while True:
            print()
            language = input("1. Python\n2. C++\n\nSelect: ")

            if language == "1":
                factory = PythonFactory()
            elif language == "2":
                factory = ExeFactory()
            else:
                continue
            break

        problemNumber = input("Problem Number: ")

        while True:
            print()
            action = input("1. Init\n2. Test\n3. Web\n4. Folder\n5. Back\n\nSelect: ")

            if action == "1":
                Init(factory, problemNumber)
            elif action == "2":
                Test(factory, problemNumber)
            elif action == "3":
                Web(factory, problemNumber)
            elif action == "4":
                Folder(factory, problemNumber)
            elif action == "5":
                break
            else:
                print("Invalid Action.")
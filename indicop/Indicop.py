# -*- coding: utf-8 -*-
##
## $Id$
##
## This file is part of CDS Indico.
## Copyright (C) 2002, 2003, 2004, 2005, 2006, 2007 CERN.
##
## CDS Indico is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License as
## published by the Free Software Foundation; either version 2 of the
## License, or (at your option) any later version.
##
## CDS Indico is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
## General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with CDS Indico; if not, write to the Free Software Foundation, Inc.,
## 59 Temple Place, Suite 330, Boston, MA 02111-1307, USA.


import os
import sys
import nose
import figleaf
import figleaf.annotate_html
import subprocess
import socket
import time
import commands
import StringIO
import shutil
import signal
import tempfile
from BaseTest import BaseTest
from TestsConfig import TestsConfig
from selenium import selenium
from MaKaC.common.Configuration import Config


class Unit(BaseTest):

    def run(self):
        returnString = ""
        self.startMessage("Starting Python unit tests")

        result = False

        #launch a fresh DB in parallel of the production DB
        try:
            self.startFakeDB(TestsConfig.getInstance().getFakeDBPort())
        except KeyError:
            return "[ERR] Unit tests - Please, specify a FakeDBPort in tests.conf"
        self.createDummyUser()

        try:
            coverage = Coverage.getInstance()
            if coverage != False:
                coverage.start()

            #capturing the stderr
            outerr = StringIO.StringIO()
            sys.stderr = outerr


            #retrieving tests from Indicop folder
            args = ['nose', '--nologcapture', '--logging-clear-handlers', '-v',
                    os.path.join(self.setupDir, 'python', 'unit')]
            #retrieving tests from plugins folder
            for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                               '..',
                                                               'indico',
                                                               'MaKaC',
                                                               'plugins'),
                                                  "/tests/python/unit"):
                args.append(folder)

            result = nose.run(argv = args)

            #restoring the stderr
            sys.stderr = sys.__stderr__


            if coverage:
                returnString += coverage.stop()

            s = outerr.getvalue()
            returnString += self.writeReport("pyunit", s)
        finally:
            #self.deleteDummyUser()
            #stopping the fake DB
            self.stopFakeDB()
            self.restoreDBInstance()

        if result:
            return returnString + "PY Unit tests succeeded\n"
        else:
            return returnString + \
                "[FAIL] Unit tests - report in indicop/report/pyunit.txt\n"

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'indico',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/unit") > 0:
                foldersArray.append(root)

        return foldersArray

class Coverage(BaseTest):
    """This class is a singleton instantiate by Indicop class and
    used by Python Unit tests.
    """
    __instance = None

    def start(self):
        figleaf.start()

    def stop(self):
        figleaf.stop()
        coverageOutput = figleaf.get_data().gather_files()
        coverageDir = os.path.join(self.setupDir, 'report', 'pycoverage')
        try:
            figleaf.annotate_html.report_as_html(coverageOutput,
                                                 coverageDir, [], {})
        except IOError:
            os.mkdir(coverageDir)
            figleaf.annotate_html.report_as_html(coverageOutput,
                                                 coverageDir, [], {})
        return ("PY Coverage - Report generated in "
                             "report/pycoverage/index.html\n")

    def getInstance(cls):
        if cls.__instance == None:
            return False
        return cls.__instance
    getInstance = classmethod( getInstance )

    def instantiate(cls):
        cls.__instance = Coverage()
    instantiate = classmethod( instantiate )

class Functional(BaseTest):
    def __init__(self):
        BaseTest.__init__(self)
        self.child = None

    def run(self):
        returnString = ""
        self.startMessage("Starting Python functional tests")

        #Stop prod DB and launch a fresh DB on this prod db port
        self.stopProductionDB()
        self.startFakeDB(Config.getInstance().getDBConnectionParams()[1])

        try:
            if not self.startSeleniumServer():
                return ('[ERR] Could not start functional tests because selenium'
                        ' server cannot be started.\n')

            #Create dummy user and use this user to create conf, session and so on
            self.createDummyUser()

            #capturing the stderr
            outerr = StringIO.StringIO()
            sys.stderr = outerr

            #retrieving tests from Indicop folder
            args = ['nose', '--nologcapture', '--logging-clear-handlers', '-v',
                    os.path.join(self.setupDir, 'python', 'functional')]
            #retrieving tests from plugins folder
            for folder in self.walkThroughFolders(os.path.join(self.setupDir,
                                                               '..',
                                                               'indico',
                                                               'MaKaC',
                                                               'plugins'),
                                                  "/tests/python/functional"):
                args.append(folder)

            result = nose.run(argv = args)

        finally:
            self.stopSeleniumServer()
            #self.deleteDummyUser()

            #restoring the stderr
            sys.stderr = sys.__stderr__

            #stopping the fake DB
            self.stopFakeDB()
            self.startProductionDB()
            self.restoreDBInstance()

        s = outerr.getvalue()
        returnString += self.writeReport("pyfunctional", s)

        report = ""
        if result:
            report = returnString + "PY Functional tests succeeded\n"
        else:
            report = returnString + ("[FAIL] Functional tests - report in"
                    " indicop/report/pyfunctional.txt\n")
        return report

    def walkThroughPluginsFolders(self):
        rootPluginsPath = os.path.join(self.setupDir,
                                       '..',
                                       'indico',
                                       'MaKaC',
                                       'plugins')
        foldersArray = []

        for root, dirs, files in os.walk(rootPluginsPath):
            if root.endswith("/tests/python/functional") > 0:
                foldersArray.append(root)

        return foldersArray

    def startSeleniumServer(self):
        started = True
        try:
            self.child = subprocess.Popen(["java", "-jar",
                                      os.path.join(self.setupDir,
                                                   'python',
                                                   'functional',
                                                   TestsConfig.getInstance().
                                                   getSeleniumFilename())],
                                      stdout=subprocess.PIPE)
        except OSError, e:
            return ("[ERR] Could not start selenium server - command \"java\""
                    " needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            return "[ERR] Please specify a SeleniumFilename in tests.conf"

        sel = selenium("localhost", 4444, "*chrome", "http://www.cern.ch/")
        for i in range(5):
            try:
                #testing if the selenium server has started
                time.sleep(1)
                sel.start()
                sel.stop()

                #server has started
                break
            except socket.error:
                print 'Selenium has not started yet. Attempt #%s\n' % (i+1)
                time.sleep(5)
        else:
            started = False

        return started

    def stopSeleniumServer(self):
        self.child.kill()

class Specify(Functional):
    def __init__(self, specifyArg):
        self.specify = specifyArg

    def run(self):
        self.startMessage("Starting Python specified tests")

        #if specified path does not contained unit, we are probably dealing
        #with functional tests
        if self.specify.find('unit/') < 0:
            if not self.startSeleniumServer():
                return ('[ERR] Could not start functional tests because selenium'
                        ' server cannot be started.\n')
            try:
                #Stop prod DB and launch a fresh DB on this prod db port
                self.stopProductionDB()
                self.startFakeDB(Config.getInstance().getDBConnectionParams()[1])
                self.createDummyUser()

                #running the test and ouputing in the console
                result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                                   '..',
                                                                   self.specify)])
            finally:
                self.stopSeleniumServer()
                #stopping the fake DB
                self.stopFakeDB()
                self.startProductionDB()
                self.restoreDBInstance()

        else:
            #launch a fresh DB in parallel of the production DB
            try:
                self.startFakeDB(TestsConfig.getInstance().getFakeDBPort())
            except KeyError:
                return "[ERR] Please, specify a FakeDBPort in tests.conf"
            try:
                self.createDummyUser()

                #running the test and ouputing in the console
                result = nose.run(argv=['nose', '-v', os.path.join(self.setupDir,
                                                               '..',
                                                               self.specify)])

            finally:
                self.deleteDummyUser()
                #stopping the fake DB
                self.stopFakeDB()
                self.restoreDBInstance()
        if result:
            return "Specified Test - Succeeded\n"
        else:
            return "[FAIL] Specified Test - read output from console\n"


class TimeoutException(Exception):
    """SIGALARM was sent to the process"""
    pass

def raise_timeout(signum, frame):
    raise TimeoutException("15sec Timeout")

class Grid(BaseTest):
    def __init__(self):
        try:
            self.hubEnv = TestsConfig.getInstance().getHubEnv()
            self.gridData = GridData.getInstance()
            self.gridData.setUrl(TestsConfig.getInstance().getHubURL())
            self.gridData.setPort(TestsConfig.getInstance().getHubPort())
            self.gridData.setActive(False)
            self.configExists = True
        except KeyError:
            self.configExists = False

    def run(self):
        self.startMessage("Starting grid tests")

        if not self.configExists:
            return "[ERR] Grid - Please specify hub configuration in tests.conf"

        try:
            #Stop prod DB and launch a fresh DB on this prod db port
            self.stopProductionDB()
            self.startFakeDB(Config.getInstance().getDBConnectionParams()[1])
            self.createDummyUser()
            self.gridData.setActive(True)

            #Checking if hub is online
            sel = selenium(self.gridData.getUrl(), self.gridData.getPort(),
                           self.hubEnv[0], "http://www.cern.ch/")

            signal.signal(signal.SIGALRM, raise_timeout)
            signal.alarm(15)
            sel.start()
            sel.open("/")
            sel.stop()
            #disable the alarm signal
            signal.alarm(0)

            #capturing the stderr
            outerr = StringIO.StringIO()
            sys.stderr = outerr

            returnString = ""
            for env in self.hubEnv:
                self.gridData.setEnv(env)
                sys.stderr.write('\n~ %s ~\n' % env)
                result = nose.run(argv=['nose', '--nologcapture',
                                        '--logging-clear-handlers', '-v',
                                        os.path.join(self.setupDir,
                                                     'python',
                                                     'functional')])
                if result:
                    returnString += "PY Functional (%s) tests succeeded\n" % env
                else:
                    returnString += ("[FAIL] Functional (%s) tests - report in"
                            " indicop/report/pygrid.txt\n") % env

            #restoring the stderr
            sys.stderr = sys.__stderr__

            s = outerr.getvalue()
            returnString += self.writeReport("pygrid", s)
        except socket.error:
            return ("[ERR] Selenium Grid - Connection refused, check your "
                    "hub's settings (%s:%s)") % \
                    (self.gridData.getUrl(), self.gridData.getPort())
        except TimeoutException, e:
            return "[ERR] Selenium Grid - Hub is probably down (%s:%s) (%s)" % \
                    (self.gridData.getUrl(), self.gridData.getPort(), e)
        finally:
            #disable alarm
            signal.alarm(0)
            #stopping the fake DB
            self.stopFakeDB()
            self.startProductionDB()
            self.restoreDBInstance()
        return returnString

class GridData(BaseTest):
    """Provide informations for selenium grid, data are set from Class Grid
    and are used by seleniumTestCase.py.
    Because nosetest cannot forward the arguments to selenium grid."""

    __instance = None
    def __init__(self):
        self.active = None
        self.url = None
        self.port = None
        self.active = None
        self.currentEnv = None

    def isActive(self):
        return self.active
    def getUrl(self):
        return self.url
    def getPort(self):
        return self.port
    def getEnv(self):
        return self.currentEnv

    def setActive(self, active):
        self.active = active
    def setUrl(self, url):
        self.url = url
    def setPort(self, port):
        self.port = port
    def setEnv(self, env):
        self.currentEnv = env

    @classmethod
    def getInstance(cls):
        if cls.__instance == None:
            cls.__instance = GridData()
        return cls.__instance


class Pylint(BaseTest):
    def run(self):
        returnString = ""
        self.startMessage("Starting pylint tests")

        statusOutput = commands.getstatusoutput("pylint --rcfile=%s %s" %
                                                (os.path.join(self.setupDir,
                                                              'python',
                                                              'pylint',
                                                              'pylint.conf'),
                                                os.path.join(self.setupDir,
                                                             '..',
                                                             'indico',
                                                             'MaKaC', 'conference.py')))
        if statusOutput[1].find("pylint: not found") > -1:
            return ("[ERR] Could not start Source Analysis - "
                    "command \"pylint\" needs to be in your PATH. (%s)\n" %
                                                                statusOutput[1])
        else:
            returnString += self.writeReport("pylint", statusOutput[1])
            return returnString + "PY Lint - report in indicop/report/pylint.txt\n"


class Jsunit(BaseTest):
    def __init__(self, jsSpecify, jsCoverage):
        self.coverage = jsCoverage
        self.specify = jsSpecify

    def run(self):
        self.startMessage("Starting Javascript unit tests")

        #conf file used at run time
        confFile = ("builtConf.conf")
        #path relative to the jar file
        coveragePath = os.path.join('..', '..', 'report', 'jscoverage')

        try:
            #Starting js-test-driver server
            server = subprocess.Popen(["java", "-jar",
                                       os.path.join(self.setupDir,
                                                    'javascript',
                                                    'unit',
                                                    TestsConfig.getInstance().
                                                    getJsunitFilename()),
                                        "--port",
                                        "9876",
                                        "--browser",
                                        "firefox"],
                                        stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE)
            time.sleep(2)

            #constructing conf file depending on installed plugins and
            #coverage activation
            success = self.buildConfFile(confFile, self.coverage)
            if not (success == ""):
                return success

            #switching directory to run the tests
            os.chdir(os.path.join(self.setupDir, 'javascript', 'unit'))

            #check if server is ready
            for i in range(5):
                jsDryRun = commands.getstatusoutput(("java -jar "
                                             "%s"
                                             " --config "
                                             "%s"
                                             " --tests Fake.dryRun") %\
                                             (TestsConfig.getInstance().
                                              getJsunitFilename(),
                                              confFile))
                if jsDryRun[1].startswith("No browsers were captured"):
                    print ("Js-test-driver server has not started yet. "
                           "Attempt #%s\n") % (i+1)
                    time.sleep(5)
                else:
                    #server is ready
                    break
            else:
                return ('[ERR] Could not start js unit tests because '
                        'js-test-driver server cannot be started.\n')

            #setting tests to run
            toTest = ""
            if self.specify:
                toTest = self.specify
            else:
                toTest = "all"

            command = ("java -jar %s "
                            "--config %s "
                            "--tests %s ") % \
                            (TestsConfig.getInstance().getJsunitFilename(),
                             confFile,
                             toTest)
            if self.coverage:
                command += "--testOutput %s" % coveragePath

            #running tests
            jsTest = commands.getoutput(command)

            coverageReport = ""
            if self.coverage:
                #generate html for coverage
                genOutput = commands.getstatusoutput("genhtml -o %s %s" %
                                                    (os.path.join('..',
                                                                '..',
                                                                'report',
                                                                'jscoverage'),
                                                    os.path.join('..',
                                                                 '..',
                                                                 'report',
                                                                 'jscoverage',
                                           '%s-coverage.dat' % confFile)))

                if genOutput[1].find("genhtml") > -1:
                    coverageReport = ("[ERR] JS Unit Tests - html coverage "
                                      "generation failed, genhtml needs to be "
                                      "in your PATH. (%s)\n" % genOutput[1])
                else:
                    coverageReport = ("JS Coverage - generated in "
                                     "indicop/report/jscoverage/index.html\n")

            #delete built conf file
            os.unlink(confFile)

            #restoring directory
            os.chdir(self.setupDir)

            report = ""
            if self.specify:
                #ouputing directly in the console
                print jsTest
                report = "JS Unit Tests - Output in console\n"
            else:
                report += self.writeReport("jsunit", jsTest)
                report += ("JS Unit Tests - report in "
                          "indicop/report/jsunit.txt\n")
        except OSError, e:
            return ("[ERR] Could not start js-test-driver server - command "
                    "\"java\" needs to be in your PATH. (%s)\n" % e)
        except KeyError:
            return "[ERR] Please specify a JsunitFilename in tests.conf"

        #stopping the server
        server.kill()
        return coverageReport + report

    def buildConfFile(self, confFilePath, coverage):
        confTemplatePath = os.path.join(self.setupDir,
                                        'javascript',
                                        'unit',
                                        'confTemplate.conf')

        relativeTestsFolder = os.path.join("tests")
        absoluteTestsFolder = os.path.join(self.setupDir,
                                           "javascript",
                                           "unit",
                                           "tests")

        relativePluginsFolder = os.path.join("..", "indico", "MaKaC", "plugins")
        absolutePluginsFolder = os.path.join(self.setupDir,
                                            "..",
                                            "indico",
                                            "MaKaC",
                                            "plugins")
        try:
            #lines needed to activate coverage plugin
            coverageConf = """\nplugin:
  - name: \"coverage\"
    jar: \"plugins/%s\"
    module: \"com.google.jstestdriver.coverage.CoverageModule\"""" % \
        TestsConfig.getInstance().getJscoverageFilename()
        except KeyError:
            return "[ERR] Please, specify a JscoverageFilename in tests.conf"


        try:
            #retrieve and store the template file
            f = open(confTemplatePath)
            confTemplate = f.read()
            f.close()

            #adding tests files from Indicop folder
            for root, dirs, files in os.walk(absoluteTestsFolder):
                for name in files:
                    if name.endswith(".js"):
                        absoluteFilePath = os.path.join(root, name)
                        splitPath = absoluteFilePath.split(relativeTestsFolder)
                        relativeFilePath = relativeTestsFolder + splitPath[1]

                        confTemplate += "\n  - %s" % os.path.join(relativeFilePath)


            #adding plugins test files
            for root, dirs, files in os.walk(absolutePluginsFolder):
                for name in files:
                    if name.endswith(".js") and \
                                          root.find("/tests/javascript/unit") > 0:
                        absoluteFilePath = os.path.join(root, name)
                        splitPath = absoluteFilePath.split(relativePluginsFolder)
                        relativeFilePath = relativePluginsFolder + splitPath[1]

                        confTemplate += "\n  - %s" % os.path.join('..',
                                                                  '..',
                                                                  relativeFilePath)

            #addind coverage if necessary
            if coverage:
                confTemplate += coverageConf

            #writing the compelete configuration in a file
            confFile = open(os.path.join(self.setupDir, 'javascript', 'unit',
                                         confFilePath), 'w')
            confFile.write(confTemplate)
            confFile.close()

            return ""
        except IOError, e:
            return "[ERR] JS Unit Tests - Could not open a file. (%s)" % e

class Jslint(BaseTest):
    def run(self):
        returnString = ""
        self.startMessage("Starting jslint tests")

        #Folders which are not going to be scanned.
        #Files are going to be find recursively in the other folders
        import sets
        blackList = sets.Set(['pack', 'Loader.js', 'Common', 'i18n'])

        outputString = ""

        #checking if rhino is accessible
        statusOutput = commands.getstatusoutput("rhino -?")
        if statusOutput[1].find("rhino: not found") > -1:
            return ("[ERR] Could not start JS Source Analysis - command "
                    "\"rhino\" needs to be in your PATH. (%s)\n" % statusOutput[1])

        #constructing a list of folders to scan
        folderNames = []
        list  = os.listdir(os.path.join(self.setupDir,
                                        '..',
                                        'indico',
                                        'htdocs',
                                        'js',
                                        'indico'))
        for name in list:
            if not (name in blackList):
                folderNames.append(name)

        #Scanning Indico core
        for folderName in folderNames:
            outputString += self.walkThroughFolders(os.path.join(
                                                          self.setupDir,
                                                          '..',
                                                          'indico',
                                                          'htdocs',
                                                          'js',
                                                          'indico'),
                                                    folderName)

        #Scanning plugins js files
        outputString += self.walkThroughFolders(os.path.join(
                                                          self.setupDir,
                                                          '..',
                                                          'indico',
                                                          'MaKaC',
                                                          'plugins'))

        returnString += self.writeReport("jslint", outputString)
        return returnString + "JS Lint - report in indicop/report/jslint.txt\n"

    def walkThroughFolders(self, path, folderRestriction=''):
        returnString = ""
        for root, dirs, files in os.walk(os.path.join(self.setupDir,
                                                      path,
                                                      folderRestriction)):
            for name in files:
                if name.endswith(".js"):
                    filename = os.path.join(root, name)
                    returnString += ("\n================== Scanning %s "
                                     "==================\n") % filename
                    output = commands.getstatusoutput("rhino %s %s" %
                                                      (os.path.join(
                                                                self.setupDir,
                                                                'javascript',
                                                                'jslint',
                                                                'jslint.js'),
                                                                filename))
                    returnString += output[1]
        return returnString


class Indicop(object):
    __instance = None

    def __init__(self, jsspecify, jscoverage):
        self.dbmgr = None
        self.zeoServer = None

        #variables for jsunit
        self.jsSpecify = jsspecify
        self.jsCoverage = jscoverage

        #define the set of tests
        self.testsDict = {'unit': Unit(),
                 'functional': Functional(),
                 'pylint': Pylint(),
                 'jsunit': Jsunit(self.jsSpecify, self.jsCoverage),
                 'jslint': Jslint(),
                 'grid': Grid()}


    def main(self, specify, coverage, testsToRun):

        returnString = "\n\n=============== ~INDICOP SAYS~ ===============\n\n"

        #To not pollute the installation of Indico
        self.configureTempFolders()

        if coverage:
            Coverage.instantiate()

        #specified test can either be unit or functional.
        if specify:
            returnString += Specify(specify).run()
        else:
            for test in testsToRun:
                try:
                    returnString += self.testsDict[test].run()
                except KeyError:
                    returnString += ("[ERR] Test %s does not exist. "
                      "It has to be added in the testsDict variable\n") % test

        self.deleteTempFolders()

        return returnString

    def configureTempFolders(self):
        keyNames = ['LogDir',
                    'ArchiveDir',
                    'UploadedFilesTempDir']
        self.newValues = {}

        for key in keyNames:
            self.newValues[key] = tempfile.mkdtemp()

        Config.getInstance().updateValues(self.newValues)

    def deleteTempFolders(self):
        for k in self.newValues:
            shutil.rmtree(self.newValues[k])

    @classmethod
    def getInstance(cls, jsspecify, jscoverage):
        if cls.__instance == None:
            cls.__instance = Indicop(jsspecify, jscoverage)
        return cls.__instance
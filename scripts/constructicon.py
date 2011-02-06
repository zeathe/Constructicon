# ----------------------------------------------------------------------------
#
#   Constructicon.PY
#   (C) Zeathe 2010-2011 - zeathe@qua-axiom.com
#  
#   Overview:
#
#      Constructicon is a build wrapper/driver script to support builds
#      adhering to Constructicon standards.  The build system is designed
#      to provide for local dev builds from file or GIT Repo, localized
#      consumer builds of source (direct pull of released version tags),
#      and completely controlled official builds with publishing and
#      back-tagging into a master GIT Repo.
#
#      Constructicon does the heavy lifting around a series of ANT scripts
#      for a fully functional build infrastructure to support just about
#      any level of controlled building needs.
#
#      Constructicon has been designed to modularly reside within any
#      number of build management tools (Hudson, CruiseControl, ccNET,
#      custom scripts, or other build manager) and provide some
#      flexibility.
#
#   Structure:
#
#      ---- Constructicon ----                    ---- External Project ----
#
#      Build Tool                                 "Project Foo"
#       |                                          |
#       |-- Constructicon.py           |------>>   |-- Constructicon Project
#            |                         |               ANT build.xml
#            |-- Constructicon         |                |
#                Master ANT    >>------|                |-- Project Foo ANT
#                build.xml                                  XMLs
#                                                            |
#                                                            |-- Custom Tasks
#
#
#   License:
#
#      SCOPE OF LICENSE
#      Constructicon.py, the build.xml packaged with Constructicon.py, the
#      file system structure of Constructicon's BuildSystems directory, and
#      the root build.xml file to be present in external projects (provided
#      by Constructicon) all fall within the scope of the Constructicon
#      license.
#
#      Full list of files:
#         ./BuildSystems/scripts/constructicon.py
#         ./BuildSystems/scripts/build.xml
#
#         ./BuildSystems/python/python.mac.sh
#         ./BuildSystems/python/python.linux.sh
#         ./BuildSystems/python/python.win32.cmd
#
#         ./Projects/HelloWorld/v0.1/build.xml
#
#         ./Projects/HelloWorld/v0.1/... (all other recursive files)
#
#      3rd Party tools (Python, Python Libraries, MinGW, etc) are all
#      *NOT* owned/controlled by me and are subject to their own respective
#      licenses.  I apologize to these owners now for any violation of
#      their re-distribution clauses -- and will aim to correct this in
#      ways that doesn't compromise the stand-alone modularity attempted
#      to be achieved by Constructicon.
#
#      This license excludes all third-party external project code that
#      would exist past the constructicon project ANT build.xml file.  This
#      license releases all claims of interest to to external project code
#      in which a user would use constructicon to build, as defined as
#      being further down-stream from the constructicon project ANT build.xml
#      file.
#
# Copyright 2011 Zeathe <zeathe@qua-axiom.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ----------------------------------------------------------------------------
import logging
import logging.handlers
import optparse
import os
import platform
import sys
import uuid
from git import *

class cmdLineOptions:
	"""A cmdLineOptions object holds all of the run-time options for Constructicon derrived from ARGV"""
	def __init__(self):

		###
		### generate and parse the command-line arguments
		###
		self.cmdlineparser = optparse.OptionParser(usage="usage: %prog [options] arg", version="%prog asdfadsf")
		self.cmdlineparser.set_defaults(buildtype="local")

		self.cmdlineparser.add_option("--explain", type="string", dest="helper", help="Pass another switch to get detailed info on that switch")
		self.cmdlineparser.add_option("-v", "--verbose", action="count", dest="verbosity", help="be verbose.  use multiple times to be more verbose.")
		self.cmdlineparser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="suppress all output but errors.")

		self.cmdlineparser.add_option("--debug", action="store_true", dest="debug", help="enable debugging output")

		self.cmdlineparser.add_option("-b", "--buildtype", dest="buildtype", type="string", help="""specify the build type for the constructicon build.  build types include: 
local (default) - builds local build from central code pulled from a defined repo... 
dev - builds local dev-level builds with no external syncing... 
official - builds an official build updating tags and versions with the defined repo...""")
		self.cmdlineparser.add_option("-r", "--repopath", dest="repopath", type="string", help="repo path to build from... ie: git://www.github.org/project/foo/")
		self.cmdlineparser.add_option("-f", "--filepath", dest="filepath", type="string", help="file path to buid from... ie: /path/to/sources.  This is mutually exclusive to RepoPath")
		self.cmdlineparser.add_option("--synclabel", dest="synclabel", type="string", help="sync repopath to given sha, tag, or branch (at head)")

		self.cmdlineparser.add_option("--branch", dest="branch", type="string", help="GIT branch to sync from within the repository")

		self.cmdlineparser.add_option("--workspace", dest="workspace", type="string", help="output path for build.... otherwise, a mount volume is used.")

		self.cmdlineparser.add_option("--publishpath", dest="publishpath", type="string", help="publish path for deliverable bits... useful generally only for official builds.  This results in files generated in the directory structure as follows: ##PUBLISH PATH##/{FAILED|SUCCESSFUL}BUILDS/##BUILDTYPE##/##REPOPATH|FILEPATH##/##BRANCH##/##SYNCLABEL##")

		# internal, constructicon has sync'd himself to latest and run himself again...
		self.cmdlineparser.add_option("--skipselfsync", action="store_true", dest="selfsynced", help=optparse.SUPPRESS_HELP)

		# internal, dev-helper spew info option...
		self.cmdlineparser.add_option("--spewie", action="store_true", dest="spewie", help=optparse.SUPPRESS_HELP)

		# secret, force ReDeux of old label for official build
		self.cmdlineparser.add_option("--forcenewlabel", action="store_true", dest="forcenewlabel", help=optparse.SUPPRESS_HELP)

		(self.cmdOpts, self.args) = self.cmdlineparser.parse_args()

	def sanityCheck(self):

		# Perform several sanity checks for the command-line variables provided
			#               1         2         3         4         5         6         7         8
			#      12345678901234567890123456789012345678901234567890123456789012345678901234567890
		if ( self.cmdOpts.quiet != None and 0 < self.cmdOpts.verbosity):
			print("ERROR: --quiet specified while --verbose was also specified, this is just silly")
			print("")
			print("...Try using --help")
			print("")
			raise

		if ( None == self.cmdOpts.repopath and None == self.cmdOpts.filepath ):
			print("ERROR: --REPOPATH or --FILEPATH is a required flag")
			print("")
			print("...Try using --help")
			print("")
			raise

		if ( None != self.cmdOpts.repopath and None != self.cmdOpts.filepath ):
			print("ERROR: Only Specify --REPOPATH or --FILEPATH but not both")
			print("")
			print("...Try using --help")
			print("")
			raise

		if ( None != self.cmdOpts.synclabel and None != self.cmdOpts.filepath ):
			print("ERROR: You don't get Source Control Labels on --FILEPATH")
			print("")
			print("...Try using --help")
			print("")
			raise

		if ( None == self.cmdOpts.buildtype ):
			print("ERROR: --BUILDTYPE is a required flag")
			print("")
			print("...Try using --help")
			print("")
			raise

		# Official Build Requirements
		if ( str.lower("official") == self.cmdOpts.buildtype):
			if (None == self.cmdOpts.publishpath):
				print("ERROR: --PUBLISHPATH required when --BUILDTYPE is 'OFFICIAL'")
				print("")
				print("...Try using --help")
				print("")
				raise

			if (None != self.cmdOpts.filepath):
				print("ERROR: Cannot use --FILEPATH when --BUILDTYPE is 'OFFICIAL'")
				print("       --FILEPATH is for --BUILDTYPE of 'DEV' only")
				print("")
				print("...Try using --help")
				print("")
				raise

		# Local Build Requirements
		if ( str.lower("local") == self.cmdOpts.buildtype):
			if (None != self.cmdOpts.filepath):
				print("ERROR: Cannot use --FILEPATH when --BUILDTYPE is 'LOCAL'")
				print("       --FILEPATH is for --BUILDTYPE of 'DEV' only")
				print("")
				print("...Try using --help")
				print("")
				raise

		if ( str.lower("local") != self.cmdOpts.buildtype and str.lower("dev") != self.cmdOpts.buildtype and str.lower("official") != self.cmdOpts.buildtype ):
			print("ERROR: --BUILDTYPE must be either: local, dev, or official")
			print("   you specified '" + str(self.cmdOpts.buildtype) + "'")
			print("")
			print("...Try using --help")
			print("")
			raise

		#if ( str.lower("repopath") == self.cmdOpts.helper ):
		#	print("--repopath    The path of the repo man")
		#	exit(255)

	def getSpewie(self):
		return self.cmdOpts.spewie

	def getForceNewLabel(self):
		return self.cmdOpts.forcenewlabel

	def getVerbosity(self):
		if (True is self.cmdOpts.quiet):
			retVal = -1
		elif (None == self.cmdOpts.verbosity):
			retVal = 0
		else:
			retVal = self.cmdOpts.verbosity

		return retVal

	# Returns a raw CmdLineObj -- this is more for debugging than for using
	def getCmdLineObj(self):
		return self.cmdOpts

	# Returns a dictionary of options -- this is the general practice of usage
	def getOptDict(self):
		cmdLineOptDict = { 
				"verbosity": self.cmdOpts.verbosity,
				"quiet": self.cmdOpts.quiet,
				"debug": self.cmdOpts.debug,
				"buildtype": self.cmdOpts.buildtype,
				"repopath": self.cmdOpts.repopath,
				"filepath": self.cmdOpts.filepath,
				"synclabel": self.cmdOpts.synclabel,
				"branch": self.cmdOpts.branch,
				"workspace": self.cmdOpts.workspace,
				"publishpath": self.cmdOpts.publishpath}

		return cmdLineOptDict

	def getSkipSelfSync(self):
		return self.cmdOpts.selfsynced

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print " Following Command Line Variables are set..."
		print "    verbosity           : " + str(self.cmdOpts.verbosity)
		print "    quiet               : " + str(self.cmdOpts.quiet)
		print "    debug               : " + str(self.cmdOpts.debug)
		print "    buildtype           : " + str(self.cmdOpts.buildtype)
		print "    repopath            : " + str(self.cmdOpts.repopath)
		print "    filepath            : " + str(self.cmdOpts.filepath)
		print "    synclabel           : " + str(self.cmdOpts.synclabel)
		print "    branch              : " + str(self.cmdOpts.branch)
		print "    workspace           : " + str(self.cmdOpts.workspace)
		print "    publishpath         : " + str(self.cmdOpts.publishpath)
		print " Undoc Variables are set..."
		print "    selfsynced          : " + str(self.cmdOpts.selfsynced)
		print "    spewie              : " + str(self.cmdOpts.spewie)
		print "******************************************************************************"


class messageHandler:
	def __init__(self, arg1, arg2):
		try:
			self.sourceApp = arg1
			self.sourceVerbosity = arg2

			if (self.sourceVerbosity > 4):
				self.verbosity = 4
			else:
				self.verbosity = self.sourceVerbosity

			self.LevelValues = {
					4: "debug",
					3: "info",
					2: "warning",
					1: "error",
					0: "critical",
					-1: "quiet",
					}
			self.defLevel = self.LevelValues.get(self.verbosity, "quiet")

			# Logger Configurations
			self.msgLogger = logging.getLogger(self.sourceApp)

			self.msgFormat = "[%(asctime)s] [%(levelname)-8s] [%(name)-20s] %(message)s"

			LEVELS = {	'debug'		: logging.DEBUG,
					'info'		: logging.INFO,
					'warning'	: logging.WARNING,
					'error'		: logging.ERROR,
					'critical'	: logging.CRITICAL,
					'quiet'		: logging.NOTSET }

			self.msgLevel = LEVELS.get(str.lower(self.defLevel), logging.NOTSET)

			logging.basicConfig(level=self.msgLevel,format=self.msgFormat)

			self.msgLogger.debug("Logger Initialized")
		except:
			print("Failed to stand initialize Logger")
			raise

	# Default Emitter, and other emitters
	def emit(self, record):
		self.msgLogger.info(record)

	def debug(self, record):
		self.msgLogger.debug(record)

	def info(self, record):
		self.msgLogger.info(record)

	def warning(self, record):
		self.msgLogger.warning(record)

	def error(self, record):
		self.msgLogger.error(record)

	def critical(self, record):
		self.msgLogger.critical(record)

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print "loggerSource                     : " + self.sourceApp
		print "msgFormat                        : " + self.msgFormat
		self.msgLogger.debug("Test - debug messgage")
		self.msgLogger.info("Test - info message")
		self.msgLogger.warning("Test - warning message")
		self.msgLogger.error("Test - error message")
		self.msgLogger.critical("Test - critical message")
		print "******************************************************************************"

class detectOS:
	def __init__(self, verbosityLevel):
		try:
			self.msgLogger = messageHandler("detectOS Module", verbosityLevel)
		except:
			print("Failed to initialize internal logger")
			raise

		try:
			self.msgLogger.debug("initializing detectedOS variable for OS Token")
			self.detectedOS = None

			self.msgLogger.debug("Generating a uName Object")
			self.uname = os.uname()
		
			self.msgLogger.debug("Pull out of the uName tuple (sysname, nodename, release, version, machine)")
			self.sysname = self.uname[0]
			self.nodename = self.uname[1]
			self.release = self.uname[2]
			self.version = self.uname[3]
			self.machine = self.uname[4]
			
			self.msgLogger.debug("Pull other Python variables for OS detection...")
			self.name = os.name
			self.platform = sys.platform
			self.system = platform.system()

		except:
			self.msgLogger.error("Failed to pull Python variables for OS detection")
			raise

		try:
			self.msgLogger.debug("Executing runDetection()")
			self.runDetection()
		except:
			self.msgLogger.error("Failed to execut runDetection()")
			raise

	def runDetection(self):
		### OS-Detection function
		# 
		#
		if ("posix" == str.lower(self.name) and "darwin" == str.lower(self.platform) and "darwin" == str.lower(self.system)):
			self.msgLogger.debug("Discovered MacOSX")
			self.detectedOS = "MacOSX"

		if ("posix" == str.lower(self.name) and "linux2" == str.lower(self.platform) and "linux" == str.lower(self.system)):
			self.msgLogger.debug("Discovered Linux")
			self.detectedOS = "Linux"

		# TO-DO: Need to identify the strings present on a Windows Python install
		#if ("posix" == str.lower(self.name) and "linux2" == str.lower(self.platform) and "linux" == str.lower(self.system)):
		#	self.msgLogger.debug("Discovered Windows")
		#	self.detectedOS = "Windows"

	def getOS(self):
		self.msgLogger.debug("returning detectedOS via getOS()")
		return str.lower(self.detectedOS)

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print " detectedOS                 : " + self.detectedOS
		print " Derived from os.uname..."
		print "    sysname                 : " + self.sysname
		print "    nodename                : " + self.nodename
		print "    release                 : " + self.release
		print "    version                 : " + self.version
		print "    machine                 : " + self.machine
		print " Other Values..."
		print "    os.name                 : " + self.name
		print "    sys.platform            : " + self.platform
		print "    platform.system()       : " + self.system
		self.msgLogger.debug("Test - debug messgage")
		self.msgLogger.info("Test - info message")
		self.msgLogger.warning("Test - warning message")
		self.msgLogger.error("Test - error message")
		self.msgLogger.critical("Test - critical message")
		print "******************************************************************************"


class builderObject:
	def __init__(self, verbosityLevel):
		try:
			self.msgLogger = messageHandler("builderObject", verbosityLevel)
		except:
			print("Failed to initialize internal logger")
			raise

		try:
			self.msgLogger.debug("Initializing Build Generics variables...")
			# Build Generics
			self.buildtype = None
			self.repopath = None
			self.filepath = None
			self.synclabel = None
			self.branch = None
			self.workspace = None
			self.publishpath = None

			self.msgLogger.debug("Initializing Version Info variables...")
			# Version Info
			self.majorversion = None
			self.minorversion = None
			self.maintenanceversion = None
			self.buildid = None

			self.msgLogger.debug("Initializing Internal BuildTrack variables...")
			# Error Catch
			self.buildfailure = False
		except:
			self.msgLogger.error("Cannot initialize base object variables")
			raise


	# Retrieve Values
	def getBuildType(self):
		return self.buildtype

	def getRepoPath(self):
		return self.repopath

	def getFilePath(self):
		return self.filepath

	def getSyncLabel(self):
		return self.synclabel

	def getBranch(self):
		return self.branch

	def getWorkspace(self):
		return self.workspace

	def getPublishPath(self):
		return self.publishpath

	def getMajorVersion(self):
		return self.majorversion

	def getMinorVersion(self):
		return self.minorversion

	def getMaintVersion(self):
		return self.maintenanceversion

	def getBuildID(self):
		return self.buildid

	def getBuildFailed(self):
		return self.buildfailure


	# Set Values
	def setBuildType(self, value):
		self.msgLogger.debug("Setting buildtype via setBuildType() as " + str(value))
		self.buildtype = value

	def setRepoPath(self, value):
		self.msgLogger.debug("Setting repopath via setRepoPath() as " + str(value))
		self.repopath = value

	def setFilePath(self, value):
		self.msgLogger.debug("Setting filepath via setFilePath() as " + str(value))
		self.filepath = value

	def setSyncLabel(self, value):
		self.msgLogger.debug("Setting synclabel via setSyncLabel() as " + str(value))
		self.synclabel = value

	def setBranch(self, value):
		self.msgLogger.debug("Setting branch via setBranch() as " + str(value))
		self.branch = value

	def setWorkspace(self, value):
		self.msgLogger.debug("Setting workspace via setWorkspace() as " + str(value))
		self.workspace = value

	def setPublishPath(self, value):
		self.msgLogger.debug("Setting publishpath via setPublishPath() as " + str(value))
		self.publishpath = value

	def setMajorVersion(self, value):
		self.msgLogger.debug("Setting majorversion via setMajorVersion() as " + str(value))
		self.majorversion = value

	def setMinorVersion(self, value):
		self.msgLogger.debug("Setting minorversion via setMinorVersion() as " + str(value))
		self.minorversion = value

	def setMaintVersion(self, value):
		self.msgLogger.debug("Setting maintenanceversion via setMaintVersion() as " + str(value))
		self.maintenanceversion = value

	def setBuildID(self, value):
		self.msgLogger.debug("Setting buildid via setBuildID() as " + str(value))
		self.buildid = value

	def setBuildFailed(self):
		self.buildfailure = True


	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print " Build Generics..."
		print "    BuildType                    : " + str(self.buildtype)
		print "    RepoPath                     : " + str(self.repopath)
		print "    FilePath                     : " + str(self.filepath)
		print "    SyncLabel                    : " + str(self.synclabel)
		print "    Branch                       : " + str(self.branch)
		print "    Workspace                    : " + str(self.workspace)
		print "    PublishPath                  : " + str(self.publishpath)
		print " Build Versioning Info..."
		print "    Major Version                : " + str(self.majorversion)
		print "    Minor Version                : " + str(self.minorversion)
		print "    Maintenance Version          : " + str(self.maintenanceversion)
		print "    Build ID                     : " + str(self.buildid)
		print "Internal BuildTrack variables..."
		print "    Build Failure                : " + str(self.buildfailure)
		self.msgLogger.debug("Test - debug messgage")
		self.msgLogger.info("Test - info message")
		self.msgLogger.warning("Test - warning message")
		self.msgLogger.error("Test - error message")
		self.msgLogger.critical("Test - critical message")
		print "******************************************************************************"



class localBSR:
	def __init__(self, verbosityLevel, buildObject):
		try:
			self.msgLogger = messageHandler("localBSR", verbosityLevel)
		except:
			print("Failed to initialize internal logger")
			raise


		try:	
			self.workspace = buildObject.getWorkspace()
		except:
			self.msgLogger.error("Unable to retreive workspace from buildObject.getWorkspace()")
			raise

		# if this isn't specified, and the BuildObject doesn't contain the workspace value,
		# the BSR will have to assume the TMP directory
		if (None == self.workspace):
			self.msgLogger.debug("Starting to look for temporary directory environment variables")

			try:
				if (os.environ['TEMP']):
					self.msgLogger.debug("found TEMP os.environ variable")
					self.msgLogger.debug("Setting local object workspace")
					self.workspace = str(os.environ["TEMP"])
					self.msgLogger.debug("exporting object workspace to buildObject")
					buildObject.setWorkspace( os.environ["TEMP"] )
			except:
				pass

			try:	
				if (os.environ['TMPDIR']):
					self.msgLogger.debug("found TMPDIR os.environ variable")
					self.msgLogger.debug("Setting local object workspace")
					self.workspace = os.environ['TMPDIR']
					self.msgLogger.debug("exporting object workspace to buildObject")
					buildObject.setWorkspace( os.environ['TMPDIR'] )
			except:
				pass
			if (None == self.workspace):
				self.msgLogger.error("We didn't find a working directory... We cannot proceed")
				raise

		# Get some pathing information
		self.__pathname, self.__scriptname = os.path.split(sys.argv[0])

		self.pathUUID = str(uuid.uuid4())

		self.buildSystemPath = os.path.abspath( self.__pathname + ".." + os.sep )
		self.projectPath = self.workspace + os.sep + self.pathUUID + os.sep + "Project"
		self.outputPath = self.workspace + os.sep + self.pathUUID + os.sep + "OR" + os.sep + "v" + str(buildObject.getMajorVersion()) + "." + str(buildObject.getMinorVersion()) + "." + str(buildObject.getMaintVersion()) + "." + str(buildObject.getBuildID())

	def getWorkspace(self):
		return self.workspace

	def getPathUUID(self):
		return self.pathUUID

	def getBuildSystemPath(self):
		return self.buildSystemPath

	def getProjectPath(self):
		return self.projectPath

	def getOutputPath(self):
		return self.outputPath

	def getLinkSrc(self):
		pass

	def resetBuildSystemPath(self):
		self.buildSystemPath = self.workspace + os.sep + self.pathUUID + os.sep + "BuildSystem"

	def resetOutputPath(self):
		self.outputPath = self.workspace + os.sep + self.pathUUID + os.sep + "OR" + os.sep + "v" + str(buildObject.getMajorVersion()) + "." + str(buildObject.getMinorVersion()) + "." + str(buildObject.getMaintVersion()) + "." + str(buildObject.getBuildID())

	### os-independent mount point maker
	# intake: source location of the link and destination of where to make the link
	# returns true if successful, false if not successful
	# 
	def makemountpoint(self, linksrc, linkdest):
		pass

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print "    Workspace		: " + str(self.workspace)
		try:
			print "    os.environ[temp]    : " + str(os.environ['TEMP'])
		except:
			pass
		try:
			print "    os.environ[tmpdir]  : " + str(os.environ['TMPDIR'])
		except:
			pass
		try:
			print "    os.environ[tmp]     : " + str(os.environ['TMP'])
		except:
			pass
		print "    os.environ[temp]    : " 
		print "    buildSystemPath     : " + str(self.buildSystemPath)
		print "    projectPath         : " + str(self.projectPath)
		print "    outputPath          : " + str(self.outputPath)
		print "******************************************************************************"

class gitObject:
	def __init__(self, verbosityLevel):
		try:
			self.msgLogger = messageHandler("gitObject", verbosityLevel)
		except:
			print("Failed to initialize internal logger")

		self.remoteRepoPath = None
		self.localRepoPath = None
		self.repoBranch = None
		self.repoSyncLabel = None 
		self.__localRepoHandle = None
		self.__remoteRepoHandle = None

	def getRemoteRepoPath(self):
		return self.remoteRepoPath

	def getLocalRepoPath(self):
		return self.localRepoPath

	def getRepoBranch(self):
		return self.repoBranch

	def getRepoSyncLabel(self):
		return self.repoSyncLabel

	def setRemoteRepoPath(self, value):
		self.msgLogger.debug("Setting RemoteRepoPath via setRemoteRepoPath() as " + str(value))
		self.remoteRepoPath = value

	def setLocalRepoPath(self, value):
		self.msgLogger.debug("Setting RemoteRepoPath via setLocalRepoPath() as " + str(value))
		self.localRepoPath = value

	def setRepoBranch(self, value):
		self.msgLogger.debug("Setting RemoteRepoPath via setRepoBranch() as " + str(value))
		self.repoBranch = value

	def setRepoSyncLabel(self, value):
		self.msgLogger.debug("Setting RemoteRepoPath via setRepoSyncLabel() as " + str(value))
		self.repoSyncLabel = value

	def initRepo(self):
		try:
			self.msgLogger.debug("Initializing Local RepoPath via initRepo() as " + str(self.localRepoPath))
			self.__localRepoHandle = Repo.init(self.localRepoPath, bare=False)
		except:
			self.msgLogger.error("Failed to initialize local RepoPath via initRepo()")
			raise
	
	def initRemoteRepo(self):
		try:
			self.msgLogger.debug("Initializing Remote RepoPath via initRemoteRepo() as " + str(self.remoteRepoPath))
			self.__remoteRepoHandle = self.__localRepoHandle.create_remote('origin', str(self.remoteRepoPath))
		except:
			self.msgLogger.error("Failed to initialize remote Repot Path via initRemoteRepot()")
			raise

	def remoteFetch(self):
		try:
			self.msgLogger.debug("Running GIT FETCH on remote repo")
			self.__remoteRepoHandle.fetch()
		except:
			self.msgLogger.error("Failed to execute GIT FETCH on remote repo via remoteFetch()")
			raise

	def checkoutBranch(self, branchname):
		try:
			# byHand.git.checkout('remotes/origin/v2.0')
			self.msgLogger.debug("Running GIT CHECKOUT on remote repo and branch")
			self.__localRepoHandle.git.checkout("remotes/origin/" + branchname)
		except:
			self.msgLogger.error("Failed to check out branch " + branchname)
			raise


	def checkoutTag(self, tag):
		try:
			# byHand.git.checkout('v2.0.0.3')
			self.msgLogger.debug("Running GIT CHECKOUT on remote repo and branch")
			self.__localRepoHandle.git.checkout(tag)
		except:
			self.msgLogger.error("Failed to check out branch " + tag)
			raise

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print "    Remote Repo Path    : " + str(self.remoteRepoPath)
		print "    Local Repo Path     : " + str(self.localRepoPath)
		print "    Repo Branch         : " + str(self.repoBranch)
		print "    Sync Label          : " + str(self.repoSyncLabel)
		print "******************************************************************************"




def main():
	# ----------------------------------------------------------------------
	# Stand Up Command-Line Parsing and initial settings
	# ----------------------------------------------------------------------

	try:
		cmdOpts = cmdLineOptions()
		if ( cmdOpts.getSpewie() ):
			cmdOpts.testMe()

		cmdOptsDict = cmdOpts.getOptDict()
	except:
		if ( str.lower(sys.argv[1]) == "--help" or str.lower(sys.argv[1]) == "-h" or str.lower(sys.argv[1]) == "--h" or str.lower(sys.argv[1]) == "-help" ):
			pass
		else:
			print("")
			print("")
			print("")
			print("ERROR: Failed to bootstrap the CommandLine parsing process")
			print("")
			exit(255)


	try:
		cmdOpts.sanityCheck()
	except:
		exit(1)


	# ----------------------------------------------------------------------
	# Stand Up Logger
	# ----------------------------------------------------------------------

	#                         Caller Instance      , CmdLine Obj
	cLogger = messageHandler("Constructicon Master", cmdOpts.getVerbosity())
	if ( cmdOpts.getSpewie() ):
		cLogger.testMe()

	# ----------------------------------------------------------------------
	# Debug Initialization Output
	# ----------------------------------------------------------------------

	cLogger.debug("Message Handler Initialized")
	cLogger.debug("cmdLineOptions() previously established before Message Handler Initialized...")
	cLogger.debug("""cmdOptsDict.get("verbosity") is   : """ + str(cmdOptsDict.get("verbosity")))
	cLogger.debug("""cmdOptsDict.get("quiet") is       : """ + str(cmdOptsDict.get("quiet")))
	cLogger.debug("""cmdOptsDict.get("debug") is       : """ + str(cmdOptsDict.get("debug")))
	cLogger.debug("""cmdOptsDict.get("buildtype") is   : """ + str(cmdOptsDict.get("buildtype")))
	cLogger.debug("""cmdOptsDict.get("repopath") is    : """ + str(cmdOptsDict.get("repopath")))
	cLogger.debug("""cmdOptsDict.get("filepath") is    : """ + str(cmdOptsDict.get("filepath")))
	cLogger.debug("""cmdOptsDict.get("synclabel") is   : """ + str(cmdOptsDict.get("synclabel")))
	cLogger.debug("""cmdOptsDict.get("branch") is      : """ + str(cmdOptsDict.get("branch")))
	cLogger.debug("""cmdOptsDict.get("workspace") is   : """ + str(cmdOptsDict.get("workspace")))
	cLogger.debug("""cmdOptsDict.get("publishpath") is : """ + str(cmdOptsDict.get("publishpath")))



	#cLogger.debug("START -- detectOS()")
	#testedOS = detectOS(cmdOpts.getVerbosity())
	#if ( cmdOpts.getSpewie() ):
	#	testedOS.testMe()
	#cLogger.debug("END -- detectOS()")


	# ----------------------------------------------------------------------
	# Check if SelfSync needs to be performed
	# ----------------------------------------------------------------------

	if not ( cmdOpts.getSkipSelfSync() ):

		cLogger.debug("START -- Syncing Build System...")

		###
		### Pull in BuildSystem
		###
		try:
			cLogger.debug("Creating Self-Sync BuildObject")
			selfsyncB = builderObject(cmdOpts.getVerbosity())
		except:
			cLogger.critical("Failed to create a Self-Sync BuildObject")
			exit(1)

		cLogger.debug("Pushing Command-Line specified Workspace into selfsyncB")
		selfsyncB.setWorkspace(cmdOptsDict.get("workspace"))

		try:
			cLogger.debug("Creating Self-Sync BSRObject")
			selfsyncBSR = localBSR(cmdOpts.getVerbosity(), selfsyncB)
			cLogger.debug("Resetting BuildSystem Path from BSR Default")
			selfsyncBSR.resetBuildSystemPath()
		except:
			cLogger.critical("Failed to Create Self-Sync BSRObject")
			exit(1)

		try:
			cLogger.debug("Creating Self-Sync GIT Object")
			selfsyncGIT = gitObject(cmdOptsDict.get("verbosity"))
		except:
			cLogger.critical("Failed to Create Self-Sync GIT Object")
			exit(1)

		try:
			cLogger.debug("Creating Build System Path")
			os.makedirs(selfsyncBSR.getBuildSystemPath())	
		except:
			cLogger.critical("Failed to Create Build System Path " + str(selfsyncBSR.getBuildSystemPath()))
			exit(1)

		cLogger.debug("Setting RemoteRepoPath")
		selfsyncGIT.setRemoteRepoPath("git://github.com/zeathe/Constructicon.git")
		cLogger.debug("Setting LocalRepoPath")
		selfsyncGIT.setLocalRepoPath(selfsyncBSR.getBuildSystemPath())
		cLogger.debug("Setting RepoBranch")
		selfsyncGIT.setRepoBranch("master")

		try:
			cLogger.debug("selfsyncGIT Init Local Repo")
			selfsyncGIT.initRepo()
		except:
			exit(1)

		try:
			cLogger.debug("selfsyncGIT Init Remote Repo")
			selfsyncGIT.initRemoteRepo()
		except:
			exit(1)

		try:
			cLogger.debug("selfsyncGIT Remote Fetch")
			selfsyncGIT.remoteFetch()
		except:
			exit(1)

		try:
			cLogger.debug("selfsyncGIT checkout master")
			selfsyncGIT.checkoutBranch("master")
		except:
			exit(1)




		# Check for current build system
			# Verify Manifest of current build system
			# To-Do: Write Manifest Check Code

		# Pull in BuildSystem
			# Verify Manifest of received build system

		# ArgV is ['constructicon.py', '--repopath', 'git@github.com:zeathe/Constructicon-TestDevDepot.git', '--buildtype', 'local', '--workspace=/tmp/contest']
		recycleCMDLine = ""

		for arg in sys.argv[1:]:
			recycleCMDLine += arg + " "

		#cLogger.critical("CommandLine Would Be: blah blah constructicon.py " + recycleCMDLine + " --skipselfsync")
		# selfsyncBSR.getBuildSystemPath()
		print selfsyncBSR.getBuildSystemPath() + os.sep + "python" + os.sep + "python.mac.sh" + " " + selfsyncBSR.getBuildSystemPath() + os.sep + "scripts" + os.sep + "constructicon.py " + str(sys.argv) + " --skipselfsync"
		#exit(RetVal)
		exit(69)


		# Re-Execute Constructicon (call --skipselfsync)

		# TO-DO: Fix Self-Syncing
	else:

		# ----------------------------------------------------------------------
		# Create Builder Object and set parameters
		# ----------------------------------------------------------------------


		cLogger.debug("START -- Instantiating builderObject b")

		try:
			cLogger.debug("Building b with builderObject()")
			b = builderObject(cmdOpts.getVerbosity())
		except:
			cLogger.critical("Cannot create builderObject b")
			exit(1)


		cLogger.debug("Pushing Command-Line specified BuildType into BuildObject b")
		try:
			b.setBuildType(cmdOptsDict.get("buildtype")) # This is a required variable from the command-line
		except:
			cLogger.critical("Failed to assign BuildType to BuildObject b")
			exit(1)
		

		if not ( None == cmdOptsDict.get("repopath") ):
			cLogger.debug("Pushing Command-Line specified RepoPath into BuildObject b")
			try:
				b.setRepoPath(cmdOptsDict.get("repopath")) # This is a required variable from the command-line
			except:
				cLogger.critical("Failed to assign RepoPath to BuildObject b")
				exit(1)

		if not ( None == cmdOptsDict.get("filepath") ):
			cLogger.debug("Pushing Command-Line specified FilePath into BuildObject b")
			try:
				b.setFilePath(cmdOptsDict.get("filepath")) # This is a required variable from the command-line
			except:
				cLogger.critical("Failed to assign FilePath to BuildObject b")
				exit(1)

		cLogger.debug("Checking if SyncLabel has been specified on Command-Line")
		if ( None != cmdOptsDict.get("synclabel") ):
			cLogger.debug("Pushing Command-Line specified SyncLabel into BuildObject b")
			b.setSyncLabel(cmdOptsDict.get("synclabel"))
		else:
			cLogger.debug("SyncLabel doesn't appear to be specified")

		if ( None != cmdOptsDict.get("branch") ):
			cLogger.debug("Pushing Command-Line specified Branch into BuildObject b")
			b.setBranch(cmdOptsDict.get("branch"))
		else:
			cLogger.debug("Setting Branch default to Master since Branch not specified on Command-Line")
			b.setBranch("Master")

		if ( None != cmdOptsDict.get("workspace") ):
			cLogger.debug("Pushing Command-Line specified Workspace into BuildObject b")
			b.setWorkspace(cmdOptsDict.get("workspace"))
		else:
			cLogger.debug("Workspace doesn't appear to be specified... BSR will assume TMP")

		if ( None != cmdOptsDict.get("publishpath") ):
			cLogger.debug("Pushing Command-Line specified PublishPath into BuildObject b")
			b.setPublishPath(cmdOptsDict.get("publishpath"))
		else:
			cLogger.debug("PublishPath doesn't appear to be specified")


					

		if ( cmdOpts.getSpewie() ):
			b.testMe()

		cLogger.debug("END -- builderObject b Instantiation")

		# ----------------------------------------------------------------------
		# Set up Build System Root (BSR)
		# ----------------------------------------------------------------------

		if not (b.getBuildFailed()):

			cLogger.debug("START -- building up BSR...")
			try:
				BSR = localBSR(cmdOptsDict.get("verbosity"), b)
			except:
				cLogger.critical("Failed to create BSR LocalBSR object...")
				exit(1)

			if ( cmdOpts.getSpewie() ):
				BSR.testMe()


			### Set up Workspace (either defined workspace or standard mountpoint)

			# Variables that we already have in localBSR Object
			# localBSRObj.getWorkspace		=	Workspace Root Location
			# localBRSObj.getBuildSystemPath	=	Build System Path 
			#						(where Constructicon would be sync'd and second-Run)
			# localBSRObj.getProjectPath		=	Source Code Sync Point (for local and offical builds)
			# localBSRObj.getOutputPath		-	Objects/BuildLogs/Deliverables "BSLandingZone"

			# Make mount points
			#cLogger.debug("Creating BSR Build System Path : " + str(BSR.getBuildSystemPath()))
			#os.makedirs(BSR.getBuildSystemPath())
			cLogger.debug("Creating BSR Output Path       : " + str(BSR.getOutputPath()))
			os.makedirs(BSR.getOutputPath())

			# Prep directory structure

			# IF BuildType IS dev.... and RepoPath is file share.... link into ProjectPath
			if ( None != b.getFilePath() ):
				cLogger.debug("Linking FilePath " + str(b.getFilePath()) + " to ProjectPath " + str(BSR.getProjectPath()))
				try:
					os.link(b.getFilePath(), BSR.getProjectPath())
				except:
					cLogger.critical("Failed to Link FilePath " + str(b.getFilePath()) + " to ProjectPath " + str(BSR.getProjectPath()))
					exit(1)
			else:
				if ( None != b.getRepoPath() ):
					cLogger.debug("Creating BSR Project Path      : " + str(BSR.getProjectPath()))
					os.makedirs(BSR.getProjectPath())
				else:
					cLogger.critical("Major Problem.... No FilePath or RepoPath. We fell into a trap we should never hit...")
					exit(1)


			cLogger.debug("END -- BSR built up...")


		# ----------------------------------------------------------------------
		# Verify source, version, report back for official builds
		# ----------------------------------------------------------------------

		if not (b.getBuildFailed()):

			cLogger.debug("START -- Verifying Sources, Versions, and Labels...")

			### Get Version
			if ( None == b.getFilePath() and None != b.getRepoPath() ):

				### Verify Remote Repo
				
				# Verify RepoPath is a valid GIT object

				# Get ourselves a working local repo of the remote

				# Create Local Repo Space to work in
				try:
					cLogger.debug("Initializing gitHandle via gitObject()")
					gitHandle = gitObject(cmdOptsDict.get("verbosity"))
				except:
					cLogger.critical("Failed to create gitObject")
					b.setBuildFailed()

				cLogger.debug("Configuring gitHandle via gitHandle.setXXX(): Setting Remote Repo Path")
				gitHandle.setRemoteRepoPath(b.getRepoPath())
				cLogger.debug("Configuring gitHandle via gitHandle.setXXX(): Setting Local Repo Path")
				gitHandle.setLocalRepoPath(BSR.getProjectPath())
				cLogger.debug("Configuring gitHandle via gitHandle.setXXX(): Setting Repo Branch")
				gitHandle.setRepoBranch(b.getBranch())
				cLogger.debug("Configuring gitHandle via gitHandle.setXXX(): Setting Repo Sync Label")
				gitHandle.setRepoSyncLabel(b.getSyncLabel())

				if ( cmdOpts.getSpewie() ):
					gitHandle.testMe()

				# $ mkdir /path/to/local/repo
				# $ pushd /path/to/local/repo
				# $ git init
				try:
					cLogger.debug("Calling gitHandle.initRepo()")
					gitHandle.initRepo()
				except:
					cLogger.critical("Failed to Initialize Local Repo")
					b.setBuildFailed()


				# $ git remote add origin b.getRemoteRepoPath()
				try:
					cLogger.debug("Calling gitHandle.initRemoteRepo()")
					gitHandle.initRemoteRepo()
				except:
					cLogger.critical("Failed to Initialize Remote Repo")
					b.setBuildFailed()



				# $ git fetch
				try:
					cLogger.debug("Calling gitHandle.remoteFetch()")
					gitHandle.remoteFetch()
				except:
					cLogger.critical("Failed to FETCH from Remote Repo")
					b.setBuildFailed()



				# $ git checkout remotes/origin/b.getBranch()
				try:
					cLogger.debug("Attempting to checkout branch " + str(b.getBranch()))
					gitHandle.checkoutBranch(b.getBranch())
				except:
					cLogger.critical("Failed to checkout branch " + str(b.getBranch()))
					b.setBuildFailed()

				# This assumes the state of the command-line specified Tag
				if ( None != b.getSyncLabel() ):

					try:
						cLogger.debug("Attempting to checkout branch " + str(b.getSyncLabel()))
						gitHandle.checkoutTag(b.getSyncLabel())
					except:
						cLogger.critical("Failed to checkout " + str(b.getSyncLabel()))
						b.setBuildFailed()




				# If git branch isn't in the form of vNUM.NUM -- ie "foo" -- Assume Major and Minor are zero (v0.0)
				#    (ie Branch is not Constructicon-friendly)
				# ... otherwise grab the %Major% and %Minor% from the branch as v(%Major%).(%Minor%)

				# If git branch is "master" -- Assume Major version of 1000 and minor version of 0 (v1000.0)

				# Within the project at the source root, find .constructicon.maintenance file...
				# ... The numeric value in here is %Maint%
				# ... if .constructicon.maintenance is absent, set %Maint% to 0

				# Set Major Minor Maint BuildID
				# b.setMajorVersion(##MAJOR##)
				# b.setMinorVersion(##MINOR##)
				# b.setMaintVersion(##MAINT##)
				# b.setBuildID(##BUIDID##)


				if ( "official" == str.lower( b.getBuildType() ) ):

					# Construct the tag pattern as %BRANCH%-v0.0.%Maint% for non-friendly branches

					# Construct the tag pattern as v1000.0.%Maint% for master

					# Construct the tag pattern as v%major%.%Minor%.%Maint% for friendly branches.... Let's assume v1.3

					# If BuildType is Official.... Ascertain versions already built and Inc Ver

					# If BuildType is Official.... push new Inc Version back into source control

					# If BuildType is Official.... Create Sync State Label using Inc Ver at HEAD
					# b.setSyncLabel(##NEW SYNC LABEL##)

					# If BuildType is Official.... Ascertain versions already built and Inc Ver

					# $ git tag -l <tag pattern>*
					# ... step through it

					# Resulting Tags should be v1000.0.x.N for Master
					#                    %BRANCH%-v0.0.x.N for non-friendly
					#                             v1.3.x.N for friendly
					#
					# ... Where N is a returning series of somewhat contiguous, but possibly gapped numbers

					# Decide the next version... Set Versions
					#					master	foo	v1.3
					#     b.setMajorVersion(%Major%) 	1000	0	1
					#     b.setMinorVersion(%Minor%) 	0	0	3
					#     b.setMaintVersion(%Maint%) 	x	x	x
					#     b.setBuildID(%BuildID%)		y	y	y
					#
					# ... Where X = %Maint% and Y = %BuildID%
					
					# Set new BuildID
					# b.setBuildID(##BUIDID##)


					# If SyncLabel is NOT specified....
					if ( None == b.getSyncLabel() ):

						# tagname = v%Major%.%Minor%.%Maint%.%BuildID% or whatever above (friendly vs unfriendly)
						# $ git tag -a -m "AutoIncrement Blah Blah Blah" <tagname> (AT HEAD)

						# If BuildType is Official.... push new Inc Version back into source control

						# $ git push origin --tags

						# b.setSyncLabel(<tagname>)

						cLogger.critical("METHOD NOT IMPLEMENTED")
						b.setBuildFailed()

					# If SyncLabel IS specified....
					if ( None != b.getSyncLabel() ):
						if not ( cmdOpts.getForceNewLabel() ): 
							cLogger.error("You are generating a new official build in the same state as a previous label: " + str(b.getSyncLabel()))
							cLogger.error("...you must specify --forcenewlabel to make this happen")

							# It is okay to blow out here as official builds won't leave behind a link in the Project node
							exit(1)
						else:
							cLogger.warning("You are generating a new official build in the same state as a previous label: " + str(b.getSyncLabel()))
							# If BuildType is Official.... push new Inc Version back into source control

							# tagname = v%Major%.%Minor%.%Maint%.%BuildID% or whatever above (friendly vs unfriendly)
							# $ git tag -a -m "AutoIncrement Blah Blah Blah" <tagname> <b.getSyncLabel()>


							# $ git push origin --tags

							# b.setSyncLabel(<tagname>)
							# note that ##NEW SYNC LABEL## is actually a copy o

							cLogger.critical("METHOD NOT IMPLEMENTED")
							b.setBuildFailed()

				if ( "local" == str.lower( b.getBuildType() ) ):

					if ( None == b.getSyncLabel() ):
						# If BuildType is Local.... Identify latest successful build version Label

						# Sync to the label b.getBranchName()-LATEST
						# b.setSyncLabel(##LastSuccessfulBuild##)

						cLogger.debug("No Sync Label specified on LOCAL BuildType...")
						cLogger.debug("Auto-Syncing to the Tag " + str(b.getBranch()) + "-LATEST")

						b.setSyncLabel(str(b.getBranch()) + "-LATEST")

						try:
							cLogger.debug("Attempting to checkout branch " + str(b.getSyncLabel()))
							gitHandle.checkoutTag(b.getSyncLabel())
						except:
							cLogger.critical("Failed to checkout branch " + str(b.getSyncLabel()))
							b.setBuildFailed()

						# Set Major Minor Maint BuildID
						# b.setMajorVersion(##MAJOR##)
						# b.setMinorVersion(##MINOR##)
						# b.setMaintVersion(##MAINT##)
						# b.setBuildID(##BUIDID##)

				if ( "dev" == str.lower( b.getBuildType() ) ):
					if ( None == b.getSyncLabel() ):
						# Get SHA of HEAD
						# b.setSyncLabel(##HEAD SHA###)

						# Set Major Minor Maint BuildID
						# b.setMajorVersion(##MAJOR##)
						# b.setMinorVersion(##MINOR##)
						# b.setMaintVersion(##MAINT##)
						# b.setBuildID(##BUIDID##)
						cLogger.critical("METHOD NOT IMPLEMENTED")
						b.setBuildFailed()


				# Set SyncLabel to defined above labels either found or generated...
				# ....by the time we're here --  b.getSyncLabel() should just return what we need

				# Verify SyncLabel specified is in source control and exists

				# If SyncLabel IS Specified.... Use SyncLabel if verified exists
				
				# If BuildType is Local or Official.... Sync BSR to Branch/Version Label
			else:
				# If BuildType is Dev and FILEPATH.... Skip SyncState (this allows building with rogue code)
				
				# Set Major Minor Maint BuildID
				b.setMajorVersion(0)
				b.setMinorVersion(0)
				b.setMaintVersion(0)
				b.setBuildID(0)


			cLogger.debug("END -- Verifying Sources, Versions, and Labels...")


		# ----------------------------------------------------------------------
		# Sync the Code (Obsolete -- checkout is performed above)
		# ----------------------------------------------------------------------

		#if not (b.getBuildFailed()):

		#	cLogger.debug("START -- Pulling in Project sources")

		#	if ( None != b.getRepoPath() and True != b.getBuildFailed() ):
		#		### Pull in Source
		#		cLogger.critical("NOT IMPLEMENTED: Sync the Code")
		#		b.setBuildFailed()


		#	cLogger.debug("END -- Pulling in Project sources")


		# ----------------------------------------------------------------------
		# Provide build variables and debugging output
		# ----------------------------------------------------------------------

		if not (b.getBuildFailed()):

			cLogger.debug("START -- Dumping key variables")

			### Dump Debug Info

			# Dump Debug Info
			print "*** BUILD INFORMATION ********************************************************"
			print ""
			print "Local Build FS Info..."
			print "------------------------------------------------------------------------------"
			print "    Workspace           : " + str(BSR.getWorkspace())
			print "    buildSystemPath     : " + str(BSR.getBuildSystemPath())
			print "    projectPath         : " + str(BSR.getProjectPath())
			print "    outputPath          : " + str(BSR.getOutputPath())
			print ""
			print " Build Generics..."
			print "------------------------------------------------------------------------------"
			print "    BuildType           : " + str(b.getBuildType())
			print "    RepoPath            : " + str(b.getRepoPath())
			print "    FilePath            : " + str(b.getFilePath())
			print "    SyncLabel           : " + str(b.getSyncLabel())
			print "    Branch              : " + str(b.getBranch())
			print "    Workspace           : " + str(b.getWorkspace())
			print "    PublishPath         : " + str(b.getPublishPath())
			print ""
			print " Build Versioning Info..."
			print "------------------------------------------------------------------------------"
			print "    Major Version       : " + str(b.getMajorVersion())
			print "    Minor Version       : " + str(b.getMinorVersion())
			print "    Maintenance Version : " + str(b.getMaintVersion())
			print "    Build ID            : " + str(b.getBuildID())
			print ""
			print "******************************************************************************"

			cLogger.debug("Setting Environment Variables...")

			cLogger.debug("Setting Local Build FS LandingZone...")
			os.putenv("BSLandingZone", str(BSR.getOutputPath()))
			cLogger.debug("Setting Local Build FS ProjectPath...")
			os.putenv("basedir", str(BSR.getProjectPath()))

			cLogger.debug("Setting Local Build Generics BuildType...")
			os.putenv("constructicon.buildtype", str(b.getBuildType()))
			cLogger.debug("Setting Local Build Generics RepoPath...")
			os.putenv("constructicon.repopath", str(b.getRepoPath()))
			cLogger.debug("Setting Local Build Generics FilePath...")
			os.putenv("constructicon.filepath", str(b.getFilePath()))
			cLogger.debug("Setting Local Build Generics SyncLabel...")
			os.putenv("constructicon.synclabel", str(b.getSyncLabel()))
			cLogger.debug("Setting Local Build Generics Branch...")
			os.putenv("constructicon.branch", str(b.getBranch()))
			cLogger.debug("Setting Local Build Generics Workspace...")
			os.putenv("constructicon.workspace", str(b.getWorkspace()))
			cLogger.debug("Setting Local Build Generics PublishPath...")
			os.putenv("constructicon.publishpath", str(b.getPublishPath()))

			cLogger.debug("Setting Local Build Version Major...")
			os.putenv("constructicon.majorversion", str(b.getMajorVersion()))
			cLogger.debug("Setting Local Build Version Minor...")
			os.putenv("constructicon.minorversion", str(b.getMinorVersion()))
			cLogger.debug("Setting Local Build Version Maintenance...")
			os.putenv("constructicon.maintenanceversion", str(b.getMaintVersion()))
			cLogger.debug("Setting Local Build Version BuildID...")
			os.putenv("constructicon.buildid", str(b.getBuildID()))

			os.putenv("antbuildxml", BSR.getProjectPath() + os.sep + "build.xml")
			os.putenv("antbuildtarget", "default")


			cLogger.debug("END -- Dumping key variables")


		# ----------------------------------------------------------------------
		# Build and Return Status
		# ----------------------------------------------------------------------

		if not (b.getBuildFailed()):

			cLogger.debug("START -- Building Project")

			### Build

			# Execute ANT against Constructicon build.xml
			
			# $ pushd /path/to/BuildSystem/scripts
			# $ ../ant/bin/ant -Denv.BSLandingZone=/path/to/OUTDIR/<version> -Denv.antbuildxml=/path/to/project/root/<version> -Denv.antbuildtarget=default
			# $ popd
			try:
				cLogger.debug("Calling Ant...")
				BuildRetVal = os.system(BSR.getBuildSystemPath() + os.sep + "ant" + os.sep + "bin" + os.sep + "ant" + " -logger org.apache.tools.ant.listener.BigProjectLogger " + " -logfile " + BSR.getOutputPath() + os.sep + "constructicon.ant.log.txt " + "-f" + " " + BSR.getBuildSystemPath() + os.sep + "scripts" + os.sep + "build.xml")
			except:
				cLogger.error("Failed to launch ANT build")
				b.setBuildFailed()

			if ( 0 < BuildRetVal ):
				cLogger.error("Build returned non-zero output of [" + str(BuildRetVal) + "]")
				b.setBuildFailed()

			### Verify

			# If BuildType is Official.... Report version as Successful or Failure for build

			cLogger.debug("END -- Building Project")


		# ----------------------------------------------------------------------
		# Publish for official builds
		# ----------------------------------------------------------------------

		if not (b.getBuildFailed()):

			cLogger.debug("START -- Publishing Deliverables...")

			### Publish

			# If BuildType is Official and PublishPath is Specified....

			# 	Verify Specified Publish Path

			# 	Create New location
				##PUBLISH PATH##/{FAILED|SUCCESSFUL}BUILDS/##BUILDTYPE##/##REPOPATH|FILEPATH##/##BRANCH##/##SYNCLABEL##

			#       Copy Deliverables from Workspace to Publish path

			cLogger.debug("END -- Publishing Deliverables...")



		# ----------------------------------------------------------------------
		# Unlinking
		# ----------------------------------------------------------------------

		cLogger.debug("START -- Post Processing and Clean-Up...")

		### Unlink the sources

		# IF BuildType IS dev.... and RepoPath is file share.... unlink ProjectPath
		if ( None != b.getFilePath() ):
			cLogger.debug("UnLinking FilePath " + str(b.getFilePath()) + " to ProjectPath " + str(BSR.getProjectPath()))
			try:
				os.unlink(BSR.getProjectPath())
			except:
				cLogger.error("Failed to UnLink FilePath " + str(b.getFilePath()) + " to ProjectPath " + str(BSR.getProjectPath()))
				cLogger.warning("You will need to UnLink " + str(BSR.getProjectPath()) + " by hand...")

		# If BuildType is Official and PublishPath is Specified....

		# 	Verify Specified Publish Path

		#       Copy Deliverables from Workspace to Publish path

		cLogger.debug("END -- Post Processing and Clean-Up...")



		# ----------------------------------------------------------------------
		# Final Results
		# ----------------------------------------------------------------------

		if not ( b.getBuildFailed() ):
			cLogger.debug("Build Completed Successfully...")
			print "BUILD SUCCEEDED"
			exit(0)
		else:
			cLogger.error("Build Reported Failure...")
			cLogger.critical("BUILD FAILED")
			print "BUILD FAILED"
			exit(1)


if __name__ == "__main__":
	main()

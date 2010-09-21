import logging
import logging.handlers
import os
import sys
import platform
import optparse

class cmdLineOptions:
	"""A cmdLineOptions object holds all of the run-time options for Constructicon derrived from ARGV"""
	def __init__(self):

		###
		### generate and parse the command-line arguments
		###
		self.cmdlineparser = optparse.OptionParser(usage="usage: %prog [options] arg", version="%prog asdfadsf")
		self.cmdlineparser.set_defaults(buildtype="local")

		self.cmdlineparser.add_option("-v", "--verbose", action="count", dest="verbosity", help="be verbose.  use multiple times to be more verbose.")
		self.cmdlineparser.add_option("-q", "--quiet", action="store_true", dest="quiet", help="suppress all output but errors.")

		self.cmdlineparser.add_option("--debug", action="store_true", dest="debug", help="enable debugging output")

		self.cmdlineparser.add_option("-b", "--buildtype", dest="buildtype", type="string", help="""specify the build type for the constructicon build.  build types include: local (default) - builds local build from central code pulled from a defined repo... dev - builds local dev-level builds with no external syncing... official - builds an official build updating tags and versions with the defined repo...""")
		self.cmdlineparser.add_option("-r", "--repopath", dest="repopath", type="string", help="repo path to build from... ie: git://www.github.org/project/foo/")
		self.cmdlineparser.add_option("--synclabel", dest="synclabel", type="string", help="sync repopath to given sha, tag, or branch (at head)")

		self.cmdlineparser.add_option("--workspace", dest="workspace", type="string", help="output path for build.... otherwise, a mount volume is used.")

		self.cmdlineparser.add_option("--publishpath", dest="publishpath", type="string", help="publish path for deliverable bits... useful generally only for official builds.")

		# internal, constructicon has sync'd himself to latest and run himself again...
		self.cmdlineparser.add_option("--selfsynced", action="store_true", dest="selfsynced", help=optparse.SUPPRESS_HELP)

		# internal, dev-helper spew info option...
		self.cmdlineparser.add_option("--spewie", action="store_true", dest="spewie", help=optparse.SUPPRESS_HELP)

		(self.cmdOpts, self.args) = self.cmdlineparser.parse_args()


	def sanityCheck(self):
		pass

	def getSpewie(self):
		return self.cmdOpts.spewie

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
				"synclabel": self.cmdOpts.synclabel,
				"workspace": self.cmdOpts.workspace,
				"publishpath": self.cmdOpts.publishpath}

		return cmdLineOptDict

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
		print "    synclabel           : " + str(self.cmdOpts.synclabel)
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

		try:
			self.msgLogger.debug("Executing runDetection()")
			self.runDetection()
		except:
			self.msgLogger.error("Failed to execut runDetection()")

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

		try:
			self.msgLogger.debug("Initializing Build Generics variables...")
			# Build Generics
			self.buildtype = None
			self.repopath = None
			self.synclabel = None
			self.workspace = None
			self.publishpath = None

			self.msgLogger.debug("Initializing Version Info variables...")
			# Version Info
			self.majorversion = None
			self.minorversion = None
			self.maintenanceversion = None
			self.buildid = None
		except:
			self.msgLogger.error("Cannot initialize base object variables")


	# Retrieve Values
	def getBuildType(self):
		return self.buildtype

	def getRepoPath(self):
		return self.repopath

	def getSyncLabel(self):
		return self.synclabel

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


	# Set Values
	def setBuildType(self, value):
		self.msgLogger.debug("Setting buildtype via setBuildType() as " + str(value))
		self.buildtype = value

	def setRepoPath(self, value):
		self.msgLogger.debug("Setting repopath via setRepoPath() as " + str(value))
		self.repopath = value

	def setSyncLabel(self, value):
		self.msgLogger.debug("Setting synclabel via setSyncLabel() as " + str(value))
		self.synclabel = value

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


	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print " Build Generics..."
		print "    BuildType                    : " + str(self.buildtype)
		print "    RepoPath                     : " + str(self.repopath)
		print "    SyncLabel                    : " + str(self.synclabel)
		print "    Workspace                    : " + str(self.workspace)
		print "    PublishPath                  : " + str(self.publishpath)
		print " Build Versioning Info..."
		print "    Major Version                : " + str(self.majorversion)
		print "    Minor Version                : " + str(self.minorversion)
		print "    Maintenance Version          : " + str(self.maintenanceversion)
		print "    Build ID                     : " + str(self.buildid)
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
		try:	
			self.workspace = buildObject.getWorkspace()
		except:
			self.msgLogger.error("Unable to retreive workspace from buildObject.getWorkspace()")

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




		
	### os-independent mount point maker
	# intake: source location of the link and destination of where to make the link
	# returns true if successful, false if not successful
	# 
	def makemountpoint(linksrc, linkdest):
		return True

	def testMe(self):
		print "******************************************************************************"
		print " Process: " + str(self) 
		print " testMe() output"
		print "------------------------------------------------------------------------------"
		print "    Workspace		: " + str(self.workspace)
		print "    os.environ[temp]     : " + str(os.environ['TMPDIR'])
		print "******************************************************************************"


def main():
	try:
		cmdOpts = cmdLineOptions()
		if ( cmdOpts.getSpewie() ):
			cmdOpts.testMe()

		myDict = cmdOpts.getOptDict()
	except: 
		print("Failed to bootstrap the CommandLine parsing process")

	#                         Caller Instance      , CmdLine Obj
	cLogger = messageHandler("Constructicon Master", cmdOpts.getVerbosity())
	if ( cmdOpts.getSpewie() ):
		cLogger.testMe()

	cLogger.debug("Message Handler Initialized")
	cLogger.debug("cmdLineOptions() previously established before Message Handler Initialized...")
	cLogger.debug("""myDict.get("verbosity") is : """ + str(myDict.get("verbosity")))
	cLogger.debug("""myDict.get("quiet") is : """ + str(myDict.get("quiet")))
	cLogger.debug("""myDict.get("debug") is : """ + str(myDict.get("debug")))
	cLogger.debug("""myDict.get("buildtype") is : """ + str(myDict.get("buildtype")))
	cLogger.debug("""myDict.get("repopath") is : """ + str(myDict.get("repopath")))
	cLogger.debug("""myDict.get("synclabel") is : """ + str(myDict.get("synclabel")))
	cLogger.debug("""myDict.get("workspace") is : """ + str(myDict.get("workspace")))
	cLogger.debug("""myDict.get("publishpath") is : """ + str(myDict.get("publishpath")))



	cLogger.debug("START -- detectOS()")
	testedOS = detectOS(cmdOpts.getVerbosity())
	if ( cmdOpts.getSpewie() ):
		testedOS.testMe()
	cLogger.debug("END -- detectOS()")


	cLogger.debug("START -- Instantiating builderObject b")

	b = builderObject(cmdOpts.getVerbosity())
	if ( cmdOpts.getSpewie() ):
		b.testMe()

	cLogger.debug("END -- builderObject b Instantiation")


	cLogger.debug("START -- building up BSR...")
	BSR = localBSR(myDict.get("verbosity"), b)
	if ( cmdOpts.getSpewie() ):
		BSR.testMe()


	###
	### Set up Workspace (either defined workspace or standard mountpoint)
	###


	# Make mount point

	# Prep directory structure


	cLogger.debug("END -- BSR built up...")


	cLogger.debug("START -- Syncing Build System...")
	###
	### Pull in BuildSystem
	###

	# Check for current build system
		# Verify Manifest of current build system

	# Pull in BuildSystem
		# Verify Manifest of received build system

	# Re-Execute Constructicon (call --selfsynced)

	cLogger.debug("END -- Syncing Build System...")

	cLogger.debug("START -- Dumping key variables")

	###
	### Dump Debug Info
	###

	# Dump Debug Info


	cLogger.debug("END -- Dumping key variables")


	cLogger.debug("START -- Pulling in Project sources...")
	###
	### Pull in Source
	###

	# Sync in RepoPath with SyncLabel


	cLogger.debug("END -- Pulling in Project sources")

	cLogger.debug("START -- Building Project")
	###
	### Build
	###

	# If Official Build, Push Versioning back to home repopath

	# Execute ANT



	cLogger.debug("END -- Building Project")

	cLogger.debug("START -- Publishing Deliverables...")
	###
	### Publish
	###

	# Push deliverables from workspace to Publish Path



	cLogger.debug("END -- Publishing Deliverables...")


if __name__ == "__main__":
	main()

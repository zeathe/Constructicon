# Constructicon ###############################################################

#### This is a work in progress ####

### What is Constructicon?

Constructicon is a simple build framework designed solely provide the exact
same build experience between developers, self-building end-consumers, and
managed point-builds.  Constructicon strives to provide cross-platform build
functionality for Mac OS X, Linux/BSD, and Windows that all react the same way
so that developers know what to expect.

In addition to providing a cross-platform foundation, Constructicon is designed
to perform auto-magic versioning and take the pain out of the build/deploy
cycle through as much automation as possible.  Constructicon interfaces with
the GIT source control system and performs builds in a sane, stable, and
repeatable manner.

### Why Constructicon? -- I'm a consumer of a Constructicon Project

As an end-consumer, Constructicon is great for one simple reason: You can be
assured that your build locally is sourced from the exact same code as a
developer from the project.  You can consistently build point release builds,
unstable release builds, or even current builds on your local system from
a previously built tag from the developers.

What's better -- there is no installation for Constructicon.  You simply pull
the latest copy of Constructicon and dump it into a folder and then run a
command-line against it.

### Why Constructicon? -- I'm a developer

Constructicon makes development more stream-lined.  If you're writing a project
to run on multiple platforms, Constructicon can automate builds across these
platforms and standardize the basic build steps across these platforms while
still allowing flexibility to the developer in their build commands within
the lower-level ANT scripts that persist in a given code project.

After the initial overhead to plug a project into the framework, many things
are received as freebies.

+ No more futzing with version numbers.... especially in an uncommon way
  between platforms
+ No manually tagging stuff in source control
+ It's got a cool name
+ Plug your project into Constructicon... Plug Constructicon into CruiseControl,
  Hudson, ccNET, or whatever.... and watch it go.
+ Stream-lined building for consumers of your code... unless they can't type
  in a command-line -- they'll probably be able to build your project just
  like you do.... and if they're missing something to build your project, you
  may be able to remedy that by bundling the required tools to build your
  project in your project.




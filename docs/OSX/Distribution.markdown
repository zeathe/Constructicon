# DISTRIBUTION OF MAC SOFTWARE ################################################

## Theories of Mac Software Distribution

I personally believe that the DMG file is _the_ mechanism that should be used
for Mac deployments.  It's very simplistic, standardized, and follows the
conventions that an APP bundle should be self-contained.

A good write-up on this can be found at [Idle Blog - How to Distribute Your Software](http://boredzo.org/blog/archives/2006-01-16/how-to-distribute-your-software)

I also agree that a PKG Installer file should only be used for frameworks on a
Macintosh platform.

... THUS.... you should probably create a DMG file as part of your build and
distribution process.

## Making a DMG Installer Package

The DMG needs to be manually created initially -- but I would argue that this
is no different than creating a NIB in Interface Builder as part of your coding
process.  Once you have a DMG template, you can stuff it away in your source
tree and re-use it in a scripted fashion with HDIUTIL on each build.

Let's get rocking and rolling...

### Initial DMG Template Creation

Let's create a sparse package disk image.  You're obviously working on an
application and you should know what you're going to name your application. For
this example, let's say you're working on FOO that will be bundled as Foo.app
and will be v0.0.0.0 (at least for the initial build)...

#### Create the TEMPLATE directory

Create the initial directory workspace...

	>pushd /tmp
	>mkdir /tmp/foo.app.dmg.sparse.template

Create a place holder for your Application...

	>mkdir /tmp/foo.app.dmg.sparse.template/foo.app

Create a link to the Applications folder...

	>ln -s /Applications /tmp/foo.app.dmg.sparse.template/Applications

It's important that if you have any other icons other than your bundle present,
you create place holders for those now...

You could create a placeholder for a single license text file...

	>touch /tmp/foo.app.dmg.sparse.template/LICENSE.txt

You could create a placeholder for a single readme text file...

	>touch /tmp/foo.app.dmg.sparse.template/README.txt

You could create a folder for numerous documentation files...

	>mkdir /tmp/foo.app.dmg.sparse.template/README

#### Create the DMG Sparse file

We'll initially create the DMG... You could use Disk Utility and point-and-click
your way through everything... but why when you can use a terminal?

	>hdiutil create -srcfolder /tmp/foo.app.dmg.sparse.template -volname "FOO TEMPLATE" -fs HFS+ -fsargs "-c c=64,a=16,e=16" -format UDSP -size 24M /tmp/foo.template.dmg

Poof. You have your DMG.  But we're not done yet...

#### Create the folder Background

Use your favorite graphics program to create an awesome background to stage
your software in.... make little spots for the folders to rest in with
graphical arrows.  Channel your inner Mac Fanboy and make it really artistic...
no... artistEEK!

Make sure that the picture is set to a specific size that you want the DMG
window itself to be.... say 320x200, 640x480, 640x320, whatever....

Let's say you save your fabulous background as /tmp/foo.dmg.background.png --
you can use the Jpeg, GIF, or PNG formats if I remember correctly... you might
be able to even use more -- but I honestly really like PNG myself.

#### Mount the Template

Let's mount up your template now.... so we can start our tweaking process for
the graphical presentation of your installer.  Let's be very specific though
in how we mount this...

	>mkdir /tmp/foo.mount
	>hdiutil attach /tmp/foo.template.dmg.sparseimage -mountpoint /tmp/foo.mount

If you don't immediately get Finder to pop up with your new image -- open it
up by hand...

	>open /tmp/foo.mount

#### Add the Background, Adjust the Icon Positions, Adjust the Window Prefs

After you have the image file open in Finder, adjust the view settings....

Switch to icons view with Command+1 keys

Hide the Sidebar with ALT+COMMAND+S

Hide the Toolbar with ALT+COMMAND+T

Command+J will bring up the folder options dialog... 

Check Always Open in Icon View

Adjust the Icon Size and Icon Spacing sliders to your desired positions

Adjust the Text Size to your desired size

Make sure that Show Item Info is unchecked

Show Icon Preview is optional.... This will actually provide a thumbnail
instead of standard OS icons for some file types.

Dot "Picture" for background

Open a second Finder window into /tmp:

	>open /tmp

Find your background image and Drag-and-Drop it into the Background frame
in the Finder properties window.

Finally, adjust your window size to the appropriate size for your background
image and move your icons around until they're in the correct positions you
desire.

#### Verify the Template DMG

At this point, your stuff should be pretty solid.  Make sure no processes like
a terminal window are still in /tmp/foo.mount... Eject the image...

	>hdiutil eject /tmp/foo.mount

Now -- verify that all your purty changes peristed...  Open up it up again...

	>open /tmp/foo.template.dmg.sparseimage

Everything should look good....  Eject it again... Go ahead and use another 
Finder window... otherwise you'll have to eject /Volumes/FOO TEMPLATE:

	>hdiutil eject "/Volumes/FOO TEMPLATE"

#### Compact Your Template DMG

	>hdiutil compact /tmp/foo.template.dmg

### Check in the DMG Template

Put your DMG into a sub-folder of your source code and check it into your
SCM system.  It'll be used later on....


### Constructicon Making APP Installers 

If you follow my ANT scripts -- you'll be calling GCC.  I don't care how you're
building (if you're using xcodebuild, GCC, Ouija Board, European Swallow, etc)
but if you're using Constructicon -- your code should be getting pooped out
into the Constructicon output.root folder for DIST and DEBUG builds as follows:

	${output.root}/DIST
	${output.root}/DEBUG

... Essentially your Distributable version of the Foo app should be at:

	${output.root}/DIST/foo.app

... and your Debug version at:

	${output.root}/DEBUG/foo.app

... and of course, you should also have ${object.root}/{DEBUG|DIST}

SO.... we basically just need to

+ Duplicate the Template DMG file into a DIST and DEBUG image copies
+ Mount the DEBUG DMG and populate it
+ Rename the Volume
+ Mount the DIST DMG and populate it
+ Rename the Volume
+ Unmount them both
+ Resize the DEBUG DMG for the file size
+ Resize the DIST DMG for the file size
+ Convert the DEBUG DMG to a compressed read-only DMG
+ Convert the DIST DMG to a compressed read-only DMG

We'll keep the DMG files in the deliverables (${output.root} directory) and
the heavy lifting in the Objects (${object.root}) directory to keep everything
tidy in the build sandbox.

#### Duplicate the DMG files

I would highly advise *NOT* just picking an arbitrary size for the DMG files
as this can inevitably do both...
+ Waste large amounts of space during build times
+ Cause Build Breaks when the DMG isn't large enough after an app grows
  after time and exceeds the arbitrarily set size

Do a DU or something of the sort on the ${output.root}/DEBUG and the 
${output.root}/DIST folders.... take that and add say a couple of MB, and shove
those in appropriately for the -size nnnM listed in the two below commands...

Create our DEBUG landing area

	>cp ${project.root}/path/to/template.dmg.sparseimage ${object.root}/appname.debug.dmg.sparseimage

Create our DIST landing area

	>cp ${project.root}/path/to/template.dmg.sparseimage ${object.root}/appname.dmg.sparseimage


#### Mount the DEBUG DMG and Populate

	>mkdir ${object.root}/DEBUGDMG
	>hdiutil attach ${output.root}/appname.debug.dmg.sparseimage -mountpoint ${object.root}/DEBUGDMG -readwrite
	>cp -Rv ${output.root}/DEBUG/FOO.app ${object.root}/DEBUGDMG/FOO.app
	>cp ${output.root}/DEBUG/readme.txt ${object.root}/DEBUGDMG/README.txt
	>cp ${project.root}/docs/LICENSE ${object.root}/DEBUGDMG/LICENSE.txt

	>bless --openfolder ${object.root}/DEBUGDMG

#### Rename the Volume

	>diskutil renameVolume ${object.root}/DEBUGDMG "APPName v${Major}.${minor}.${maint}.${buildid} DEBUG"


#### Mount the DIST DMG and Populate

	>mkdir ${object.root}/DISTDMG
	>hdiutil attach ${object.root}/appname.dmg.sparseimage -mountpoint ${object.root}/DISTDMG -readwrite
	>cp -Rv ${output.root}/DIST/FOO.app ${object.root}/DISTDMG/FOO.app
	>cp ${output.root}/DIST/readme.txt ${object.root}/DISTDMG/README.txt
	>cp ${project.root}/docs/LICENSE ${object.root}/DISTDMG/LICENSE.txt

	>bless --openfolder ${object.root}/DISTDMG

#### Rename the Volume

	>diskutil renameVolume ${object.root}/DISTDMG "APPName v${Major}.${minor}.${maint}.${buildid}"

#### Unmount them both
	>hdiutil eject ${object.root}/DEBUGDMG
	>hdiutil eject ${object.root}/DISTDMG

#### Resize the DEBUG and DIST DMG

Before we get these ready for distribution, let's make sure they're as small as
they should be....

	>hdiutil compact ${object.root}/app.debug.dmg.sparse
	>hdiutil compact ${object.root}/app.dmg.sparse


#### Convert the DEBUG DMG to a compressed read-only DMG

	>hdiutil convert ${object.root}/app.debug.dmg.sparse -format UDBZ -o ${output.root}/app.debug.dmg

#### Convert the DIST DMG to a compressed read-only DMG

	>hdiutil convert ${object.root}/app.dmg.sparse -format UDBZ -o ${output.root}/app.dmg

# Versioning Binaries #########################################################

#### This is a work in progress ####

## Version Theory and Stamping Theory ##

When working on Software applications, versioning becomes very important very
quickly.  The very first problems that can be helped with versioning starts
with the very second build and distribution of an author's software package.
Versioning becomes critical during efforts to identify which version of
software a client or end-user may be running.

Versioning can be used for controlling and stablizing process and program
interactions, or defining a level of support for an API.

### Build Numbers 

There are many many different ideas about versioning.  I'm not one to take
anything written in wikipedia as generally mostly factual -- but their entry
on [Software Versioning](http://en.wikipedia.org/wiki/Software_versioning)
actually has some good information in it.

Generally, I like to adhere to the idea of the following:

<Major Version>.<Minor Version>.<Maintenance Version>.<Build Identifier>

#### Major Version

The Major version of a project is incremented when large changes are made to
a software package that change its features, fundamental design and its
functionality with other software packages.  Most important to this fact is
that these changes are *not* backward compatible with previous versions.

Consumers of Widget Application Foo v1.0 will need to make sure that they
will be able to continue to do what they have been doing when upgrading to
Widget Application Foo v2.0... Shame on the consumer for not doing proper
verifications when upgrading from v1.0 to v2.0.

#### Minor Version

The Minor version of a project is incremented when large changes are made to
a software package that change its features, fundamental design or other
major changes... but the software *is* backward compatible with previous
versions.

Consumers of Widget Application Foo v1.0 should be able to upgrade to v1.1
(hopefully) without worry of breaking.  If a consumer cannot use v1.1 from
v1.0, shame on Widget Application Foo's author for not properly upholding
backward compatibility.

#### Maintenance Version

The Maintenance Version is a serially incremented number for each release or 
distributed build of a given branch.  Say that Widget Application Foo v1.0
has some bugs in it, or it uses OpenSSL statically and needs to updated for
security and to fix those bugs.  If the first release was v1.0.1, the bug
fixes may come out in v1.0.2.

Increments in Maintenance versions should not be a release vehicle for large
functionality changes, and should be strictly minor code enhancements or bug
fixes.

#### Build Identifier

The build identifier needs to be a unique identification string for each build
of a given Major.Minor.Maint. These are the unique finger prints of any given 
build for a release vehicle.

I've seen Build IDs as the hashes out of GIT, or the CLs out of Perforce
and Subversion.  I've also seen the Build IDs simply be incremental, flattened
date/time stamps, or seconds since epoch.

Constructicon simply increments BuildID based on the last label involved in
GIT.... But the BuildID is the most varied design for versioning amongst
software manufacturers like Apple, Microsoft, etc.

## Versioning By Platform ##

#### Apple Software - kext Info.plist

Apple has a fairly strict versioning scheme for OS X software within their
Info.plist configurations.  The [kext info here](http://developer.apple.com/library/mac/#documentation/Darwin/Conceptual/KEXTConcept/Articles/infoplist_keys.html)
is pretty interesting, and probably applies to just about anything from Apple
using the Info.plist versioning schemes (not just kext packages).

In a nutshell, Apple uses Major.Minor.Maint with a small set of special 
identifiers for BuildID:

Major Version		-	Limited to 4 digits
Minor Version		-	Limited to 2 digits
Maint Version		-	Limited to 2 digits
Build Identifier	-	Special Letters {d|a|b|fc} and [0-255] value


#### Microsoft - VERSIONINFO

Microsoft uses some interesting 32-bit INT representing 16-bit INT pairs for
their versioning.  Details on the resource file for VERSIONINFO can be found
[on MSDN](http://msdn.microsoft.com/en-us/library/aa381058.aspx) and the
details are fairly clear.

Microsoft also supports some key flags in the VERSIONINFO file that can clearly
identify development-level builds... For example, the SpecialBuild, and the
PrivateBuild flags.

Basically, each of the four version numbers can be between [0-65535].... with
some different limitations.


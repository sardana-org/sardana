	Title: reorganization of code repos
	SEP: 1
	State: OBSOLETE
	Reason: 
	 SEP15 obsoletes SEP1. Sardana project has been migrated to GitHub.
	 SEP1 has references to SourceForge for Sardana project.
	 3rd party repositories of macros and controllers will remain in 
	 SourceForge until further notice.
	Date: 2013-08-06
	Drivers: Carlos Pascual-Izarra cpascual@cells.es
	URL: http://www.sardana-controls.org/sep/?SEP1.md
	License: http://www.jclark.com/xml/copying.txt
	Abstract:
	The sardana source will be moved to a git repository. This SEP
	proposes the structure and location of the final repository, including 
	what to do with the Taurus code.


Introduction
------------

This SEP describes the details about how the source code repositories of sardana will be re-organized. It tries to answer the following questions:

 - which version control system we use
 - where do we host the canonical repo
 - where do we put the taurus code


Description of current (June 2013) situation
--------------------------------------------

**Note on nomenclature:** from now on, we use *"sardana"* (quoted, lowercase) to denote the code that is currently in the sardana.core project of sf.net (i.e., Pool+MS+Spock + utils +docs,...). When we want to refer to the whole Sardana suite, which includes Taurus we will either refer to it as *Sardana suite* or just *Sardana* (unquoted, with capital S)

The Sardana suite code is currently in 4 Subversion repositories hosted in two sourceforge.net projects (sardana and tango-cs):

 part of sardana              |  repository                                | project 
 ---------------------------- | ------------------------------------------ |-----------
 "sardana"                    | svn.code.sf.net/p/sardana/code             | sardana (SF)
 3d party controllers         | svn.code.sf.net/p/sardana/controllers/code | sardana (SF)
 3d party macros              | svn.code.sf.net/p/sardana/macros/code      | sardana (SF)
 taurus                       | svn.code.sf.net/p/tango-cs/code/gui/taurus | tango-cs (SF)

Each of these repositories has its own trunk/branches/tags, and allows for independent user permissions administration.

Motivation
----------

Currently code of the Sardana suite is managed with subversion repositories. Moving it to a more modern control version sistem (and in particular to Git) has been requested by potential users and identified as a way to better promote collaboration in the Sardana Community mostly for the following reasons:

 - easier branching/merging (necessary in a scattered community like ours)
 - easier tools/workflows for code validation

In addition, the problems caused by the current separation of taurus in an independent svn repository disconnected from the "sardana core" repository need to be solved. The main issue is that in between releases, during the development phase, many changes require commits to both taurus and "sardana" repositories. These commits can only be identified as belonging to the same change by either reading their comments or by linking their dates. This creates difficulties when trying to revert changes that caused problems.

Requirements
------------

The following requirements are given in rough order of importance (the first 3 are the ones that are really mandatory, while the rest are optional "nice-haves")

 1. use git for version control
 2. allow to easilly identify coherent "sardana" and taurus revisions in the past (not only in releases but also between releases)
 3. allow users that only want taurus to continue downloading just taurus code (not forcing them to install "sardana")
 4. having tools for managing the discussions/decisions on patch validation
 5. not forcing contributors to use more than one account for contributing
 6. be compatible with tango-cs accounts
 7. make the code/repos structure reflect the official vision of Sardana as a whole scada that includes Taurus.


Proposed Plan for implementation
--------------------------------

Several steps:

a) As a first step, we propose to follow steps **1-7** from [this recipe](http://www.17od.com/2010/11/11/migrating-a-sourceforge-subversion-repository-to-github/) to migrate the current 4 svn repositories to corresponding 4 *local* git repos. Note that this involves using [svn2git](https://github.com/nirvdrum/svn2git) instead of git-svn

b) Then we would use git subtree to merge the taurus git repo into the "sardana" git repo. The taurus code will be in a subdirectory called "taurus" at the root of the "sardana" repo. The branches and tags would be merged using preffix "taurus" for the taurus ones.

c) The resulting 3 local git repositories ("sardana"+taurus, 3rd party macros and 3rd party controllers) would then each be cloned to sourceforge to be used as the canonical ones: 


With this solution we directly address all the requirements except #4. Regarding #4, even if we do not directly adress it, we also do not block it, since we later on can opt for using an email based patch review process or install some other kind of code revision tool -e.g. gerrit)

This solution also does not force any modification on the current source code or its structure (everything that works now on a local copy from svn.code.sf.net/p/sardana/code/trunk, would work on the "master" of a clone of git.code.sf.net/p/sardana/code, and everyting that works in a checkout of svn.code.sf.net/p/tango-cs/code/gui/taurus/trunk would work from the taurus subdirectory of the clone of git.code.sf.net/p/sardana/code). 


Actual implementation details
-----------------------------

After getting consensus on the proposed plan for implementation, this was put into action. APPENDIX I contains some raw notes on how this was done in practice.

The result is that 3 git repositories were created in the sardana.sf.net project:


 part of sardana              |  repository                                | Notes
 ---------------------------- | ------------------------------------------ | -------
 Sardana (including taurus)   | git.code.sf.net/p/sardana/sardana.git      | 1,2,3
 3d party controllers         | git.code.sf.net/p/sardana/controllers.git  | 4
 3d party macros              | git.code.sf.net/p/sardana/macros.git       |

Notes:

 1. this includes the taurus code as a subdirectory at its root
 2. The code in the ASCANCT branches of both taurus and sardana svn repos has been 
merged into sep6 branch of the sardana.git repository. 
 3. The code of the taurus_cleanup branch is now the base for the sep3 branch of the sardana.git repository.
 4. The code in the ASCANCT branch of the controllers svn repository is now in the sep6 branch of the controllers.git repository.

Instructions on how to clone each of these repositories can be found by following the appropriate link in:

https://sourceforge.net/p/sardana/_list/git

Regarding the original svn repositories, they have been left in an effectively read-only mode because all commits are blocked by a pre-commit hook.


Pending tasks after the migration
---------------------------------

The SEP1 just deals with the migration of the repositories to git. But this migration is done in order to enable more efficient forms of collaboration and therefore discussions should start (possibly with another SEP) to agree on and describe a workflow for code contribution.


Links to more details and discussions
-------------------------------------

The seminal discussion for this SEP started in this thread:
<https://sf.net/mailarchive/forum.php?thread_name=201305311445.13302.cpascual%40cells.es&forum_name=sardana-users>

The discussions about the SEP1 itself are in the sardana-devel mailing list: <https://sourceforge.net/mailarchive/forum.php?thread_name=201306111047.41202.cpascual%40cells.es&forum_name=sardana-devel>

APPENDIX I: commands used for migrating
----------------------------------------

Note that what follows is a raw transcript of the commands that I (cpascual) used while putting the plan for implementation into practice. These are just copy-pasteable notes, not a script. They worked in a Debian7 machine with svn and git installed from official deb repos and svn2git installed from its git repo. I also used a newer version of git (1.8.3.1.378.g9926f66) for the last part, as mentioned in the notes.


~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#Docs used
#http://www.git-scm.com/book
#http://www.17od.com/2010/11/11/migrating-a-sourceforge-subversion-repository-to-github/
#https://github.com/nirvdrum/svn2git
#https://sourceforge.net/p/forge/documentation/Git/
#http://www.git-scm.com/book/en/Git-Tools-Subtree-Merging
#http://h2ik.co/2011/03/having-fun-with-git-subtree/ 

#create dirs
mkdir /home/cpascual/src/sdnongit
cd /home/cpascual/src/sdnongit

#create local backups of svn repos (same commands also update them)
mkdir svnbck
rsync -av svn.code.sf.net::p/sardana/code/ svnbck/sardana/
rsync -av svn.code.sf.net::p/sardana/macros/code/ svnbck/macros
rsync -av svn.code.sf.net::p/sardana/controllers/code/ svnbck/controllers
rsync -av svn.code.sf.net::p/tango-cs/code/ svnbck/tango-cs

#lock the commits to the gui/taurus directory of the tango-cs svn repo:
#log into tango-cs 
ssh -t cpascual,tango-cs@shell.sourceforge.net create

#and create /home/svn/p/tango-cs/code/hooks/pre-commit file with perms 755 containing:

#~~~~~~~~~~~~
#!/bin/sh

REPOS="$1"
TXN="$2"

SVNLOOK=/usr/bin/svnlook

# Committing to gui/taurus is not allowed
$SVNLOOK changed -t "$TXN" "$REPOS" | egrep "^(A|U|D|UU|_U)\W*gui/taurus" && /bin/echo "Migration of taurus repo in course. Commits forbidden!" 1>&2 && exit 1

# All checks passed, so allow the commit.
exit 0
#~~~~~~~~~~~~

#lock the commits to the sardana svn repos:
#log into sardana 
ssh -t cpascual,sardana@shell.sourceforge.net create

#and create pre-commit files with perms 755 (in /home/svn/p/sardana/{,controllers/,macros/}code/hooks/) containing:

#~~~~~~~~~~~~
#!/bin/sh

/bin/echo "Migration to git in course. Commits forbidden!" 1>&2
exit 1
#~~~~~~~~~~~~


#create an all-authors.txt map
for r in sardana macros controllers;do echo $r; svn log file:///home/cpascual/src/sdnongit/svnbck/"$r" -q | awk -F '|' '/^r/ {sub("^ ", "", $2); sub(" $", "", $2); print $2" = "$2" <"$2"@users.sourceforge.net>"}' |sort -u > authors-"$r".txt; done
svn log file:///home/cpascual/src/sdnongit/svnbck/tango-cs gui/taurus -q | awk -F '|' '/^r/ {sub("^ ", "", $2); sub(" $", "", $2); print $2" = "$2" <"$2"@users.sourceforge.net>"}' |sort -u > authors-taurus.txt
cat authors-*.txt|sort -u > allauthors.txt

#transform repos from svn to git (creates the repos in /home/cpascual/src/sdnongit/gitrepos/xxxxx). 
# Note that for taurus we cannot use the local backup since we only want to extract the taurus part, and svn2git seems to need an http:// URL for this
# note: this commands fails (with 'command failed: 2>&1 git branch --track "2>&1 git branch --track "ASCANCT" "remotes/svn/ASCANCT" ') if using git version 1.8.3.1.378.g9926f66 instead of the debian distributed git (version 1.7.10.4)
mkdir gitrepos
cd gitrepos
for r in sardana macros controllers;do mkdir $r; cd $r; svn2git file:///home/cpascual/src/sdnongit/svnbck/"$r" -m --authors ../../allauthors.txt ; cd .. ; done
mkdir taurus; cd taurus; svn2git http://svn.code.sf.net/p/tango-cs/code/gui/taurus --no-minimize-url -m --authors ../../allauthors.txt; cd ..
cd ..

#clone the git repos for cleaning from svn rubish...

mkdir gitrepos/new
cd gitrepos/new
git clone /home/cpascual/src/sdnongit/gitrepos/taurus
git clone /home/cpascual/src/sdnongit/gitrepos/sardana
git clone /home/cpascual/src/sdnongit/gitrepos/controllers
git clone /home/cpascual/src/sdnongit/gitrepos/macros

#NOTE: When we clone, we lose the branches from taurus and sardana. They may need be recreadted (origin/foo --> foo)  before publishing these repos...
# we decided to migrate only the following branches (and to rename them!)
# for taurus: 
#    origin/taurus_cleanup --> sep3
#    origin/ASCANCT  --> sep6
# for sardana:
#    origin/ASCANCT --> sep6
# for controllers:
#    origin/ASCANCT --> sep6

cd taurus; git branch --no-track sep3 origin/taurus_cleanup ; git branch --no-track sep6 origin/ASCANCT; cd ..
cd sardana; git branch --no-track sep6 origin/ASCANCT; cd ..
cd controllers; git branch --no-track sep6 origin/ASCANCT; cd ..



#FOR MERGING "sardana" and taurus:
#approach 1, using standard git-merge with subtree strategy for merging (see section 6.7 of progit)
###NOTE: Ifinally decided to use Approach 2. I leave this here for reference only
#cd /home/cpascual/src/sdnongit/gitrepos/new/sardana
#git remote add taurus /home/cpascual/src/sdnongit/gitrepos/taurus
#git fetch taurus
#git checkout -b taurus taurus/master
#git checkout master
#git read-tree --prefix=taurus/ -u taurus
#git commit -m 'merged taurus master as subtree of sardana'
#git merge -s subtree taurus   
##note that in the previous command I do NOT put -squash because I **DO** want to merge histories

#Approach2 (requires non-standard git-subtree which is still not in the main git distro... not standard/mature):
#So from this point on, I am using git version 1.8.3.1.378.g9926f66  !!!!!!
#NOTE: in this approach I already handle the merging of the branches as well.

cd /home/cpascual/src/sdnongit/gitrepos/new/sardana
git checkout -b sep3;  git subtree add --prefix=taurus /home/cpascual/src/sdnongit/gitrepos/new/taurus sep3
git checkout sep6;  git subtree add --prefix=taurus /home/cpascual/src/sdnongit/gitrepos/new/taurus sep6
git checkout master; git subtree add --prefix=taurus /home/cpascual/src/sdnongit/gitrepos/new/taurus master


#Note: If later on we wanted to split it (creating a taurus_branch):
git subtree split --prefix=taurus --annotate='(split) ' --rejoin --branch taurus_branch


#push the resulting repos to sf

#first create the (empty) projects in sf using mountpoints sardana.git, controllers.git macros.git
# see https://sourceforge.net/p/forge/documentation/Git/

#configure the local git repos to use the sf repos as origin and push the master and branches:

cd /home/cpascual/src/sdnongit/gitrepos/new/sardana
git remote rm origin
git remote add origin ssh://cpascual@git.code.sf.net/p/sardana/sardana.git
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
git push origin master
git push origin sep3
git push origin sep6

cd /home/cpascual/src/sdnongit/gitrepos/new/controllers
git remote rm origin
git remote add origin ssh://cpascual@git.code.sf.net/p/sardana/controllers.git
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
git push origin master
git push origin sep6

cd /home/cpascual/src/sdnongit/gitrepos/new/macros
git remote rm origin
git remote add origin ssh://cpascual@git.code.sf.net/p/sardana/macros.git
git config branch.master.remote origin
git config branch.master.merge refs/heads/master
git push origin master


#Note: at this point we may want to change the messages in the pre-commit hooks used for locking the svn repos.

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



License
-------

The following copyright statement and license apply to SEP1 (this
document).

Copyright (c) 2013  Carlos Pascual-Izarra

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

Changes
-------

* 2016-11-22 
  [mrosanes](https://github.com/sagiss/) 
  Migrate SEP1 from SF wiki to independent file, modify URL. Change SEP state from ACCEPTED --> OBSOLETE according SEP15.

* 2013-08-06
  [cpascual](https://sourceforge.net/u/cpascual/) changed SEP state from CANDIDATE-->ACCEPTED

* 2013-08-06
  [cpascual](https://sourceforge.net/u/cpascual/) Added "Actual Implementation details" section

* 2013-07-05:
  [cpascual](https://sourceforge.net/u/cpascual/) changed SEP state from DRAFT-->CANDIDATE. Small modifications to the document to reflect conclusions from <https://sourceforge.net/mailarchive/forum.php?thread_name=201306111047.41202.cpascual%40cells.es&forum_name=sardana-devel> to date.

* 2013-06-11:
  [cpascual](https://sourceforge.net/u/cpascual/) Initial version written trying to capture the initial discussions in sardana-users list

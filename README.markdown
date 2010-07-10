![alt text][2]

##Screenshot / Code Snippet
Current Version: Beta build v1.0

![alt text][1]
![alt text][3]

##About

StackTracker, a cross-platform desktop notifier for the StackExchange API built with PyQt4

The application displays a task tray notification when someone has posted an answer or a comment to a question you 
are tracking on any of the StackExchange sites.  Clicking the notification will open the corresponding question in your browser.

###License

GPL - Full LICENSE file available in the repo (below)

###Download

Linux build:  [Download Linux ZIP][4] (Requires Python 2.6 and PyQt4 to be installed)

Run `>> python StackTracker.py` from the StackTracker folder

----------

Windows build: [Download Windows ZIP][5] (May need Microsoft VC++ DLL installed)

Launch the `StackTracker.exe`.

----------

Mac OS X build: [Download Mac OS X tarball][6] (Requires Growl to be installed)

Launch `StackTracker.app`. Only tested in Leopard/Snow Leopard on Intel-based Macs.

##Contact

Matt Swanson, mdswanso@purdue.edu

##Code

Tools/Frameworks/Etc Used: Python, PyQt4, gVim

Repo: `git clone git@github.com:swanson/stacktracker.git`

[http://github.com/swanson/stacktracker][7]

##Release Notes
Please post feature requests or bugs in the answer section.  Patches or pull requests are more than welcome.

###Beta Builds

**v1.0** (July 9)

 - StackTracker has now entered Beta status!
 - Support for API v1.0 release
 - Fixed bug in Mac OS X build involving exiting from the tray icon
 - Added Mac OS X build icon
 - Added default logo for all new Area51/StackExchange sites
 - Economized API calls
 - Added better handling of multiple alerts overwriting each other
 - Added notification when a question is autoremoved
 - Removed option to autoremove on accept answers
 - Code clean-up and refactoring

###Alpha Builds

**v0.4.1** (June 24)

 - Updating app to API version 0.9

**v0.4** (June 23)

 - Fixed bug with gzipped API response that broke
   nearly all functionality :)
 - Added Mac OS X build

**v0.3** (June 8)

 - Major UI changes
 - Windows build released and tested
 - Added settings for auto-removing questions
   and changing update interval
 - Shifted application design from a single window
   to a system tray icon
 - Added answer count and asked by fields to question list
 - Clicking on a question title in the window will now open
   the question in the browser
 - Throttling API calls to adhere to new "conscientious use" policy
 - Changed application icon
 - Adding error dialogs for bad input to question URL field
 - Added support for Python 2.5 JSON library
 - Fixed bug related to local time vs GMT
 - Fixed bug where the same question could be tracked multiple times
 - Code clean-up and refactoring
 

**v0.2** (May 28)

 - Added support for other 'Trilogy'
   sites
 - Questions in the list are colored
   based on which site they are from
 - Changed input from question ID to
   question URL
 - Fixed Segmentation Fault when closing
   program
 - Fixed bug where invalid system clock
   could cause multiple notifications
   for same answer/comment
 - Various refactoring and code clean-up

**v0.1** (May 26)

 - Initial build


  [1]: http://i.imgur.com/FWcvp.png
  [2]: http://i.imgur.com/9D3k1.png
  [3]: http://i.imgur.com/HCIgF.png
  [4]: http://github.com/swanson/stacktracker/archives/v1.0
  [5]: http://github.com/downloads/swanson/stacktracker/StackTracker%20v1.0.zip
  [6]: http://github.com/downloads/swanson/stacktracker/StackTracker%20v1.0%20-%20OS%20X.tar.gz
  [7]: http://github.com/swanson/stacktracker

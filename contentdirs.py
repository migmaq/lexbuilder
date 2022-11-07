"""
We allow content directories to be paired with entities by adding #id to the
end of the content directory name.

...

Content directores are scanned in a background thread (they are huge
directories and in the first implementation they will be accessed over
a slow network protocol, so we can't reasonably do it per request).
"""

import time
import re
import os
from itertools import imap
import collections
import config
import util


tagRegex = re.compile (u"#([0-9]+)[ ]*$")

def buildTagToFilenameMap (root, containingDirs, verbose=False):
    """Given a directory name, returns a map of n -> filenames for all filenames
    tagged by ending the filename with a hash sign then an integer (including
    directory names - which is our normal use case.

    For example:   "Ziegler, David #729"

    This is used to associate directories with database entities.

    If a root is supplied, the containingDirs are first resolved relative
    to the root.  The root part is not included in the output resolved dirs.
    """
    idToFilenames = collections.defaultdict (list)
    for containingDir in containingDirs:
        resolvedContainingDir = \
            os.path.join (root, containingDir) if root else containingDir
        for filename in os.listdir(resolvedContainingDir):
            match = tagRegex.search (filename)
            if match:
                idToFilenames[match.group(1)].append (os.path.join (containingDir, filename))


    if verbose:
        print time.ctime (), 'built tag to filename map with', \
            len(idToFilenames), 'entries.'
                    
    return dict(idToFilenames)



tagToFilenameMapService = util.PeriodicallyUpdatedValue (
    task = lambda:buildTagToFilenameMap (config.jobseekerDocRoot,
                                         config.jobseekerDocDirs),
    period = 5.0,
    label = 'Jobseeker id to jobseeker directory')


def startTagToFilenameService ():
    tagToFilenameMapService.start ()

def getTagToFilenameMap ():
    return tagToFilenameMapService.getCurrentValue (errorIfStale=True)

def getFilenamesForTag (tag):
    #print getTagToFilenameMap ()
    return getTagToFilenameMap ().get (tag, [])

def refresh ():
    return tagToFilenameMapService.getCurrentValue (forceRefresh=True)

def test_tagToFilenameService ():
    print getTagToFilenameMap ()
    time.sleep (10.0)

if __name__ == "__main__":
    print buildTagToFilenameMap ('/home/dziegler',
                                 ['data/PQDs - Nursing',
                                  'data/PQDs - MD'])
    test_tagToFilenameService ()


"""
- work out representation of docs for a particular jobseeker.
- make the query/cache thing.
- idea: use similar mechanism to do artifacts for articles etc - less fussy
  than the whole path system - but consider now, because will lead to different
  factoring.

- saudiSunset #28-title #27-title #22-summary.jpg

- for jobseekers, want more of a dir based scheme.
- content pages already have strong urls, just auto create dirs as needed, show
  files in dirs etc etc.
- no need for this tagging

- the API between the layers is that we can get a list of dirs for a jobseeker,
  the rest happens at presentation time.
- if have more than one, show as error at presentation time.

- query can also show possible dir (based on name match) + button to confirm
  (which renames dir + refreshes doc thing)
"""



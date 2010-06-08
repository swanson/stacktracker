from distutils.core import setup
import py2exe
import os, sys

def find_file_in_path(filename):
    for include_path in sys.path:
        file_path = os.path.join(include_path, filename)
        if os.path.exists(file_path):
            return file_path
        
setup(name="StackTracker",
      version="0.3",
      author="Matt Swanson",
      author_email="mdswanso@purdue.edu",
      url="http://stackapps.com/questions/290/",
      license="GNU General Public License (GPL)",
      windows=[{"script": "StackTracker.py"}],
      data_files = [('img', ['img/st_logo.png',
                             'img/stackoverflow_logo.svg',
                             'img/metastackoverflow_logo.svg',
                             'img/serverfault_logo.svg',
                             'img/superuser_logo.svg',
                             ]
                     ),
                    ('imageformats', [
                        find_file_in_path("PyQt4/plugins/imageformats/qsvg4.dll"),
                        find_file_in_path("PyQt4/plugins/imageformats/qjpeg4.dll"),
                        find_file_in_path("PyQt4/plugins/imageformats/qico4.dll"),
                        find_file_in_path("PyQt4/plugins/imageformats/qmng4.dll"),
                        find_file_in_path("PyQt4/plugins/imageformats/qtiff4.dll"),
                        find_file_in_path("PyQt4/plugins/imageformats/qgif4.dll"),]
                     )
                    ],
      options={"py2exe": {"skip_archive": True,
                          "includes": ["sip"],
                          }
               }
      )

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
      windows=[{"script": "StackTracker.py",
                "icon_resources": [(1, "st.ico")]}],
      data_files = [('img', ['img/st_logo.png',
                             'img/stackoverflow_logo.png',
                             'img/metastackoverflow_logo.png',
                             'img/serverfault_logo.png',
                             'img/superuser_logo.png',
                             'img/stackapps_logo.png',
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

import os.path
import simdjson

def createVersionFile(version_file_path):
    with open(version_file_path, 'w') as f:
        short_list = {
            'short-list': [],
            'files': {},
            'name-list': [],
            'fbx-files': {}
        }
        simdjson.dump(short_list, fp=f, indent=4)

def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

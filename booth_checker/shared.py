import os.path
import simdjson

def createVersionFile(version_file_path):
    f = open(version_file_path, 'w')
    
    short_list = {'short-list': [], 'files': {}, 'name-list': []}
    # shortlist = {"short-list": download_url_list, 'files': {}}
    
    # for fileroot in download_url_list:
    #     shortlist['files'][f'{fileroot}'] = {}
    
    simdjson.dump(short_list, fp = f, indent = 4)
    f.close()
    
    
def createFolder(directory):
    try:
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError:
        print ('Error: Creating directory. ' +  directory)

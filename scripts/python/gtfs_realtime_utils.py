import glob
from zipfile import ZipFile
from google.transit import gtfs_realtime_pb2
import time


def log_num_files_parsed(i, total, t1):
    if i % 100 == 0:
        print(f"Parsed {round(i*100 / total)}% of {total} files in {round(time.time() - t1)} seconds.")

def get_gtfs_from_binaries(paths: list):
    entities = []
    total = len(paths)
    assert total > 0, "paths is empty."
    t1 = time.time()

    for i, path in enumerate(paths, 1):
        if path.endswith(".bin"):
            with open(path, 'rb') as f:
                feed = gtfs_realtime_pb2.FeedMessage()
                feed.ParseFromString(f.read())
                entities.extend(feed.entity)
        else:
            print(f"{path} is not a binary file.")
        log_num_files_parsed(i, total, t1)
    return entities

def get_gtfs_entities_from_zips(paths:list, bin_file='gtfsrt.bin'):
    '''
    Get the GTFS-RT entities, from a list of filepaths, as a list.

    Params
    ------
    paths: list
        A list of paths 
    bin_file: str
        The name of the binary file you expect to find in each zip file.
    '''
    entities = []
    total = len(paths)
    assert total > 0, "paths is empty."
    t1 = time.time()
    
    for i, path in enumerate(paths, 1):
        if path.endswith(".zip"):
            with ZipFile(path) as zf:
                if bin_file in zf.namelist():
                    with zf.open(bin_file, 'r') as f:
                        feed = gtfs_realtime_pb2.FeedMessage()
                        feed.ParseFromString(f.read())
                        entities.extend(feed.entity)
                else:
                    print(f'{bin_file} is not contained within {path}. Skipping to next zip file.')
        else:
            print(f"{path} is not a zip file.")
        log_num_files_parsed(i, total, t1)
    return entities

def get_gtfs_entities_from_directory(DIR: str):
    '''
    Get the GTFS-RT entities, from a directory of zip files containing gtfsrt binary files, as a list.

    Params
    ------
    DIR: str
        path to directory containing zip files. May also include other, non-zip files (these are ignored).
    '''
    return get_gtfs_entities_from_zips(glob.glob(DIR + '/*.zip'))

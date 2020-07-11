import sys
import os
import hashlib
import shutil
from collections import defaultdict

# add the path you want to parse in dupecheck function call at bottom for now.

# Todo: fix usage
# usage: in a python terminal, run python DupeFind.py E:/yourpath/someotherpath
# I may have the slashes backwards, I don't remember, python is weird.
# adding support for multiple paths eventually - for path in paths: is broke


# parameters
delete = True  # this will delete the first duplicate found when true
move = False  # this will attempt to move the file to a new folder rather than delete
movepath = "C:\your\path\here" # Strong recommendation to not chose a path script is parsing for dupes

def dupeCheck(paths):

    filesBySize = defaultdict(list)  # files stored in list format
    filesByTinyHash = defaultdict(list)
    filesByFullHash = dict()

    # step 1: crawl thru the directory
    #for path in paths:
    for root, dirs, filenames in os.walk(paths):
        for filename in filenames:
            fullPath = os.path.join(root, filename)
            try:
                fullPath = os.path.realpath(fullPath)
                fileSize = os.path.getsize(fullPath)
            except OSError:
                # catch permission errors, in use, etc.
                continue
            filesBySize[fileSize].append(fullPath)  # where file size is the key, and path is value

    # for all files with same file size, get the hash of their first 1024 bytes
    # this is an arbitrary amount, just the first cycle of the hash function
    for fileSize, files in filesBySize.items():
        if len(files) < 2:
            # if the value is < 2, you can skip because you know it is unique size (not a dupe)
            continue
        for filename in files:
            try:
                tinyhash = get_hash(filename, first_chunk_only=True)
            except OSError:
                # always ready for it to break - possible if permissions change
                continue
            filesByTinyHash[(fileSize, tinyhash)].append(filename)

    # similar to above, take the hash of the full file if the first 1kb matches
    for files in filesByTinyHash.values():
        if len(files) < 2:
            # same as above; it has a unique small hash, so we skip
            continue
        for filename in files:
            try:
                # get the full hash
                fullhash = get_hash(filename, first_chunk_only=False)
            except OSError:
                continue

            # now check for a dupe
            if fullhash in filesByFullHash:
                dupe = filesByFullHash[fullhash]
                print("Duplicate found:\n - %s\n - %s\n" % (filename, dupe))

                if move is True:
                    try:
                        shutil.move(filename, movepath)
                    except shutil.Error as err:
                        print("deleting since already exists: %s\n" % filename)
                        print(err)
                        pass
                elif delete is True:
                    # May be possible that you don't have permissions and this could cause a crash
                    os.remove(filename)
            else:
                filesByFullHash[fullhash] = filename
    folder_cleanup(paths)


def folder_cleanup(paths):
    for root, dirnames, filenames in os.walk(paths, topdown=False):
        for dirname in dirnames:
            try:
                fullPath = os.path.join(root, dirname)
                os.rmdir(fullPath)
                print("Deleted %s \n" % fullPath)
            except OSError:
                print("not an empty folder: %s .. skipping.." % dirname)
                pass


def get_hash(filename, first_chunk_only=False, hash_algo=hashlib.sha1):
    hashobj = hash_algo()
    with open(filename, "rb") as f:
        if first_chunk_only:
            hashobj.update(f.read(1024))
        else:
            for chunk in chunk_reader(f):
                hashobj.update(chunk)
    return hashobj.digest()


def chunk_reader(fobj, chunk_size=1024):
    """ Generator that reads a file in chunks of bytes """
    while True:
        chunk = fobj.read(chunk_size)
        if not chunk:
            return
        yield chunk


if __name__ == "__main__":
    dupeCheck("H:\Plex")
    if sys.argv[1:]:
        # dupeCheck(sys.argv[1:])
        print("dupe checking time!")
        # dupeCheck("H:\Plex")
    else:
        print("Usage: %s <folder> [<folder>...]" % sys.argv[0])
#!/usr/bin/env python

from __future__ import print_function
import os
import re
import argparse
import functools
import shutil
import tarfile
from threading import Thread
from random import randint

LOG_HOME = '/var/log'
MONITOR_DIRECTORY = [LOG_HOME]
QUEUE_TASKS = []

# Argument Parser
parser = argparse.ArgumentParser()
parser.add_argument('-a', metavar='apps', type=str,
                    help='Additional Application Log Directories to Cleanup',
                    required=False)

parser.add_argument('-e', metavar='exclude', type=str,
                    help='Exclude directories from analysis',
                    required=False)

args = parser.parse_args()


class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class AsyncManager(Thread):
    def __init__(self):
        Thread.__init__(self)

    @classmethod
    def get(cls):
        if len(QUEUE_TASKS) > 0:
            return QUEUE_TASKS.pop()
        else:
            raise IndexError('No more directories')

    def run(self):
        while True:
            try:
                task_directory = AsyncManager.get()
            except IndexError:
                print("No More Directories in Queue")
                break

            print("Beginning new Task on Directory {}\n".format(task_directory))
            try:
                print(assess_directory_structure(task_directory))
            finally:
                print("Sucessfully retrieved directory from Queue\n")


class DeepRecurse(object):

    @classmethod
    def recurse(cls, directory):
        d_tree = []
        for root, dirs, file in os.walk(directory):
            for fd in file:
                if os.path.islink(os.path.join(directory, fd)):
                    continue
                d_tree.append(os.path.join(directory, fd))
        # d_tree is a list of files including absolute path
        return d_tree

    @classmethod
    def screen(cls, file_list):
        screened_files = []
        if not isinstance(file_list, list):
            file_list = list(file_list)
        
        for file in file_list:
            if not file[-2:] == 'gz':
                continue
            screened_files.append(file)
        return screened_files


def get_directory_size(directory):
    total = 0

    def recurse(path):
        deep_total = 0
        checklist = DeepRecurse.recurse(path)
        if not all(map(os.path.exists, checklist)):
            for index, file in enumerate(checklist):
                if not os.path.exists(file):
                    # remove the file that does not exists to prevent script from exiting
                    print(bcolors.OKBLUE+"Removing File {} From the Recursive Checklist".format(file)+bcolors.ENDC)
                    del(checklist[index])
        try:
            deep_total += sum(map(os.path.getsize, checklist))
        except OSError:
            pass

        return deep_total

    for inode in map(functools.partial(os.path.join, directory),
        os.listdir(directory)):

        if (args.e is not None) and (inode in args.e):
            print(bcolors.OKBLUE+"Removing {} Because it was excluded!".format(inode)+bcolors.ENDC)
            continue
        if os.path.isdir(inode):
            print(bcolors.OKGREEN+"{} is a Directory, further recursion required to get Size.".format(inode)+bcolors.ENDC)
            total += recurse(inode)
            continue
        total += os.path.getsize(inode)
    return total


def assess_directory_structure(directory):
    rotation_files = []
    ARCHIVE_NAME = '{}_'.format(str(randint(1,9))) + 'zipped_log_archive.tar'
    # TODO use coroutines/asyncio to thread this behavior
    # Tasks assigned to each iteration should be run asynchronously 
    check_free = map(get_directory_size, ['/alldata', directory])

    # Make sure there is enough space
    if (check_free[0] > 0) and (not (check_free[0] - check_free[1]) >\
        (check_free[1] / 2)):
        raise OSError(bcolors.FAIL+'Not Enough Free Space in {}\n {} Exists in {}, however {} exists in {}'.format(
            '/alldata', check_free[1], directory, check_free[0], '/alldata')+bcolors.ENDC)

    # Screen for the files that we want
    for inode in map(functools.partial(os.path.join, directory),
        os.listdir(directory)):

        if os.path.isdir(inode):
            print(bcolors.OKGREEN+"{} is a Directory, further recursion required to target Files.".format(inode)+bcolors.ENDC)
            if inode in args.e.split():
                print(bcolors.OKBLUE+"Skipping the Directory {} because it belongs to the Exclusion list".format(
                    inode)+bcolors.ENDC)
                continue
            rotation_files = rotation_files + DeepRecurse.recurse(inode)
            continue
        rotation_files.append(inode)

    work_queue = set(rotation_files).intersection(set(DeepRecurse.screen(rotation_files)))
    if not os.path.exists('/alldata/temporary_log_cleaning'):
        os.mkdir('/alldata/temporary_log_cleaning')

    print(bcolors.OKGREEN+"Transferring {} Files to {}".format(len(work_queue), '/alldata/temporary_log_cleaning')+bcolors.ENDC)
    for zip_file in work_queue:
        shutil.move(zip_file, '/alldata/temporary_log_cleaning')

    # Make uncompressed tar archive, individual files are already compressed
    # if os.path.exists(os.path.join('/alldata/temporary_log_cleaning', ARCHIVE_NAME)):
    #     print(bcolors.UNDERLINE+"Archive {} already exists, Prepending random digit to Archive Name".format(ARCHIVE_NAME)+bcolors.ENDC)
    #     ARCHIVE_NAME = '{}_'.format(str(randint(1,9))) + ARCHIVE_NAME
    
    with tarfile.open(os.path.join('/alldata/temporary_log_cleaning', ARCHIVE_NAME), 'w') as tar:
        for file in map(functools.partial(os.path.join, '/alldata/temporary_log_cleaning'),
            os.listdir('/alldata/temporary_log_cleaning')):
            print(bcolors.WARNING+"Adding {} to Archive {}".format(file, os.path.join('/alldata/temporary_log_cleaning', ARCHIVE_NAME))+bcolors.ENDC)
            # Add files to archive
            tar.add(file)
        tar.close()
    
    print(bcolors.OKGREEN+"Files Successfully added to archive {}".format(ARCHIVE_NAME)+bcolors.ENDC)
    print(bcolors.OKGREEN+"Moving Archive {} to {} root, and deleting the temp directory {}".format(
        ARCHIVE_NAME, '/alldata', 'temporary_log_cleaning')+bcolors.ENDC)
    
    shutil.move(os.path.join('/alldata/temporary_log_cleaning', ARCHIVE_NAME), '/alldata')
    clean_decision = raw_input(bcolors.OKGREEN+"The {} tar Archive has been created, and is {} bytes in size.\
        Would you like to delete the original zip files (y/n)?".format(
            ARCHIVE_NAME, os.stat(os.path.join('/alldata/', ARCHIVE_NAME)).st_size)+bcolors.ENDC)


    while clean_decision.lower() not in ['y','yes','no','n']:
        clean_decision = raw_input(bcolors.OKGREEN+"The {} tar Archive has been created, and is {} bytes in size.\
            Would you like to delete the original zip files (y/n)?".format(
                ARCHIVE_NAME, os.stat(os.path.join('/alldata/', ARCHIVE_NAME)).st_size)+bcolors.ENDC)

    if clean_decision.lower() in ['y', 'yes']:
        print(bcolors.OKGREEN+"Deleting Original Zip File Copies!"+bcolors.ENDC)
        for file in os.listdir('/alldata/temporary_log_cleaning'):
            shutil.os.remove(file)

    shutil.os.rmdir('/alldata/temporary_log_cleaning')

    print(bcolors.WARNING+"Creating Symbolic Link!"+bcolors.ENDC)
    start = 'a'
    try:
        shutil.os.symlink(os.path.join('/alldata/', ARCHIVE_NAME), '/var/log/old_logs_archive_{}'.format(a))
    except OSError:
        shutil.os.symlink(os.path.join('/alldata/', ARCHIVE_NAME), '/var/log/old_logs_archive_{}'.format(
            chr(ord(start) + 1)))
    
    print(bcolors.OKBLUE+"Log Directory Cleanup is Complete.  Please check {} for Symbolic link!".format('/var/log')+bcolors.ENDC)

if __name__ == "__main__":
    if args.a is not None:
        MONITOR_DIRECTORY.append(args.a)

    for directory in MONITOR_DIRECTORY:
        QUEUE_TASKS.append(directory)
    
    # 1 Thread for every directory that we will monitor
    # By default /var/log will be monitored, use -a to monitor additional directories
    for tcount in range(len(MONITOR_DIRECTORY)):
        thread = AsyncManager()
        # thread.daemon = True
        thread.start()

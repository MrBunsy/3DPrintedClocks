from pathlib import Path
import argparse
from multiprocessing import Pool
import multiprocessing
from .cuckoo_bits import *

def whistle_jobs():
    jobs = []

    for size in [65,70,80,100]:
        job = lambda :
        whistleObj = Whistle(size)
        whistle = whistleObj.getWholeWhistle()
        whistle_top = whistleObj.getWhistleTop()
        whistle_full = whistleObj.getWholeWhistle(True)
        bellow_base = whistleObj.getBellowBase()
        bellow_top = whistleObj.getBellowTop()


    return jobs

def executeJob(job):


if __name__ == "__main__":
    '''
    Regenerate various bits of clock
    Mostly copy/pasted from 3DPrintedTrains generate.py
    '''

    options = {"whistles": lambda: whistle_jobs(),
               }

    parser = argparse.ArgumentParser(description="Generate all variants of a parametric object")
    for opt in options.keys():
        parser.add_argument("--{}".format(opt), action='store_true')

    args = parser.parse_args()
    jobs = []

    all = True
    for opt in options.keys():
        # https://stackoverflow.com/questions/43624460/python-how-to-get-value-from-argparse-from-variable-but-not-the-name-of-the-var
        if vars(args).get(opt):
            all = False

    for opt in options.keys():
        if vars(args).get(opt) or all:
            jobs.extend(options[opt]())

    p = Pool(multiprocessing.cpu_count() - 1)
    p.map(executeJob, jobs)
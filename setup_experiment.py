#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import os


SETUP_FILE = "./setup.json"
LOG_FILE = "./text_entry_log.csv"


def main():
    try:
        participant_id = int(sys.argv[1])
    except IndexError as e:
        print("No participant_id given as command line parameter! Starting with id 1")
        participant_id = 1

    while True:
        exit_code = os.system(f"python3 text_entry_speed_test.py {participant_id} {SETUP_FILE} >> {LOG_FILE}")
        participant_id = participant_id + 1
        if exit_code != 0:
            # something went wrong; abort mission!
            # This is also used as a "hack" to exit this while loop from the called python program by calling exit(1)
            break


if __name__ == '__main__':
    main()

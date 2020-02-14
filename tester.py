#!/usr/bin/env python3

import shlex
import argparse
import os
from subprocess import Popen, PIPE, STDOUT, check_output, getstatusoutput
import copy
import logging
from bash import bash
from io import StringIO
import subprocess


import yaml

TIMEOUT = 60
# FORMAT = '%(asctime)-15s %(clientip)s %(user)-8s %(message)s'
# logging.basicConfig(format=FORMAT)

# create logger
logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)

# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)


def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("target_file_path",
                        help="Path to file containing targets/hostnames")
    parser.add_argument("config_file_path",
                        help="Path to file containing tester configuration")

    args = parser.parse_args()
    config = return_config(args.config_file_path)
    targets = return_targets(args.target_file_path)
    if run_tests(config, targets):
        return 0
    return 1


def return_config(config_path):
    with open(config_path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def return_targets(target_path):
    with open(target_path) as file:
        content = file.readlines()
    return [x.strip() for x in content]

# Need to


def run_tests(config, targets):
    env = dict(os.environ)
    passed = True
    print("Config file: " + config["configName"] + "\n")
    for target in targets:
        print("\nRunning tests for target: " + target + "\n")
        for test in config["tests"]:
            print("Running test " + test["testName"] +
                  " for target: " + target + ": ", end="")
            # command = env["SHELL"] + " -c \"" + test["execString"] + "\""
            command = test["execString"]
            commandEnv = copy.copy(env)
            commandEnv["TARGET"] = target

            try:
                process = subprocess.Popen(
                    command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                output, errors = process.communicate()
                log_subprocess_output(output)
            except (OSError, subprocess.CalledProcessError) as exception:
                logging.info('Exception occured: ' + str(exception))
                logging.info('Subprocess failed')
                return False
            else:
                # no exception was raised
                logging.info('Subprocess finished')
            # response = run(command, commandEnv)
            # if response != 0:
            #     print("failed")
            #     passed = False
            # else:
            #     print("passed")
    return True


# def run(cmd, env=os.environ, stdout=PIPE, stderr=STDOUT, timeout=TIMEOUT, **kwargs):
#     print("running command: " + cmd)

#     process = Popen(
#         cmd, shell=True, stdout=stdout, stderr=stderr, env=env)
#     status, output = getstatusoutput(cmd)
#     logging.info(output)
#     # with process.stdout:
#     #     log_subprocess_output(process.stdout)
#     # code = process.wait()
#     return status


def log_subprocess_output(pipe):
    for line in iter(pipe.readline, b''):  # b'\n'-separated lines
        logging.info('got line from subprocess: %r', line)

# class ShellExec(object):
#     """Intended to be used as a method."""

#     def __init__(self, *args, **kwargs):
#         self.p = None
#         self.stdout = None
#         self.run(*args, **kwargs)
#         self.code = None
#         self.stdout = None
#         self.stderr = None

#     def run(self, cmd, env=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=TIMEOUT, sync=True):
#         self.p = subprocess.Popen(
#             cmd, shell=True, stdout=stdout, stdin=subprocess.PIPE, stderr=stderr, env=env
#         )

#         if sync:
#             self.sync(timeout)
#         return self

#     def sync(self, timeout=None):
#         kwargs = {'input': self.stdout}
#         if timeout:
#             kwargs['timeout'] = timeout
#         self.stdout, self.stderr = self.p.communicate(**kwargs)
#         self.code = self.p.returncode
#         return self

#     def __repr__(self):
#         return self.value()

#     def __unicode__(self):
#         return self.value()

#     def __str__(self):
#         return self.value()

#     def __nonzero__(self):
#         return self.__bool__()

#     def __bool__(self):
#         return bool(self.value())

#     def value(self):
#         if self.stdout:
#             return self.stdout.strip().decode(encoding='UTF-8')
#         return ''


main()

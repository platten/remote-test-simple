
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test runner.

This script takes in a file with a list of host targets, and a YAML file with
a list of tests to run against each one of the target hosts and then executes
the tests. It will return 0 if all the tests passed or 1 if one of them failed.


Todo:
    * Process output from STDOUT from process goes to logger.info (STDOUT)
    * Process output from STDERR from process goes to logger.error (STDERR)
    * Support timeout
    * Support config defaults (If not provided. Include PATH, ENV, SHELL, etc)
    * Support test specific overrides (Path, ENV, etc)
    * Support multiple configs
    * Support mapping of configs to hosts

.. _Google Python Style Guide:
   http://google.github.io/styleguide/pyguide.html

"""

import argparse
import os
import copy
import logging
import subprocess

import yaml

logger = logging.getLogger('simple_example')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)


def main():
    """
    Main.
    """
    # setup_logger()
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


# def setup_logger():
#     """
#     Configure logger.
#     """
#     logger = logging.getLogger('simple_example')
#     logger.setLevel(logging.DEBUG)
#     ch = logging.StreamHandler()
#     ch.setLevel(logging.DEBUG)
#     formatter = logging.Formatter(
#         '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#     ch.setFormatter(formatter)


def return_config(config_path):
    """Return Python object describing tests and execution parameters.

    Args:
        config_path (str): Path to the configuration file.

    Returns:
        dict: Dictionary containing configuration and list of tests.

    """
    with open(config_path) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def return_targets(target_path):
    """Return list of targets to scan.

    Args:
        target_path (str): Path to the target file.

    Returns:
        list: List containing target hosts.

    """
    with open(target_path) as file:
        content = file.readlines()
    return [x.strip() for x in content]


def run_tests(config, targets):
    """Run tests defined in configuration on each one of the targets.

    Args:
        config (dict): Python dict containing configuration.
        targets(list): List of host targets.

    Returns:
        bool: Whether the tests failed or passed for the targets provided.

    """
    env = dict(os.environ)
    passed = True
    print("Config file: " + config["configName"] + "\n")
    for target in targets:
        print("\nRunning tests for target: " + target + "\n")
        for test in config["tests"]:
            print("Running test " + test["testName"] + " for target: " +
                  target + ": ",
                  end="")
            # command = env["SHELL"] + " -c \"" + test["execString"] + "\""
            command = test["execString"]
            commandEnv = copy.copy(env)
            commandEnv["TARGET"] = target

            try:
                process = subprocess.Popen(command,
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE)
                output, errors = process.communicate()
                print(output)
                log_subprocess_output(output)
                if process.returncode != 0:
                    passed = False
            except (OSError, subprocess.CalledProcessError) as exception:
                logger.info('Exception occured: ' + str(exception))
                print('Exception occured: ' + str(exception))
                logger.info('Subprocess failed')
                return False
            else:
                logging.info('Subprocess finished')
    return passed


def log_subprocess_output(pipe):
    """Log output from pipe.

    Args:
        pipe (subprocess.PIPE): PIPE object
    """
    new = pipe.decode('utf-8')
    for line in new:  # b'\n'-separated lines
        print('got line from subprocess: %r', line)
        logger.info('got line from subprocess: %r', line)


main()

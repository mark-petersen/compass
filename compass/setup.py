import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description='Set up one or more test cases')
    args = parser.parse_args(sys.argv[2:])

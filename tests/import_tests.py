# test@custom example with a bunch of imports

import diffusers
import transformers
import torch
import tensorflow
import cv2

import os
import sys
import re
import logging
import datetime
import json
import random
import math
import functools

from parser import NodeBase


class ImportTests(NodeBase):
    """ImportTests: Test heavy module imports."""
    label = "ImportTests"
    description = "Tests heavy module imports such as diffusers and others."
    category = "import"
    execution_type = "single"
    
    def execute(self):
        # Since heavy imports are done at module level, this simply confirms they load properly.
        return "All heavy imports have been successfully imported."


def main():
    test = ImportTests()
    result = test.execute()
    print('Hello from test@custom. ' + result)


if __name__ == "__main__":
    main() 
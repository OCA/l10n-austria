#!/usr/bin/env python3
import os
import json
import logging


_logger = logging.getLogger(__name__)


class DepCompare():
    """ Compare DEP files"""

    def load(self, path):
        """ load dep file or directory with dep files"""
        if os.path.isfile(path):
            with open(path, "r", encoding="utf8") as f:
                return json.load(f)
        else:
            files = sorted([os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f)) and f.endswith(".json")])
            rows = []
            dep = {
                "Belege-Gruppe": [
                    {
                        "Signaturzertifikat" : "",
                        "Zertifizierungsstellen" : [],
                        "Belege-kompakt" : rows
                    }
                ]
            }
            for dep_path in files:
                with open(dep_path, "r", encoding="utf8") as dep_file:
                    partly_dep = json.load(dep_file)
                    rows += partly_dep["Belege-Gruppe"][0]["Belege-kompakt"]
            return dep

    def compare_obj(self, obj1, obj2):
        """ compare objects """
        obj1_str = json.dumps(obj1, indent=4, sort_keys=True)
        obj2_str = json.dumps(obj2, indent=4, sort_keys=True)
        return obj1_str == obj2_str


    def compare(self, path1, path2):
        """ compare file/dir with json with path2 file/dir with json """
        dep1 = self.load(path1)
        dep2 = self.load(path2)
        return self.compare_obj(dep1, dep2)

if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="DEP Protocol Compare/Checker")
    parser.add_argument("path1", help="First Source File/Directory")
    parser.add_argument("path2", help="Second Source File/Directory")

    args = parser.parse_args()
    res = DepCompare().compare(args.path1, args.path2)
    if res:
        _logger.info("Files are EQUAL")
    else:
        _logger.error("Files are NOT equal")


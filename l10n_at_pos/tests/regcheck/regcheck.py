import os
import logging
import json
import shutil
import subprocess

_logger = logging.getLogger(__name__)


class RegCheckerError(Exception):
    """ Base class for all exceptions during the check """


class RegChecker():
    """Checks the DEP protocol """

    def __init__(self, check_dir, crypto_config=None,
                 dep_file="dep.json", result_dir="result"):
        """ initialize the checker """
        self.check_dir = check_dir
        self.crypto_config = crypto_config
        self.dep_file = dep_file
        self.crypto_config_file = os.path.join(self.check_dir, "crypto_config.json")
        self.result_dir = result_dir
        self.checker_path = os.path.join(
            os.path.abspath(os.path.dirname(__file__)),
            "regkassen-verification-1.1.1"
        )
        self.checker_jar = "regkassen-verification-depformat-1.1.1.jar"
        self.result = None

    def check(self, dep=None):
        """ run the check
            :param dep: the DEP object to check, could also be empty,
                        then the path of the dep file is used
            :return: True if check was successful, False otherwise
        """

        # ensure workging directory
        if not os.path.exists(self.check_dir):
            os.makedirs(self.check_dir)
            _logger.info("Created check directory %s", self.check_dir)

        # write crypto config
        with open(self.crypto_config_file, "w", encoding="utf8") as f:
            json.dump(self.crypto_config, f, indent=4, sort_keys=True)


        # check dep file
        dep_path = (os.path.join(self.check_dir, self.dep_file)
                if not os.path.isabs(self.dep_file)
                else self.dep_file)

        # if there is an dep object,
        # write it down
        if dep:
            with open(dep_path, "w", encoding="utf8") as f:
                json.dump(dep, f, indent=4, sort_keys=True)

        # ensure a fresh result directory
        result_path = os.path.join(self.check_dir, self.result_dir)
        if os.path.exists(result_path):
            shutil.rmtree(result_path)
        os.makedirs(result_path)

        # ensure if check exists
        if not os.path.exists(self.checker_path):
            raise RegCheckerError(f"Could not find checker at {self.checker_path}")

        # run the chec
        cmd = [
            "java",
            "-Xmx100m -XX:ReservedCodeCacheSize=64m -XX:-UseCompressedClassPointers -Xss256k",
            "-jar", self.checker_jar,
            "-v", "-f",
            "-i", dep_path,
            "-c", self.crypto_config_file,
            "-o", result_path
        ]
        cmd = " ".join(cmd)
        res = subprocess.call(
           cmd
        , shell=True, cwd=self.checker_path)

        # return true if check was successful
        with open(os.path.join(result_path, "DEP-global.json"), "r", encoding="utf-8") as f:
            self.result = json.load(f)

        return res == 0 and self.result["verificationState"] == "PASS"

import os
import glob
import logging
import subprocess


class BarCodeReader():
    command = "java -jar"
    lib = ""

    def __init__(self):
        res = glob.glob(
            "zxing/javase/target/javase-*-jar-with-dependencies.jar")
        if res:
            self.lib = res[0]
        else:
            logging.error("Haven't compiled zxing correctly.")
        # TODO: support download compiled jar file
        # with urllib.request.urlopen(jar_url) as resp, open(jar_path, 'wb') as out:
        #     shutil.copyfileobj(resp, out)

    def decode(self, filename):
        if not os.path.exists(filename):
            logging.error("File dose not exist!")
            return None
        cmd = ' '.join([self.command, self.lib, filename])
        (stdout, _) = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, universal_newlines=True).communicate()
        return stdout

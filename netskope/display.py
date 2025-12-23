import os
# import argparse
import pdb
import sys
import time
import subprocess

class Display():

    @classmethod
    def status(cls, print_to_screen=True):
        cmds = [
            "sc query epdlp",
            "sc query epdlpdrv",
        ]

        output = ""
        for cmd in cmds:
            msg = os.popen(cmd).read()
            # if print_to_screen:
            #     print(msg)
            # else:
            #     output+=msg
            print(msg)
            output+=msg
        # if not print_to_screen:
        #     return output
        return output

    @classmethod
    def epdlp_running(cls, print_to_screen=True):

        msg = os.popen("sc query epdlp").read()
        if "RUNNING" in msg:
            return True
        else:
            return False

    @classmethod
    def what(cls):
        print("what")

    @classmethod
    def policy(cls):
        path = "C:\\ProgramData\\netskope\\EPDLP\\policy"
        last_update = time.ctime(os.path.getmtime(path))

        print(f"last update time = {last_update}")


    @classmethod
    def epdlpdrv_running(cls, print_to_screen=True):

        msg = os.popen("sc query epdlpdrv").read()
        if "RUNNING" in msg:
            return True
        else:
            return False

    @classmethod
    def version(cls, print_to_screen=True):

        # for Windows 10
        # for Windows 11 23H2 and below
        cmd = "wmic product get name, version | findstr \"Netskope Client\""
        process = subprocess.Popen(cmd,
                                   shell=True,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # for Windows 11 24H2 and above
        # - wmic is no longer supported in Windows 11 starting 24H2 (23H2 still works), else we would be getting below
        #   C:\Users\chlin>wmic
        #   'wmic' is not recognized as an internal or external command, operable program or batch file.
        if stderr.decode() != "":
            # fallback is to use powershell version of wmic
            cmd = "Get-CimInstance -ClassName 'Win32_Product' -Filter 'NAME LIKE \"%Netskope%\"' | Select -ExpandProperty 'Version'"
            results = subprocess.run(["powershell", "-Command", cmd], capture_output=True)
            version = results.stdout.decode().strip()
        else:
            version = stdout

        if print_to_screen:
            print(version)

        return version.decode()


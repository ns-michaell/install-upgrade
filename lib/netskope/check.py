import os
# import argparse
import sys
import time
import pdb

# =======================================================
# this has been deprecated, pleaes do not use
# instead, please use "display.py" module
#
# why? because if used, this might conflict some preserved words for "check"
# ex: when importing from "Check" classmethod, only "status", and "version" are available for use
#     anything else, such as "epdlp_running", "epdlpdrv_running", and "policy" won't be available for use
# =======================================================

class Check():

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
            #     output+=msgs
            #print(msg)
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
    def epdlpdrv_running(cls, print_to_screen=True):

        msg = os.popen("sc query epdlpdrv").read()
        if "RUNNING" in msg:
            return True
        else:
            return False

    @classmethod
    def version(cls, print_to_screen=True):
        cmd = "wmic product get name, version | findstr \"Netskope Client\""

        output = ""
        output = os.popen(cmd).read()
        # if print_to_screen:
        #     print(output)
        # else:
        #     return output

        return output

    @classmethod
    def policy(cls):

        path = "C:\\ProgramData\\netskope\\EPDLP\\policy"
        last_update = time.ctime(os.path.getmtime(path))
        msg = f"last update time = {last_update}"

        path = "C:\\ProgramData\\netskope\\EPDLP\\policy\\fingerprint"
        fd = open(path,"r")
        fingerprint = fd.read()
        fd.close()
        msg += f"fingerprint = {fingerprint}"

        return msg




import os
import subprocess

class Service():

    @classmethod
    def runCmd(*args):
        p = subprocess.Popen(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        out, error = p.communicate()
        return out, error


    @classmethod
    def stop(cls):
        cmds = [
            "sc stop epdlp",
            "sc stop epdlpdrv",
        ]

        for cmd in cmds:
            ps_command = f"& {{Start-Process cmd.exe -argumentlist '/k \"{cmd}\"' -Verb Runas}}"
            command = ['powershell.exe', '-command', ps_command]
            cls.runCmd(command)


    @classmethod
    def start(cls):
        cmds = [
            "sc start epdlp",
            "sc start epdlpdrv",
        ]

        for cmd in cmds:
            ps_command = f"& {{Start-Process cmd.exe -argumentlist '/k \"{cmd}\"' -Verb Runas}}"
            command = ['powershell.exe', '-command', ps_command]
            cls.runCmd(command)
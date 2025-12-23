import subprocess
# import argparse
import sys
import yaml
import pdb
import os
import time
import glob
# example taken from https://locall.host/how-to-run-a-powershell-command-in-python/

# msi = "NSClient_addon-epdlp-tenant00.stg.boomskope.com_1303_yoz9g5aVZ2sv2730B790_f6Nj6L7icQfA5OUeHlv6J7xOh4Ds11E03licW9ll_.msi"
# msi_install = f"C:\\Users\\vagrant\\Documents\\123.0.0.5699\\{msi}"
# msi_upgrade = f"C:\\Users\\vagrant\\Documents\\123.0.0.release\\{msi}"

SIGNTOOL_LOCATION = "C:\\Program Files (x86)\\Windows Kits\\10\\bin\\10.0.19041.0\\x64\\signtool.exe"


class Installer():

    logfile = "installer.log"

    @classmethod
    def installer(cls, file_path, operation, logfile):
        # file_path looks like C:\\testing\\binaries\\124.0.0.2283\\NSClient_addon-sjc1-datasecurity-ep.goskope.com_14989_S39jdnjr05OqZ6DK78Ef_9Sxqwb6Lnr00SnUmZ6JGm8qxm7G6kYndD3rc7qEX_.msi'
        current_dir = file_path.split("binaries")[0]
        installer_log_path = os.path.join(current_dir, logfile)

        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                f'Measure-Command {{ Start-Process -Verb RunAs msiexec -ArgumentList "/{operation} {file_path} /qn /L*V {installer_log_path}" -Wait }}'
            ],
            capture_output = True,
            text = True
        )
        # print(result.stdout)

        if result.returncode == 0:
            # print("Powershell command executed successfully.")
            stdout = result.stdout
            print(stdout)
            return stdout
        else:
            print("An error occurred during Powershell command execution.")
            print(result.stderr)


    @classmethod
    def grant_permission(cls):

        permission_file = "grant_permission.bat"

        # create grant_permission.bat
        # notice the last line "exit 0" is to close the pop-up cmd window
        # without it, there would be many annoying pop-up cmd windows
        contents = """
takeown /f "C:\\ProgramData\\netskope\\EPDLP" /r /d y
icacls "C:\\ProgramData\\netskope\\EPDLP" /grant Administrators:(OI)(CI)(RX,W)
takeown /f "C:\\ProgramData\\netskope\\EPDLP-Persistent-Cache" /r /d y
icacls "C:\\ProgramData\\netskope\\EPDLP-Persistent-Cache" /grant Administrators:(OI)(CI)(RX,W)
exit 0
"""
        fd = open(permission_file, "w")
        fd.write(contents)
        fd.flush() # better to flush it; otherwise, we could get partial contents
        fd.close()

        # execute the script with elevated mode
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                f"& {{ Start-Process cmd.exe -Verb RunAs -argumentlist '/k \"C:\\testing\\{permission_file} /qn \"'}}"
            ],
            capture_output = True,
            text = True
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("An error occurred during Powershell command execution.")
            print(result.stderr)

        # remove
        # os.remove(permission_file)


    @classmethod
    def local_config(cls, features):

        config_file = "local_config.json"

        # create local_config.json
        if features is None:
            contents = """
{
    "GSLBServiceHost": "polaris-steering-api.netskope.io",
    "LogLevel": "debug",
    "PolicyUpdateFrequency": 30,
    "EnableMemoryDump": "true"
}
"""
        else:
            '''
            lines = ""
            for i, feature in enumerate(features):
                if feature == "BAC":
                    if i == len(features) - 1:
                        lines += '"EnableBrowserApplicationControl": true'
                    else:
                        lines += '"EnableBrowserApplicationControl": true,\n'
                elif feature == "NFSCC":
                    if i == len(features) - 1:
                        lines += '"EnableNetworkContentControl": true'
                    else:
                        lines += '"EnableNetworkContentControl": true,\n'
            pdb.set_trace()
            contents = """
{
    "GSLBServiceHost": "polaris-steering-api.netskope.io",
    "LogLevel": "debug",
    "PolicyUpdateFrequency": 30,
    "EnableMemoryDump": "true",
    {lines}
}
""".format(lines=lines)
        '''
            contents = """
{
    "GSLBServiceHost": "polaris-steering-api.netskope.io",
    "LogLevel": "debug",
    "PolicyUpdateFrequency": 30,
    "EnableMemoryDump": "true",
    "EnableBrowserApplicationControl": true,
    "EnableNetworkContentControl": true
}
"""

        fd = open(config_file, "w")
        fd.write(contents)
        fd.flush() # better to flush it; otherwise, we could get partial contents
        fd.close()

        # move local_config.json to the config folder
        cmd = f"copy {config_file} C:\\ProgramData\\netskope\\EPDLP\\config\\"
        stdout, stderr = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True, # without it, on Chinese Windows 10, we would run into below
                                       #"UnicodeDecodeError: 'utf-8' codec can't decode byte 0xbd in position 0: invalid start byte"
                            shell=True).communicate()

        return stdout.strip(), stderr.strip()


    @classmethod
    def install(cls, file_path, logfile=logfile):

        return cls.installer(file_path, operation="i", logfile=logfile)


    @classmethod
    def configure(cls, features="ALL"):

        for i in range(10):                     # without retry, it would not work for the 1st time
            cls.grant_permission()              # since it's just too fast for permission granting to catchup
            stdout, stderr = cls.local_config(features) # so usually, it would work at the 3rd or 4th try

            if stderr == "" and "1 file(s) copied" in stdout:
                print("grant permission to EPDLP folder successed, local_config.json placed")
                break
            else:
                print(f'stdout="{stdout}", stderr="{stderr}"')
                print("wait for 5 seconds, and try grant permission, and move local_config.json again")
                time.sleep(5)

    @classmethod
    def enablevhd(cls):

        enablevhd_file = "enablevhd.bat"

        # create bat file
        contents = """
REG ADD HKLM\\SOFTWARE\\NetSkope\\EPDLP\\config /v EnableVHDContentControl /t REG_DWORD /d \"1\"
exit 0"
"""
        fd = open(enablevhd_file, "w")
        fd.write(contents)
        fd.flush() # better to flush it; otherwise, we could get partial contents
        fd.close()

        # execute the script with elevated mode
        result = subprocess.run(
            [
                "powershell.exe",
                "-ExecutionPolicy", "Bypass",
                f"& {{ Start-Process cmd.exe -Verb RunAs -argumentlist '/k \"C:\\testing\\{enablevhd_file} /qn \"'}}"
            ],
            capture_output = True,
            text = True
        )
        if result.returncode == 0:
            print(result.stdout)
        else:
            print("An error occurred during Powershell command execution.")
            print(result.stderr)


    @classmethod
    def uninstall(cls, file_path, logfile="installer-uninstall.log"):

        cls.installer(file_path, operation="x", logfile=logfile)


    @classmethod
    def get_files_processed(cls, folder, enforce_looking_epdlp=False):

        files = glob.glob(f"{folder}\\**", recursive=True)

        files_processed = []
        for file in files:
            if os.path.isfile(file):
                # print(file)
                file_extention = file.split(".")[-1]
                if "dll" in file_extention or \
                    "exe" in file_extention or \
                    "sys" in file_extention or \
                    "api" in file_extention:

                    if enforce_looking_epdlp:
                        if "epdlp" in file:
                            files_processed.append(file)
                    else:
                        files_processed.append(file)

        return files_processed


    @classmethod
    def check_binary_signed(cls, files):
        files_not_signed = []
        files_not_signed_by_us = []

        for file in files:
            # =====================================
            # check point to see if the binary is signed
            # =====================================

            cmd = f"\"{SIGNTOOL_LOCATION}\" verify /pa \"{file}\""
            # print(cmd)
            process = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
            stdout, stderr = process.communicate()
            if "Successfully verified" in stdout.decode():
                pass
            elif stderr.decode() != "":
                files_not_signed.append(file)
                continue


            # =====================================
            # check point to see if the binary is signed by us (optional)
            # =====================================

            cmd = f"\"{SIGNTOOL_LOCATION}\" verify /pa /v \"{file}\""
            # print(cmd)
            process = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
            stdout, stderr = process.communicate()
            if "netSkope" in stdout.decode():
                pass
            else:
                files_not_signed_by_us.append(file)

        return files_not_signed, files_not_signed_by_us


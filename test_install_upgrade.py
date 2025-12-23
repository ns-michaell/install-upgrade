import pdb
import os
import subprocess
import requests
import pytest
import yaml
import time
import re
import glob
import datetime
import sys
import pyautogui
import pygetwindow as gw
from display import Display
from installer import Installer
from fetcher import download, get_downloadable_url, get_binary_version
from client import Client


# ==========================================================================
# it covers
# - C1655099 https://netskope.testrail.io/index.php?/cases/view/1655099 current-2 > released build
# - C1655100 https://netskope.testrail.io/index.php?/cases/view/1655100 current-1 > released build
# - C1655101 https://netskope.testrail.io/index.php?/cases/view/1655101 golden    > released build
# - C1655102 https://netskope.testrail.io/index.php?/cases/view/1655102 earlier build > earlier build > released build (chain upgrade)
# - C2105126 https://netskope.testrail.io/index.php?/cases/view/2105126 hot fix   > released build
#
#   csv file
#   - get it from https://kibana.netskope.io/s/epdlp/app/dashboards#/view/16d7a160-4336-11ef-80d2-135fd25b6188?_g=(filters:!(),refreshInterval:(pause:!t,value:0),time:(from:now-1d,to:now))
#
# how to run?
#
#   > cd play
#   > cd Scripts
#   > activate
#   > cd c:\testing
#   > pytest test_install_upgrade.py --upgrade_to_version 132.0.0.2456 --upgrade_to_bit 32 --customer_file customers-tiny.csv --target_dir C:\testing\binaries --tenant sjc1 --username michaell --expected_upgrade_time 240 -v --lowest_testing_version 125
#
# ==========================================================================

def load_customer_versions(customer_file, lowest_testing_version=0, enable_auto_selection=False, skip_low_count=True):

    black_list = ["124.0.0.2277","126.0.6.2892"] # not implemented yet

    customer_versions = []
    '''
    try:                                                                       # if trying to upgrade to 123.0.0.5575
        supported_major_version = int(pytest.upgrade_to_version.split(".")[0]) # the supported_major_version is 123
    except ValueError:
        if "client-builds-origin" in pytest.upgrade_to_version:
            upgrade_to_version = ".".join(pytest.upgrade_to_version.split("/")[-4:-2])
            supported_major_version = int(upgrade_to_version.split(".")[0])
        else:
            raise Exception("not able to find a good supported major version")
    '''
    # pdb.set_trace()


    lines = open(customer_file, "r")    # "Agent Version","Unique count of uri_path.keyword" <- 1st line is just a header
    lines.readline()                    # "123.0.9.2307","157,839"                           <- 2nd line has data, so move to 2nd line

    for line in lines:
        #customer_version = line.split(",")[1]

        customer_version = line.split(",")[0]                # "123.0.9.2307"
        customer_version = customer_version.replace("\"","") # clean up opening and closing quote
                                                             # ex: "121.0.7.2203" => 121.0.7.2203

                                                             # "157,839"
        if skip_low_count:                                   # if enabled, stop support simulating upgrade when count is less than 5

            customer_count = line.split(",")[1:]          # b/c it's possible it's one off, intermediate build
            customer_count = "".join(customer_count)

            customer_count = customer_count.replace("\"","") # clean up opening and closing quote
            customer_count = customer_count.strip()  # clean up middle comma
            if int(customer_count) < 10:
                pytest.logger.info(f"will skip this version {customer_version}, since downloaded count is below {customer_count}")
                continue

        # if "." in customer_version and customer_version not in customer_versions: # if there are both 123.0.0.x and 123.0.6.x out there in the wild
                                                                                       # this logic would skip 123.0.6.x, which we don't want
        if "." in customer_version:
            '''
            ns_client_major_version = int(customer_version.split(".")[0])
            #if ns_client_major_version < supported_major_version - 6:              # get this major version
                                                                                    # and we only support from -6
                                                                                    # ex: 123-6=117
            if enable_auto_selection:
                if ns_client_major_version >= supported_major_version or \
                        ns_client_major_version < 117 or \
                        customer_version in black_list:
                    continue
            '''
            if lowest_testing_version != 0:
                customer_major_version = int(customer_version.split(".")[0])
                if customer_major_version < lowest_testing_version:
                    pytest.logger.info(f"will skip this version {customer_version}, since it's below {lowest_testing_version}")
                    continue

            if  get_downloadable_url(customer_version) == "":
                pytest.logger.info(f"will skip this version {customer_version}, since not able to download")
            else:
                customer_versions.append(customer_version)

    # pdb.set_trace()
    return customer_versions


def matrix_generator():

    testing_version = TESTING_VERSION
    testing_major_version = testing_version.split(".")[0]
    testing_minor_version = testing_version.split(".")[1]
    testing_patch_version = testing_version.split(".")[2]
    testing_build_version = testing_version.split(".")[3]

    matrix = []
    customer_versions = load_customer_versions(pytest.customer_file, lowest_testing_version=pytest.lowest_testing_version)
    for customer_version in customer_versions:
        customer_major_version = customer_version.split(".")[0]
        customer_minor_version = customer_version.split(".")[1]
        customer_patch_version = customer_version.split(".")[2]
        customer_build_version = customer_version.split(".")[3]

        if testing_major_version > customer_major_version:
            matrix.append((customer_version, testing_version))
        elif testing_major_version == customer_major_version:
            if testing_minor_version > customer_minor_version:
                matrix.append((customer_version, testing_version))
            elif testing_minor_version == customer_minor_version:
                if testing_build_version > customer_build_version:
                    matrix.append((customer_version, testing_version))
                elif testing_build_version < customer_build_version:
                    matrix.append((testing_version, customer_version))
            else:
                matrix.append((testing_version, customer_version))
        else:
            matrix.append((testing_version, customer_version))

        # test_name = f"upgrade from {customer_version} to {pytest.upgrade_to_version}"
    # pdb.set_trace()
    '''
    combinations = []
    epdlp_combinations = [
        ["disable", "disable"],
        ["enable",  "enable"],
        ["disable", "enable"]]
    for epdlp_combination in epdlp_combinations:
        for ns_client_combination in ns_client_combinations:
            epdlp_combination.extend()
            combinations.append()
    '''
    matrix_return = matrix.copy()

    return matrix_return

TESTING_VERSION = get_binary_version(pytest.upgrade_to_version)
COMBINATIONS = matrix_generator()

class TestInstallUpgrade():


    def setup_class(self):
        self.target_dir = pytest.target_dir
        self.tenant = pytest.tenant
        self.username = pytest.username
        self.expected_upgrade_time = pytest.expected_upgrade_time
        '''
        client = Client(
            config_name = "MichaelConfig",
            hostname="epdlp-tenant00.stg.boomskope.com",
            username=os.environ["USERNAME"],
            password=os.environ["PASSWORD"])

        # ensure that epdlp is enabled prior to testing
        if client.epdlp_enabled == "0":
            client.enable()
        '''

    def teardown_method(self):

        Installer.uninstall(self.download_file_full_path)

        # ensure that epdlp and epldodrv are not running
        steady_state_count = 0
        for i in range(10):
            msg = Display.status()
            if msg.count("RUNNING") == 0:
                steady_state_count += 1
                if steady_state_count == 3:
                    break
            else:
                pytest.logger.info(f"epdlp and epdlpdrv should not be running, msg={msg}")
                time.sleep(10)

        if steady_state_count != 3:
            raise Exception(f"epdlp and epdlpdrv should not be running")


    def ensure_epdlp_epdlpdrv_running(self, num_try=10, wait_time=10):

        for i in range(num_try):
            try:
                current_status = Display.status()
                msg = f"not running as expected, {current_status}"
                assert current_status.count("RUNNING") == 2, msg
                pytest.logger.info(f"both epdlp and epdlpdrv are running")
                break
            except AssertionError as e:
                pytest.logger.info(f"{e}, will wait for {wait_time} more seconds")
                time.sleep(wait_time)


    def check_deployment_folder(self):
        folder="C:\\Program Files (x86)\\Netskope\\EPDLP Deployment"
        if pytest.is_64bit:
            msg = f"'{folder}'' should not exist in 64bit installer"
            assert not os.path.exists(folder), msg
        else:
            msg = f"'{folder}' should exist in 32bit installer"
            assert os.path.exists(folder), msg


    def check_binary_signed(self):
        binary_folder1 = "C:\\Program Files\\Netskope\\EPDLP"
        binary_folder2 = "C:\\Windows\\System32\\drivers"
        files_processed = Installer.get_files_processed(binary_folder1)
        files_processed_more = Installer.get_files_processed(binary_folder2, enforce_looking_epdlp=True)
        files_processed.extend(files_processed_more)

        files_not_signed, files_not_signed_by_us = Installer.check_binary_signed(files_processed)
        pytest.logger.info(f"files_not_signed: {files_not_signed}")
        pytest.logger.info(f"files_not_signed_by_us: {files_not_signed_by_us}")
        assert len(files_not_signed)==0, f"{files_not_signed} files are not signed"


    def is_blocked(self, file_name):
        pattern = f".*{file_name}.*"
        for log_file in [
            "C:\\ProgramData\\netskope\\EPDLP\\logs\\epdlp_sys_log.txt",
            "C:\\ProgramData\\netskope\\EPDLP\\logs\\epdlp_sys_log.1.txt"]:
            if not os.path.exists(log_file):
                continue
            with open(log_file, 'r', encoding="utf8") as file:
                content = file.read()
                # pdb.set_trace()
                matches = re.findall(pattern, content, re.MULTILINE)

            for match in matches:
                if "with action \"block\"" in match:
                    return True
        return False

    def check_crash_dump(func):
        def wrapper(*args, **kwargs):
            # --------------------
            # before
            # --------------------
            # file_count_before = len(glob.glob(f"C:\\testing\\dump\\**"))
            # msg1= f"REFERENCE: before there are {file_count_before} crash dumsp"
            file_path = "C:\\testing\\dump"
            cmd = f'powershell -noninteractive -command "Get-ChildItem -Path "{file_path}" -Recurse | Measure-Object -Property Length -Sum"'

            msg = os.popen(cmd).read()
            tokens = msg.split()
            size_before = 0
            for i, token in enumerate(tokens):
                if "Sum" == token:
                    size_before = tokens[i+2]
                    break
            msg1= f"REFERENCE: before {file_path} has size {size_before}"
            pytest.logger.info(msg1)

            # --------------------
            # run
            # --------------------
            result = func(*args, **kwargs)
            time.sleep(10)

            # --------------------
            # after
            # --------------------
            # file_count_after = len(glob.glob(f"C:\\testing\\dump\\**"))
            # msg2 = f"REFERENCE; after there are {file_count_after} crash dumps"
            msg = os.popen(cmd).read()
            tokens = msg.split()
            size_after = 0
            for i, token in enumerate(tokens):
                if "Sum" == token:
                    size_after = tokens[i+2]
                    break
            msg2= f"REFERENCE: after {file_path} has size {size_after}"
            pytest.logger.info(msg2)

            # if file_count_after > file_count_before:
            #     assert False, f"new crash dump found; {msg1}, {msg2}"
            if size_before != size_after:
                assert False, f"crash dump found, size_before {size_before} is not the same as size_after {size_after}"

            return result
        return wrapper

    @check_crash_dump
    def check_nfscc_filetypes(self, target_dir_with_drive_letter, should_block=True):

        # target_dir                            2025-06-17-15-38-26
        # target_dir_with_drive_letter       Y:\2025-06-17-15-38-26
        # target_dir_with_file                  2025-06-17-15-38-26\hello.txt
        # target_dir_with_driver_letter_file Y:\2025-06-17-15-38-26\hello.txt

        # copy every single file under sample_file_dir to the NFS
        sample_file_dir = "C:\\testing\\sample_data_automation"
        files_full_path = glob.glob(f"{sample_file_dir}\\**", recursive=True) # glob returns the full path
        not_blocked_files = []
        not_copied_files = []
        for file_full_path in files_full_path[1:]:
            # ------------
            # copy to NFS
            # ------------
            cmd = f"copy {file_full_path} {target_dir_with_drive_letter}"
            os.system(cmd)

            # ------------
            # check the log and see if the file is blocked when it's supposed to
            # ------------
            file_name = file_full_path.split("\\")[-1]
            '''
            target_dir_with_file = f"{target_dir}\\\\{file_name}"

            is_finally_blocked = False
            for i in range(5):
                if self.is_blocked(target_dir_with_file):
                    is_finally_blocked = True
                    break
                else:
                    time.sleep(1)
            '''
            # ------------
            # collect a list of files that are copied to the target when they are not supposed to
            # collect a list of files that are not copied to the target when they are supposed to
            # ------------
            target_dir_with_driver_letter_file = f"{target_dir_with_drive_letter}//{file_name}"
            if "NO-BLOCK" not in file_full_path and os.path.exists(target_dir_with_driver_letter_file):
                not_blocked_files.append(file_full_path)

            if "NO-BLOCK" in file_full_path and not os.path.exists(target_dir_with_driver_letter_file):
                not_copied_files.append(file_full_path)

        if should_block:
            # if we get any unblocked files that should have been blocked, fail it
            if len(not_blocked_files) > 0:
                msg = f"these files {not_blocked_files} are not blocked, but they are supposed to"
                assert False, msg

            # if any of the NO-BLOCK-<file> are not copied to the NFS, fail it, because should be copied
            if len(not_copied_files) > 0:
                msg = f"these files {not_copied_files} are not copied, but they are supposed to"
                assert False, msg
        else:
            num_target_files = len(glob.glob(f"{target_dir_with_drive_letter}\\**"))
            num_source_files = len(files_full_path) - 1
            if num_source_files != num_target_files:
                assert False, f"expecting {num_source_files} files copied, but only getting {num_target_files} files copied"

    @check_crash_dump
    def check_nfscc_network_disconnect(self, target_dir, target_dir_with_drive_letter):

        cmds = [
            f"copy sample_data_txt\\pci-2000000.txt sample_data_txt\\pci-2000000-backup.txt",
            f"echo {target_dir} >> sample_data_txt\\pci-2000000-backup.txt",
            f"start /b copy sample_data_txt\\pci-2000000-backup.txt {target_dir_with_drive_letter} & net use Y: /delete /y",
            f"del sample_data_txt\\pci-2000000-backup.txt",
            f"net use Y: \\\\10.136.217.175\\shared "
        ]
        for cmd in cmds:
            os.system(cmd)

    @check_crash_dump
    def check_nfscc_open_save_word(self):
        def open():
            cmd = "start winword Y:\\pci-1.docx"
            os.system(cmd)

        def save():
            for window in gw.getWindowsWithTitle("pci-1.docx"):
                if not window.isActive:
                    window.activate()
                pyautogui.hotkey("ctrl", "s")
                return

        def close():
            for window in gw.getWindowsWithTitle("pci-1.docx"):
                if not window.isActive:
                    window.activate()
                pyautogui.hotkey("alt", "F4")
                return

        open()
        time.sleep(10)
        save()
        close()
        time.sleep(10)


    @pytest.mark.parametrize(
        ("upgrade_from", "upgrade_to"), COMBINATIONS
    )
    def test_install_upgrade(self, upgrade_from, upgrade_to):

        def get_ns_client_version(version):
            # if testing_version == https://artifactory.netskope.io/artifactory/client-builds-origin/release/123.0.10/2367/Release/STAgent.msi
            # testing_version = 123.0.10.2367
            # if testing_vrsion == 123.0.10.2367
            # testing_version = 123.0.10.2367

            if version == TESTING_VERSION:
                return pytest.upgrade_to_version
            else:
                return version

        def check_failing(version, logfile):
            with open(logfile, 'rb') as f:
                contents = f.read()
            if "Installation failed" in contents.decode("utf-16"):
                lines = contents.decode("utf-16").split("\r\n")
                for line in lines:
                    # capture the line that complains about the failure
                    # ex: GetNsbrandingJsonFile:  Error 0x2: Failed to download branding file using licence key after 3 retries
                    #     1: Installation failed to download the configuration, check your internet connection and try again.
                    if "Installation failed" in line:
                        # preserve the installer log file once upgrade has failed for furture references
                        old_log_file = logfile
                        new_log_file = logfile.replace(".log", f"-{version}-{datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.log")
                        os.rename(old_log_file, new_log_file)
                        assert False, line
        # pdb.set_trace()
        # self.check_nfscc_filetypes("Y:\\temp1",should_block=True)
        # ==================================================
        # upgrade from
        # ==================================================

        self.download_file_full_path = download(
            # ns_client_version = get_ns_client_version(upgrade_from),
            ns_client_version = get_binary_version(upgrade_from),
            target_dir = self.target_dir,
            tenant = self.tenant,
            username = self.username,
            is_64bit = False)

        logfile = "upgrade-testing-upgrade-from.log"
        Installer.install(self.download_file_full_path, logfile=logfile)
        Installer.configure()
        fd = open("download_file_full_path.txt","w")
        fd.write(self.download_file_full_path)
        fd.flush()
        fd.close()

        # detect to see if install has failed or not from the logfile; if so, early exit
        check_failing(version=upgrade_from, logfile=logfile)

        # ensure that we are running on the correct version
        for i in range(10):
            try:
                version_installed = Display.version()
                msg = f"running on version: {version_installed}, but expected version: {upgrade_from}"
                pytest.logger.info(f"running on version {version_installed}")
                assert version_installed.split()[-1] == upgrade_from, msg
                break
            except IndexError as e:                             # sometimes, if we check version too fast after the upgrade
                pytest.logger.info(f"ERROR: {e}")                            # it might not return us the version in timely fashion
                pytest.logger.info(f"running on version {version_installed}") # ending with "IndexError: list index out of range"
                time.sleep(10)                                  # so give it few more tries
            except Exception as e:
                assert False, msg

        # ensure that epdlp and epdlpdrv are up and running
        self.ensure_epdlp_epdlpdrv_running()

        # ------------------
        # test case: 3rd party integration
        #           open up application
        #           - ensure that notepad can save the file without corruption
        #           - ensure that chrome still has all tabs opened
        # ------------------
        '''
        # open up application
        cmd = "python C:\\testing\\background_notepad_copy_usb.py"
        os.system(f"START /B {cmd}")
        '''
        # let things sync in a bit
        pytest.logger.info("wait for 2 minutes to let things sync in a bit")
        time.sleep(120)

        # ==================================================
        # upgrade to
        # ==================================================

        # to support upgrade from 32bit to 64bit
        # - when upgrading to 64bit, we should overwrite the binary folder to re-downloan
        #   why? because the logic is to check if there is any pre-existing downloaded binary, if yes, don't download again
        #        however, the downloaded binary whether it's 32bit or 64bit contain the same file name
        #        therefore we overwrite, force download
        if pytest.is_64bit:
            should_overwrite=True
        else:
            should_overwrite=False

        self.download_file_full_path_previous = self.download_file_full_path
        self.download_file_full_path = download(
            # ns_client_version = get_ns_client_version(upgrade_to),
            ns_client_version = get_binary_version(upgrade_to),
            target_dir = self.target_dir,
            tenant = self.tenant,
            username = self.username,
            overwrite = should_overwrite,
            is_64bit = pytest.is_64bit)

        logfile = "upgrade-testing-upgrade-to.log"
        stdout = Installer.install(self.download_file_full_path, logfile=logfile)
        # Installer.configure("BAC-NFSCC") # required if we want to examine its logs
        fd = open("download_file_full_path.txt","w")
        fd.write(self.download_file_full_path)
        fd.flush()
        fd.close()

        # detect to see if upgrade has failed or not from the logfile; if so, early exit
        check_failing(version=upgrade_to, logfile=logfile)

        # ensure that deployment fodler exists in 32bit installer, not in 64bit installer
        # self.check_deployment_folder()

        # ------------------
        # test case C1547987: ensure that the upgrade time doesn't take too long
        # lines would look like
        #   ...
        #   Minutes           : 1
        #   Seconds           : 29
        # ------------------

        lines = stdout.split("\n")
        for line in lines:
            unit = line.split(":")[0].strip()
            value = line.split(":")[-1].strip()
            if unit == "Minutes":
                minutes = value
            elif unit == "Seconds":
                seconds = value
        actual_upgrade_time = int(minutes)*60 + int(seconds)
        pytest.logger.info(f"upgrade time {actual_upgrade_time} seconds")
        # pdb.set_trace()
        # expected_upgrade_time = pytest.expected_upgrade_time
        msg = f"expected_upgrade_time={self.expected_upgrade_time}, actual_upgrade_time={actual_upgrade_time}"
        assert actual_upgrade_time <= self.expected_upgrade_time, msg

        # ------------------
        # test case: make sure that all binaries are signed
        # ------------------

        # self.check_binary_signed()

        # -----------------
        # test case: ensure that we are running on the correct version
        #           we only do this checkpoint if the upgrade_to is not a direct url download
        #           it only works when user provides a specific version, ex: 123.0.0.1
        #           upgrade_to = "123.100.100.5773"
        # -----------------

        version_installed = Display.version()
        pytest.logger.info(f"running on version {version_installed}")
        msg = f"running on version: {version_installed}, but expected version: {upgrade_to}"
        assert version_installed.split()[-1] == upgrade_to, msg

        # ensure that epdlp and epldodrv are up and running
        self.ensure_epdlp_epdlpdrv_running()

        # ------------------
        # test case: make sure that NFSCC works as expected
        # -----------------
        '''
        # pdb.set_trace()
        # cmd = "xcopy C:\\testing\\local_config.json C:\\ProgramData\\netskope\\EPDLP\\config /Y"
        # os.system(cmd)
        '''
        time.sleep(120) # ensure to sleep long enough before file copying
                        # else we woule be getting some false alarms
        # pdb.set_trace()
        # create testing directory at the NFS if not there
        target_dir = datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        target_dir_with_drive_letter = f"Y:\\upgrade-from-{upgrade_from}-{target_dir}"
        if not os.path.exists(target_dir_with_drive_letter):
            os.makedirs(target_dir_with_drive_letter)
        else:
            os.rmdir(target_dir_with_drive_letter)

        # self.check_nfscc_filetypes(target_dir_with_drive_letter)
        # pdb.set_trace()
        # self.check_nfscc_network_disconnect(target_dir, target_dir_with_drive_letter)
        # self.check_nfscc_open_save_word()

        # ------------------
        # wrapping things up
        # ------------------

        time_to_wait = 180
        pytest.logger.info(f"wait for additional {time_to_wait} seconds for things to finish")
        time.sleep(time_to_wait)


        # pdb.set_trace()

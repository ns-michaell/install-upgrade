# import argparse
import os
import pdb
import subprocess
import requests
import yaml
import sys
import time
# import pytest
# from urllib import urlopen
from urllib.request import urlopen

proxy_server_ip = "10.136.217.175"

def get_downloadable_url(version, is_64bit=False):

    if is_64bit:
        package_name = "STAgent64.msi"
    else:
        package_name = "STAgent.msi"

    if version == "develop":
        url = "https://artifactory-rd.netskope.io/ui/native/client-builds/develop"
        response = urlopen(url)
        htmlRows = response.readlines()


    # extract major and minor versions
    if "https" in version:
        is_url_download = True
    else:
        is_url_download = False
        major_version = version.split(".")[:-1] # ex: 127.1.0.6182
        major_version = ".".join(major_version) #     127.1.0      major_version
        minor_version = version.split(".")[-1]  #             6182 minor_version
    # pdb.set_trace()
    # print(f"major_version={major_version}, minor_version={minor_version}")

    # try download from release first
    # if not from release, try develop second
    '''
    try:
        requests.get(url)
    except requests.exceptions.SSLError as e:
        print(f"{url} is not in 'release' branch, trying 'develop' branch")
        time.sleep(5)
        try:
            url = f"https://artifactory-rd.netskope.io/artifactory/client-builds/develop/{major_version}/{minor_version}/STAgent.msi"
            requests.get(url)
        except requests.exceptions.SSLError as e:
            print(f"{url} is not available for download")
            raise Exception(e)
    '''
    if is_url_download:
        url = version
        response = requests.get(url, verify=False)
        if response.status_code == 404:
            print(f"{url} is not available for download")
            return ""
    else:
        url = f"https://artifactory-rd.netskope.io/artifactory/client-builds/release/{major_version}/{minor_version}/Release/{package_name}"
        # pytest.logger.info(f"determing if {url} is a downloadable url")
        print(f"determing if {url} is a downloadable url")
        # pdb.set_trace()
        #response = requests.get(url, verify=False)
        for i in range(10):
            try:
                response = requests.get(url, verify=False)
                break
            except Exception as e:
                print(f"{e}, will run again")
                time.sleep(5)
        # pdb.set_trace()
        if response.status_code == 404:
            print(f"{url} is not in 'release' artifactory directory, will try 'develop' artifactory direcotry")
            url = f"https://artifactory-rd.netskope.io/artifactory/client-builds/develop/{major_version}/{minor_version}/{package_name}"
            response = requests.get(url, verify=False)
            if response.status_code == 404:
                print(f"{url} is not in 'develop' artifactory directory, will try proxy server {proxy_server_ip}")
                url = f"http://{proxy_server_ip}/binaries/{major_version}.{minor_version}/{package_name}"
                response = requests.get(url, verify=False)
                if response.status_code == 404:
                    print(f"{url} is not in proxy server {proxy_server_ip}")
                    return ""

    return url


def get_file_name(tenant, username):

    fd = open("tenants.yml", "r")
    tenants = yaml.safe_load(fd)
    fd.close()

    return f"{tenants[tenant][username]}.msi"


def issue_curl_download(ns_client_version, download_full_path, num_tries=10, is_64bit=False):

    url = get_downloadable_url(ns_client_version, is_64bit)
    if url == "":
        raise Exception(f"{ns_client_version} is not available for download")
    # pdb.set_trace()
    # there is a trick to these 2 types of url below
    # 1) https://artifactory-rd.netskope.io/ui/native/client-builds/release/126.0.0/2378/Release/STAgent.msi
    #    this url often prompts us to authenticate in order to download, else we would run into "doesn't work properly without JavaScript enabled. Please enable it to continue"
    # 2) https://artifactory-rd.netskope.io/artifactory/client-builds/release/126.0.0/2378/Release/STAgent.msi
    #    thsi url works the best without having to authenticate; therefore, whenever we see #1, substitue "ui/native" with "artifactory"
    url = url.replace("ui/native", "artifactory")

    for i in range(num_tries):
        try:
            # --------------------
            # 1st download attempt (without --ssl-no-revoke)
            # --------------------
            cmd = f"curl -f {url} --output {download_full_path}"
            process = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
            stdout, stderr = process.communicate()

            # if download is not successful, fallback to ssl-no-revoke
            # if download is     successful, exit
            if process.returncode != 0:
                print(f"Error: Command exited with code {process.returncode}")
                if stderr:
                    msg = f"Error: unable to download from {url}, due to {stderr.decode()}"
                    print(msg)
                print("will proceed next download with --ssl-no-revoke")
            else:
                print(f"Successfully download from {url}")
                return

            # --------------------
            # 2nd download attempt as fallback (with --ssl-no-revoke)
            # --------------------
            if "InitializeSecurityContext" in stderr.decode():
                cmd = f"curl -f {url} --ssl-no-revoke --output {download_full_path}"
                process = subprocess.Popen(cmd,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                shell=True)
                stdout, stderr = process.communicate()

                # if download is not successful, raise exception
                # if download is     successful, exit
                if process.returncode != 0:
                    msg = f"Error: unable to download from {url}, due to {stderr.decode()}"
                    raise Exception(msg)
                else:
                    print(f"Successfully download from {url} with --ssl-no-revoke")
                    return

            # if stderr.decode()!="" and process.returncode!=0:
            #     msg = f"unable to download from {url}, due to {stderr.decode()}"
            #     raise Exception(msg)

        except Exception as e:
            print(e)
            time.sleep(5)

    raise Exception(f"tried downloading {url} for {num_tries} times without success")


def get_binary_version(version, is_64bit=False):
    if is_64bit:
        package_name = "STAgent64.msi"
    else:
        package_name = "STAgent.msi"

    if "client-builds" in version:
        #                                                                                                       -4    -3   -2      -1
        # support download from 1) https://artifactory.netskope.io/artifactory/client-builds-origin/release/123.0.10/2367/Release/STAgent.msi
        # support download from 2) https://artifactory-rd.netskope.io/ui/native/client-builds/release/126.0.0/2378/Release/STAgent.msi
        #                       3) https://artifactory-rd.netskope.io/artifactory/client-builds/release/126.0.0/2378/Release/STAgent.msi
        binary_version = ".".join(version.split("/")[-4:-2])
    elif "client-feature-builds-origin" in version:
        # support download from https://artifactory-ep-kiwi-internal.netskope.io/artifactory/client-feature-builds-origin/feature/jenkins-client-feature-pipeline-6052/6052/Release/STAgent.msi
        # first, download to local
        download_full_path = os.path.join(os.getcwd(), package_name)
        issue_curl_download(version, download_full_path, is_64bit=is_64bit)

        # second, once downloaded, get its binary version
        cmd = f'powershell -noninteractive -command "Get-AppLockerFileInformation -Path "{download_full_path}" | Select -ExpandProperty Publisher | select BinaryVersion"'
        msg = os.popen(cmd).read()
        binary_version = msg.split()[-1]

        # remove the downloaded binary, since it's no use
        # pdb.set_trace()
        os.remove(download_full_path)
    else:
        binary_version = version

    return binary_version


def download(ns_client_version, target_dir, tenant, username, overwrite=False, is_64bit=False):
    # target_dir = "C:\\Users\\vagrant\\Downloads"
    # customers = {}
    '''
    # below logic has become problematic
    # b/c
    # 1st time, if we run ns_client_version = https://artifactory.netskope.io/artifactory/client-builds-origin/release/123.0.10/2367/Release/STAgent.msi
    # 2nd time, if we run ns_client_version = https://artifactory-rd.netskope.io/ui/native/client-builds/release/126.0.0/2378/Release/STAgent.msi
    # that means.. both binaries will go under "STAgent" direcotry, mixing up tests
    if "https:" in ns_client_version:
        try:
            # support for https://artifactory-gcp.netskope.io/artifactory/client-feature-builds/feature/jenkins-client-feature-pipeline-5803/5803/Release/STAgent.msi
            dir_name = ns_client_version.split("/feature/")[1].split("/")[0]
        except IndexError:
            # support for arbitrary url ex: https://storage.googleapis.com/epdlp_pre_agent_public/STAgent%20123.100.100.5773%20-%20pre.ms
            dir_name = "".join(ns_client_version.split("/")[-1].split(".")[:-1]) # dir name will be just the file name, ex: STAgent%20123.100.100.5773%20-%20pre
        download_dir = os.path.join(target_dir, dir_name)
    else:
        download_dir = os.path.join(target_dir, ns_client_version)
    '''

    download_dir = os.path.join(target_dir, get_binary_version(ns_client_version, is_64bit))
    # pdb.set_trace()

    # download_full_path = os.path.join(download_dir, f"{tenants[tenant]}.msi")
    #msi_tenant = "NSClient_addon-epdlp-tenant00.stg.boomskope.com_1303_yoz9g5aVZ2sv2730B790_f6Nj6L7icQfA5OUeHlv6J7xOh4Ds11E03licW9ll_.msi"
    #msi_tenant = "NSClient_addon-sjc1-datasecurity-ep.goskope.com_14989_S39jdnjr05OqZ6DK78Ef_9Sxqwb6Lnr00SnUmZ6JGm8qxm7G6kYndD3rc7qEX_.msi"
    msi_tenant = get_file_name(tenant, username)

    download_full_path = os.path.join(download_dir, msi_tenant)
    # pdb.set_trace()
    if not os.path.exists(download_full_path) or overwrite:

        # create download directory, and download msi
        if not os.path.exists(download_dir):
            os.makedirs(download_dir)
        # pdb.set_trace()

        issue_curl_download(ns_client_version, download_full_path, is_64bit=is_64bit)
        '''
        url = get_downloadable_url(ns_client_version)
        if url == "":
            raise Exception(f"{ns_client_version} is not available for download")

        # there is a trick to these 2 types of url below
        # 1) https://artifactory-rd.netskope.io/ui/native/client-builds/release/126.0.0/2378/Release/STAgent.msi
        #    this url often prompts us to authenticate in order to download, else we would run into "doesn't work properly without JavaScript enabled. Please enable it to continue"
        # 2) https://artifactory-rd.netskope.io/artifactory/client-builds/release/126.0.0/2378/Release/STAgent.msi
        #    thsi url works the best without having to authenticate; therefore, whenever we see #1, substitue "ui/native" with "artifactory"
        url = url.replace("ui/native", "artifactory")
        cmd = f"curl -f {url} --output {download_full_path}"
        # print(cmd)
        # os.system(cmd)
        process = subprocess.Popen(cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        shell=True)
        stdout, stderr = process.communicate()
        # pdb.set_trace()

        if "InitializeSecurityContext" in stderr.decode():
            cmd = f"curl -f {url} --ssl-no-revoke --output {download_full_path}"
            process = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=True)
            stdout, stderr = process.communicate()

        if stderr.decode()!="" and process.returncode!=0:
            raise Exception(f"unable to download from {url}")
        '''
        print(f"created directory {download_dir}, downloaded {download_full_path}")

        # customers[ns_client_version] = download_full_path
    else:
        print(f"{download_full_path} already exists, skip downloading")

    # return customers
    return os.path.join(download_dir, download_full_path)


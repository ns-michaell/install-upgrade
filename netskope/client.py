import os
from webapi import WebAPI
import pdb
from requests.exceptions import ConnectionError
import time
#
# pip install pylark-webapi-lib==1.14.0 --index-url https://artifactory-internal.netskope.io/artifactory/api/pypi/ns-pypi/simple
#

from webapi.settings.security_cloud_platform.netskope_client.client_configuration import ClientConfiguration

class Client():

    def __init__(self, config_name, hostname, username, password):
        self.config_name = config_name
        self.hostname = hostname
        self.webapi = WebAPI(
            hostname=hostname,
            username=username,
            password=password)

        self.web_config = ClientConfiguration(self.webapi)
        for i in range(12):
            try:
                self.web_config._get_client_config(self.config_name)
                break
            except ConnectionError as e:
                print(f"can not get client config due to '{e}', will wait for 5 more seconds and retry")
                time.sleep(5)


    @property
    def epdlp_enabled(self):
        return self.web_config._get_client_config(self.config_name)["raw_data"]["data"][0]["config"]["endpoint_dlp"]

    def enable(self):
        self.web_config.update_client_config(self.config_name, endpoint_dlp=1)

    def disable(self):
        self.web_config.update_client_config(self.config_name, endpoint_dlp=0)

    def force_push(self):
        if "npa" in self.hostname:
            cmd = "curl -XPOST 'http://klbivip-ext.c1.npa01-mp-npe.nc1.iad0.nsscloud.net/api/v1/buildpolicy/1057?force=true' -H 'HOST: epdlp-mp-policy-data' -v"
        elif "stg" in self.hostname:
            cmd = "curl -XPOST 'http://klbivip-ext.c1.stg01-mp.nc4.iad0.nsscloud.net/api/v1/buildpolicy/1303?force=true' -H 'HOST: epdlp-mp-policy-data' -v"

        os.system(cmd)


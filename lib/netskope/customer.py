from fetcher import get_downloadable_url

class Customer():

    @staticmethod
    def load_customer_versions(customer_file, lowest_testing_version=0, enable_auto_selection=False, skip_low_count=True):

        black_list = ["124.0.0.2277"]

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
                if int(customer_count) < 5:
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
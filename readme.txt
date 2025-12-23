prep work for running tests and scripts

    install necessary public packages

        > pip install pytest
        > pip install selenium==3.141.0             # not the latest selenium, please see issue #2 below
        > pip install Appium-Python-Client==1.2.0   # not the latest appium,   please see issue #1 below
        > pip install --upgrade urllib3==1.26.16    # not the latest urllib3
                                                    # because we are not using latest appium, we can't use latest urllib3
how to install additional testing packages

    > pip install --trusted-host 10.136.217.175 -U -r requirements-additional.txt
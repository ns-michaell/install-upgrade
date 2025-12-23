import paramiko
import pdb
import time
import os
from appium import webdriver
import selenium

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    RED = '\033[91m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Windows():

    def __init__(self,
        host="",
        port="",
        user="",
        password="",
        # key_pair=""
    ):
        # self.calculators = [] # holds a collection of "win32calc" app object running
        # self.explorers = []   # holds a collection of "explorer" app object running
        # self.notepads = []    # holds a collection of "notepad" app object running
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        '''
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        if key_pair != "":
            self.key_pair = key_pair
            private_key = paramiko.RSAKey.from_private_key_file(self.key_pair)
            self.client.connect(self.host, username=self.user, password=self.password, pkey=private_key, timeout=5)
        else:
            self.client.connect(self.host, username=self.user, password=self.password, timeout=5)
        '''
    '''
    @property
    def sshd_maxsessions(self):

        max_sessions = os.popen("/bin/cat /etc/ssh/sshd_config | grep MaxSession").read().split()[1]
        return int(max_sessions)


    def _run_concurrent_cmd(self, cmd):

        client = None
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            private_key = paramiko.RSAKey.from_private_key_file(self.key_pair)
            client.connect(self.host, username=self.user, password=self.password, pkey=private_key, timeout=5)
            client.exec_command(cmd)
            # stdout = stdout.read().strip().decode()
            # stderr = stderr.read().strip().decode()
            print(f"running concurrent cmd='{cmd}'")
        finally:
            if client:
                client.close()


    @property
    def screen_locked(self):

        stdin, stdout, stderr = self.cmd("query user")
        if "Disc" in stdout:
            return True
        else:
            return False


    def unlock_screen(self):

        # prepare unlock screen script
        script="""
@echo off
for /f "skip=1 tokens=3" %%s in ('query user %USERNAME%') do (
  %windir%\\System32\\tscon.exe 1 /dest:console
)
"""

        local_file = "unlock.bat"
        remote_file = "C:\\unlock.bat"

        # generate script to local first
        fd = open(local_file,"w")
        fd.write(script)
        fd.close()

        # upload script to remote
        self.send(local_file, remote_file)
        self.cmd(remote_file)
        self.delete_file(remote_file)
        os.remove(local_file)


    def cmd(self, cmd, background=False):

        if background:                              # hasn't been tested yet
            transport = self.client.get_transport() # need to test to find out
            channel = transport.open_session()      # to see if it's really working
            channel.exec_command(cmd)
        else:
            stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        return stdin, stdout, stderr


    def get_file_size(self, file_path):

        cmd = f'for %I in ({file_path}) do @echo %~zI'
        stdin, stdout, stderr = self.client.exec_command(cmd)
        file_size = stdout.read().strip().decode()
        try:
            file_size = int(file_size)
        except ValueError:
            file_size = 0
        return file_size


    def get_folder_size(self,
        folder_path,
        check_consistency=False,
        max_sample_checks=3,
        wait_time_interval=1,
        debug=True
    ):

        cmd = ('python -c  "import os;import sys;sys.stdout.write('
               'str(sum([sum([os.stat(os.path.join(dirpath, filename)).st_size '
               'for filename in filenames]) for dirpath, dirnames, filenames in os.walk(\'"' + folder_path.replace('\\', '/') + '"\')])))"')

        def measure():
            stdin, stdout, stderr = self.client.exec_command(cmd)
            folder_size = stdout.read().strip().decode()
            try:
                folder_size = int(folder_size)
            except ValueError:
                    folder_size = 0
            return folder_size

        if check_consistency:
            sizes=[]
            for i in range(10):
                folder_size = measure()
                sizes.append(folder_size)                    # mechanism to check for consistency
                if len(sizes) >= max_sample_checks:          # - once the size has reached the sample size
                    if len(sizes[-max_sample_checks:]) == 1: #   we look at the last x samples, and return
                        return folder_size                   #   if the last x samples are the same
                    else:
                        if debug:
                            print(f"establishing folder sizes consistency: current folder size {sizes[-1]} Vs previous measured size {sizes[-2]}")
                        time.sleep(wait_time_interval)
            return folder_size
        else:
            return measure()


    def disconnect_all_rdp_session(self):

        cmd=f"for /f \"skip=1 tokens=3\" %s in ('query user %USERNAME%') do (%windir%\\System32\\tscon.exe 1 /dest:console)"
        stdin, stdout, stderr = self.cmd.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        return stdin, stdout, stderr


    def create_directory(self, directory_path):
        cmd = f'mkdir {directory_path}'
        stdin, stdout, stderr = self.client.exec_command(cmd)
        if stderr!="":
            print(f"\nstderr={stderr}")
        if stdout!="":
            print(f"\nstdout={stdout}")


    def create_file(self, file_path):
        pass


    def delete_file(self, file_path):

        cmd = f"del {file_path}"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        if stderr!="":
            print(f"\nstderr={stderr}")
        if stdout!="":
            print(f"\nstdout={stdout}")


    def delete_directory(self, directory_path, recursive=True):

        cmd = f"rmdir /s /q {directory_path}"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        if stderr!="":
            print(f"\nstderr={stderr}")
        if stdout!="":
            print(f"\nstdout={stdout}")


    def delete_contents_under_directory(self, directory_path):
        cmd = f"cd {directory_path} & rd /s /q . 2>nul"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        if stderr!="":
            print(f"\nstderr={stderr}")
        if stdout!="":
            print(f"\nstdout={stdout}")


    def make_read_only(self, file):

        cmd = f"icacls {file} /deny \"Everyone\":(OI)(CI)(WD,AD,WEA,WA)"
        stdin, stdout, stderr = self.client.exec_command(cmd)
        stdout = stdout.read().strip().decode()
        stderr = stderr.read().strip().decode()
        if stderr!="":
            print(f"\nstderr={stderr}")
        if stdout!="":
            print(f"\nstdout={stdout}")


    def compress_file(self, file, compression_type):

        if compression_type == "zip":
            cmd = f"powershell Compress-Archive -LiteralPath {file} {file}.zip"
        elif compression_type == "tar":
            cmd = f"tar -zcvf {file}.tgz {file}"
        self.cmd(cmd)
        self.delete_file(file) # remove the original after zipping


    def path_exists(self, path):

        cmd = 'python -c  "import os;import sys;sys.stdout.write(str(os.path.exists(\'"' + path.replace('\\', '/') + '"\')))"'
        stdin, stdout, stderr = self.client.exec_command(cmd)
        return bool(stdout.read().strip().decode())


    def send(self, local_path, remote_path):

        sftp = paramiko.SFTPClient.from_transport(self.client._transport)
        sftp.put(local_path, remote_path, confirm=True)
    '''

    def run(self, app, appArguments=None):
        '''
        This dynamically supports multiple instances of any app running, ex: "notepad", "explorer"
        For each app invoked, it appends an app object to the class attribute as a collection of running apps objects

        app: name of the app to run, ex: "notepad", "explorer", "win32calc"
        '''

        # dynamically import library, and instaniate an object
        # this allows anyone to create any app for Windows without explictly importing
        # but there is a tradeoff, and that's about importing impliciitly
                                                    # ex: if app="noteped"
        instantiate = getattr(__import__(app), app) #     import notepad
        instance = instantiate(window=self)         #     instance = notepad.notepad()
        if appArguments is not None:
            instance.run(self.host, self.port, appArguments=appArguments)
        else:
            instance.run(self.host, self.port)

        # append the running app instance to the class attribute
        attribute=f"{app}s"
        if hasattr(self, attribute):
            objects=getattr(self, attribute)
            objects.append(instance)                # same as "self.notepads.append(instance)""
        else:
            setattr(self, attribute, [instance])    # same as "self.notepads = [instance]""


    def terminate(self, app):

        # close the app
        app.close()
        app.quit()

        # get the collection name of the app, ex: notepads
        # app in string usually comes in the form of "<notepad.notepad object at 0x10790b6d0>""
        # we then try to extract the app name, and form the collection name
        # ex: app name is "notepad", collection name is "notepads"
        attribute_name = f"{app}".split(".")[1].split(" ")[0]
        attribute_name = attribute_name+"s"
        attribute = getattr(self, attribute_name)

        # remove app from the collection
        attribute.remove(app)
        # temps.append(app)


    def attach_new_session_handle(self, caller, app, window_name, num_tries=12, wait_time_interval=5):
        '''
        use case: when we use file explorer to double click on any installer,  this installer app becomes
                  our focus of the automation, not the file explorer
        '''

        # switch to root session
        caller._activate_root_session()
        root =  caller.root_session
        for i in range(num_tries):
            try:
                # once in root session, find the element of the window that we want to attach to
                element = root.find_element_by_name(window_name)

                # with that found element, find its handle
                handle = element.get_attribute("NativeWindowHandle")

                # with that handle, attach
                desired_caps = {
                    "platformName":"Windows",
                    "deviceName":"WindowsPC",
                    "appTopLevelWindow":hex(int(handle))
                }
                session = webdriver.Remote(
                    command_executor = f"http://{self.host}:{self.port}/wd/hub",
                    desired_capabilities=desired_caps
                )
            except (selenium.common.exceptions.NoSuchWindowException,
                selenium.common.exceptions.NoSuchElementException) as e:

                # error message
                error_type = type(e).__name__
                error_msg = f'{e}'.rstrip()
                msg = f'try #{i}/{num_tries}, error finding element name "{window_name}", due to "{error_type}:{error_msg}"'
                print(f'{bcolors.RED}{msg}{bcolors.ENDC}')

                # wait
                time.sleep(wait_time_interval)

        # since we have attached to the new app, we need to update our Window object
        attribute_name = f"{app}s"
        if not hasattr(self, attribute_name):
            setattr(self, attribute_name, [])

        # instaniate an app
        instantiate = getattr(__import__(app), app)
        instance = instantiate(window=self)
        instance.session = session

        # add the app instance to our Windows object attribute
        attribute = getattr(self, attribute_name)
        attribute.append(instance)
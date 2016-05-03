import json
from crypt import crypt
from fabric.api import local
from fabric.api import reboot
from fabric.api import run
from fabric.api import sudo
from fabric.api import put
from fabric.api import settings


class LsbService:
    """
    Class for encapsulating LSB linux boot script for any python script.
    """

    def __init__(
            self,
            name,
            description,
            daemon,
            daemon_args,
            user,
            group='$USER',
            password='qwe123',
            work_dir='/opt/${NAME}',
            pidfile='${WORK_DIR}/${NAME}.pid',
            scriptname='/etc/init.d/$NAME',
            path='/sbin:/usr/sbin:/bin:/usr/bin',
            log_path='${WORK_DIR}/log',
            start_level='90',
            stop_level='10',
            keys=[
                'service_path',
                'service_name',
                'service_description',
                'service_daemon',
                'service_daemon_args',
                'service_work_dir',
                'service_owner',
                'space_owner',
                'service_pidfile',
                'service_scriptname',
                'service_log_path']
    ):
        """
        LSB service constructor.
        :param name: Service name.
        :param description: Service description.
        :param daemon: Daemon program (ie.: python).
        :param daemon_args: Arguments of thy daemon (ie.: machiny.py).
        :param user: System user for the application.
        :param group: System group for the application.
        :param password: Password for the system user.
        :param work_dir: Working directory of the application.
        :param pidfile: PID file location.
        :param scriptname: Name of the boot service.
        :param path: $PATH extensions dorectories.
        :param log_path: Path of the log directory..
        :param start_level: Start level of the LSB service.
        :param stop_level: Stop level of the LSB service.
        :param keys: Placeholder keys in the configuration file.
        :return:
        """
        self.config = {
            'service_name': name,
            'service_path': path,
            'service_description': description,
            'service_daemon': daemon,
            'service_daemon_args': daemon_args,
            'service_work_dir': work_dir,
            'service_owner': user,
            'space_owner': group,
            'service_pidfile': pidfile,
            'service_log_path': log_path,
            'service_scriptname': scriptname
        }
        self.keys = keys

    def generateLsbScript(self, templateLocation, output):
        """
        Generate LSB script bash file.
        :param templateLocation: Location of the template.
        :param output: Generated output location.
        :return:
        """
        local('cp ' + templateLocation + ' ' + output)

        s = open(output).read()
        for key in self.keys:
            print ('Repace placeholder <%s> = %s' % (key, self.config[key]))
            s = s.replace('<%s>' % (key), self.config[key])

        f = open(output, 'w')
        f.write(s)
        f.close()

        print ("LINUX BOOT SERVICE GENERATED: " + output)


def generate_lsb_service(config_file, output_name, templat_dir='templates/start-stop-daemon-template'):
    """
    FABRIC task for generate LSB service for the application locally.
    :param config_file: Name of the service configuration file.
    :param output_name: Generated output location.
    :param templat_dir: Location of the template.
    :return:
    """
    with open(config_file) as config:
        lsb_service_config = json.load(config)
        print (json.dumps(lsb_service_config))
        lsb_service = LsbService(
            name=lsb_service_config['service_name'],
            description=lsb_service_config['service_description'],
            daemon=lsb_service_config['service_daemon'],
            daemon_args=lsb_service_config['service_daemon_args'],
            user=lsb_service_config['service_owner'])

        lsb_service.generateLsbScript(
            templateLocation=templat_dir,
            output=output_name)


def deploy_scripts():
    """
    FABRIC task to deploy source to any endpoint.
    :return:
    """
    print("DEPLOY SCRIPTS ...")
    put("loki_common.py", "loki_common.py")
    put("loki_driver.py", "loki_driver.py")
    put("loki_rabbitmq.py", "loki_rabbitmq.py")
    put("loki_websocket.py", "loki_websocket.py")
    put("machine.py", "machine.py")


def install_linux_packages():
    """
    FABRIC task to install linux package dependecies remotely.
    :return:
    """
    sudo('apt-get install python-pip')


def install_python_modules():
    """
    FABRIC task to install python module dependencies remotely.
    :return:
    """
    sudo('pip install pika')
    sudo('pip install websocket-client')
    sudo('pip install pyusb==1.0.0b2')
    # sudo('pip install pymodbus')


def change_hostname(original, new, user, group):
    """
    FABRIC task to change hostname of any endpoint remotely.
    :param original: Original hostname.
    :param new: New hostname.
    :param user: Execute in the name of this user.
    :param group: Execute in the name of this group.
    :return:
    """
    print("TRYING CHANGE HOSTNAME FROM " + original + " TO " + new + " ...")

    if original == new:
        print ("ORIGINAL AND NEW HOSTNAME IS THE SAME NO OPERATION NEEDED")
    else:
        run('mkdir -p ./tmp')
        run('cd ./tmp')

        sudo('cp /etc/hostname ./tmp/hostname.bak')
        sudo('cp /etc/hosts ./tmp/hosts.bak')

        sudo('chown -R ' + user + ':' + group + ' ./*')

        run('sed \'s/' + original + '/' + new + '/g\' ./tmp/hostname.bak > ./tmp/hostname')
        run('sed \'s/' + original + '/' + new + '/g\' ./tmp/hosts.bak > ./tmp/hosts')

        sudo('cp ./tmp/hostname /etc/hostname')
        sudo('cp ./tmp/hosts /etc/hosts')

        sudo('hostname ' + new)

        # with settings(warn_only=True):
        #     sudo('reboot')

        # if result.failed and not confirm("Tests failed. Continue anyway?"):
        #     abort("Aborting at user request.")

        print("HOSTNAME CHANGED FROM " + original + " TO " + new + ".")


def create_space(user, group, application, password):
    """
    FABRIC task to create application space.
    - New user and group for the application.
    - Create installation directory.
    :param user: Execute in the name of this user.
    :param group: Execute in the name of this group.
    :param application: Name of the application.
    :param password: Password for the user.
    :return:
    """
    print ("CREATE SPACE FOR APPLICATION")

    with settings(warn_only=True):
        sudo(
            'echo y | echo "" | echo "" | echo "" | echo "" | echo ' + user + ' | echo ' + password + ' | echo ' + password + ' | adduser ' + user)
    with settings(warn_only=True):
        crypted_password = crypt(password, 'salt')
        sudo('usermod --password %s %s' % (crypted_password, user), pty=False)
    with settings(warn_only=True):
        sudo('addgroup ' + group)
    with settings(warn_only=True):
        sudo('adduser ' + user + ' ' + group)
    sudo('adduser ' + user + ' ' + 'sudo')
    with settings(warn_only=True):
        sudo('mkdir -p /opt/' + application)
        sudo('mkdir -p /opt/' + application + '/log')
        sudo('echo "Error log" >> /opt/' + application + '/log/' + application + '.err')
        sudo('echo "Output log" >> /opt/' + application + '/log/' + application + '.out')
        sudo('usermod -m -d /opt/' + application + ' -m ' + user)

    # with settings(warn_only=True):
    #     sudo('mkdir -p /opt/' + application)
    with settings(warn_only=True):
        sudo('chown -R ' + user + ':' + group + ' /opt/' + application)


def install_service(scriptfile, start_level="90", stop_level="10"):
    """
    FABRIC task to install LSB service remotely.
    :param scriptfile: Name of the local and remote scriptfile.
    :param start_level: Service starting level
    :param stop_level: Service stopping level
    :return:
    """
    print ("INSTALL LSB SERVICE " + scriptfile + " FOR APPLICATION ")
    run('mkdir -p ~/tmp')
    put(scriptfile, '~/tmp/' + scriptfile)

    run('chmod a+x ' + "~/tmp/" + scriptfile)

    sudo('mv /opt/' + scriptfile + '/tmp/' + scriptfile + ' /etc/init.d/' + scriptfile)

    sudo('update-rc.d -f ' + scriptfile + ' remove')
    sudo('update-rc.d ' + scriptfile + ' defaults ' + start_level + ' ' + stop_level)

    with settings(warn_only=True):
        sudo('systemctl daemon-reload')
    run('rm -r ./tmp')


def reboot_machine():
    """
    FABRIC task to reboot machine remotely.
    :return:
    """
    with settings(warn_only=True):
        reboot()


def clean_install():
    """
    FABRIC task to initialize system to endpoint. Create application space, install linux and python dependecies.
    :return:
    """
    create_space('loki', 'cherubits', 'loki_machine', 'qwe123')
    install_linux_packages()
    install_python_modules()


def init_system():
    """
    FABRIC task to install system. Create LSB service, deploy source, reboot ednpoint.
    :return:
    """
    deploy_scripts()
    install_service('loki_machine', 'loki')
    reboot_machine()

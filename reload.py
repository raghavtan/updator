#!/usr/bin/python
__author__ = 'rt'

import ConfigParser
import os
import urllib2
from subprocess import PIPE, Popen
import zipfile
import logging
import subprocess
import shlex
from logging import config

try:
    import yaml
except:
    pass
import argparse

#################  LOGGING CONFIGS  ######################
config_file = "logging.yml"
level = logging.INFO
##########################################################
"""
LOGGER INITIALIZE
"""
##########################################################
if os.path.exists(config_file):
    with open(config_file, 'rt') as f:
        cfg_yaml = yaml.load(f.read())
    logging.config.dictConfig(cfg_yaml)
else:
    logging.basicConfig(level=level)
logger = logging.getLogger(__name__)


##########################################################

##################################################################################
def parse_args():
    """
    :return:
    """
    global parser
    parser = argparse.ArgumentParser(description='Updation utilities')
    parser.add_argument("path", help='specify the home path for application directory to be updated')
    parser.add_argument("url", help='specify the url to fetch tar')
    parser.add_argument("-e", "--extra-args", help='Arguments for shell script eg -e ARG1,ARG2,ARG3....')
    return parser.parse_args()


###################################################################################

class updation:
    """
    BASE CLASS FOR UPDATING
    """

    def __init__(self, app_home_dir, get_url):
        """
        :param app_home_dir: home directory for the application eg /opt/zookeeper/application_to_be_refreshed/
        :param get_url: URL to download tar for new application files
        :return:
        """
        self.app_home_dir = app_home_dir
        self.wd = os.path.abspath(os.path.join(self.app_home_dir, ".."))
        self.get_path = os.path.abspath(os.path.join(self.wd, "tmp"))
        os.system("mkdir -p %s" % self.get_path)
        self.buildInfo_path = os.path.abspath(os.path.join(self.get_path, "buildinfo.ini"))
        self.get_url = get_url
        self.extract_path = os.path.abspath(os.path.join(self.get_path, "build"))

    def get_app(self):
        """
        Just Download and unpack the tar from link
        :return: None
        """
        try:
            app_file = urllib2.urlopen(self.get_url)
            with open("%s.tar" % self.get_path, 'wb') as output:
                output.write(app_file.read())
            logger.info("Downloaded %s.tar" % self.get_path)
            logger.info("Unpacking %s" % self.get_path)
            unpack_cmd = "tar -xvf %s.tar -C %s" % (self.get_path, self.get_path)
            result = Popen(unpack_cmd, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = result.communicate()
            if stderr:
                logger.info(stderr)
        except:
            raise

    def unpack_replace(self, zip_path):
        """
        :param zip_path: Unpack application files zip file within the tar
        :return: None
        """
        try:
            z = zipfile.ZipFile(zip_path)
            z.extractall(self.extract_path)
            logger.info("Unpacking %s" % self.extract_path)
        except:
            raise
        try:
            logger.info("Copying new files to %s" % self.app_home_dir)
            replace_cmd = "cp -Prf %s/* %s/" % (self.extract_path.rstrip("/"), self.app_home_dir)
            result = Popen(replace_cmd, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = result.communicate()
            logger.info(stdout)
            if stderr:
                logger.info(stderr)
            logger.info("Copying new buildinfo.ini to %s" % self.app_home_dir)
            copy_buildinfo = "cp -f %s %s/buildinfo.ini" % (self.buildInfo_path, self.app_home_dir)
            result = Popen(copy_buildinfo, stdout=PIPE, stderr=PIPE, shell=True)
            stdout, stderr = result.communicate()
            logger.info(stdout)
            if stderr:
                logger.info(stderr)
        except:
            raise

    def read_revision(self):
        """
        Read revision from the unpacked tar buildInfo.ini
        buildinfo file format
        ###############################################################
        [default]
        app_name=<name>
        revision=<revision number>
        ###############################################################
        :return: None
        """
        try:
            cfg_revision_new = ConfigParser.ConfigParser()
            cfg_revision_new.read(self.buildInfo_path)
            revision_new = cfg_revision_new.get('default', 'revision')
            logger.info("New revision %s" % revision_new)
            cfg_revision_old = ConfigParser.ConfigParser()
            cfg_revision_old.read(os.path.abspath(os.path.join(self.app_home_dir, "buildinfo.ini")))
            revision_old = cfg_revision_old.get('default', 'revision')
            logger.info("Old revision %s" % revision_old)
            return revision_new, revision_old
        except:
            raise

    def shell_execute(self, shell_file=None, args_list=None):
        try:
            if shell_file:
                if args_list:
                    args = args_list
                else:
                    args = ""
                shell_script = os.path.abspath(os.path.join(self.get_path, shell_file))
                subprocess.call(shlex.split('./%s %s') % (shell_script, args))
        except:
            raise

    def cleanUp(self):
        try:
            if os.path.exists(self.get_path):
                logger.info("Cleaning up temporary files")
                os.rmdir(self.get_path)
        except:
            raise


def main():
    args = parse_args()
    if args.path and args.url:
        arguments = None
        if args.extra_args:
            arguments = args.extra_args.replace(",", " ")
        logger.info("Application home : %s" % args.path)
        logger.info("Url to download : %s" % args.url)
        RUpdate = updation(args.path, args.url)
        RUpdate.get_app()
        rev_new, rev_old = RUpdate.read_revision()
        if rev_new > rev_old:
            shell_file = None
            files = os.listdir(RUpdate.get_path)
            for file in files:
                if file.endswith(".zip"):
                    RUpdate.unpack_replace(os.path.abspath(os.path.join(RUpdate.get_path, file)))
                elif file.endswith(".sh"):
                    shell_file = file
            RUpdate.shell_execute(shell_file, arguments)
        RUpdate.cleanUp()
    else:
        print parser.print_help()


if __name__ == '__main__':
    main()

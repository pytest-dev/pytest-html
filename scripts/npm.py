import subprocess

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class NpmBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        subprocess.check_output("npm ci", shell=True)
        subprocess.check_output("npm run build", shell=True)

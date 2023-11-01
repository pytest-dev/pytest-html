import subprocess
from pathlib import Path

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class NpmBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        is_source = Path(self.root, ".git").exists()
        app_js_exists = Path(
            self.root, "src", "pytest_html", "resources", "app.js"
        ).exists()
        if is_source or not app_js_exists:
            subprocess.run("npm ci", capture_output=True, check=True, shell=True)
            subprocess.run("npm run build", capture_output=True, check=True, shell=True)

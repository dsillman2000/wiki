"""Hatchling build hooks for wiki-client."""

from pathlib import Path

from hatchling.builders.hooks.custom import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Custom build hook to generate _version.py with dynamic version."""

    def initialize(self, version, build_data):
        """Initialize hook and generate _version.py."""
        version_file = Path(self.root) / "wiki_client" / "_version.py"
        version_file.write_text(
            f'"""Auto-generated version file."""\nversion = "{version}"\n'
        )

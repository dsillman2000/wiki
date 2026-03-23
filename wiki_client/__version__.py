"""Version information for wiki-client."""

try:
    from wiki_client._version import version as __version__
except ImportError:
    __version__ = "0.0.0"

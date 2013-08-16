import sys

from ..discover_providers import discover_providers

# Note: these tests will be run in the context of "helper_project/"

def test_discover_providers():
    """Test that discover_providers will actually discover and import a
       module."""

    def find_helper_module():
        for mod in sys.modules.iterkeys():
            if "example_provider" in mod:
                return mod
        return None

    # Make sure that the 'example_provider' module isn"t already in
    # sys.modules
    if find_helper_module():
        del sys.modules[find_helper_module()]

    discover_providers("example_provider")

    # Make sure the module has been re-added to sys.modules (that is, it has
    # been imported)
    assert find_helper_module()

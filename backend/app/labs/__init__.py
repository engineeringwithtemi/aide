"""Labs package.

Lab implementations are auto-registered via @register_lab decorator.
Auto-discovery happens when _discover_labs() is called from the routes module.
"""


def _discover_labs():
    """Auto-discover and import all lab implementations.

    This function should be called from lab routes to trigger the
    @register_lab decorator in all lab modules.

    This delayed import pattern avoids circular import issues.
    """
    import importlib
    import pkgutil
    from pathlib import Path

    package_dir = Path(__file__).parent

    # Import all Python modules in this package (except __init__.py and base.py)
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        module_name = module_info.name

        # Skip base module (abstract class, not a concrete lab)
        if module_name == "base":
            continue

        # Import the module to trigger @register_lab decorator
        importlib.import_module(f"app.labs.{module_name}")

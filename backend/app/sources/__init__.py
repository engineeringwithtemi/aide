"""Sources package.

Source implementations are auto-registered via @register_source decorator.
Auto-discovery happens when _discover_sources() is called from the routes module.
"""


def _discover_sources():
    """Auto-discover and import all source implementations.

    This function is called from app.routes.v1.sources to trigger the
    @register_source decorator in all source modules.

    This delayed import pattern avoids circular import issues:
    - registry.py can import app.sources.base without triggering full package load
    - Source implementations are only imported when routes are loaded
    - By that time, registry.py is fully initialized
    """
    import importlib
    import pkgutil
    from pathlib import Path

    package_dir = Path(__file__).parent

    # Import all Python modules in this package (except __init__.py and base.py)
    for module_info in pkgutil.iter_modules([str(package_dir)]):
        module_name = module_info.name

        # Skip base module (abstract class, not a concrete source)
        if module_name == "base":
            continue

        # Import the module to trigger @register_source decorator
        importlib.import_module(f"app.sources.{module_name}")

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
    from pykka import ActorProxy
    from pykka._types import AttrPath

logger = logging.getLogger("pykka")


class AttrInfo(NamedTuple):
    callable: bool
    traversable: bool


def introspect_attrs(
    *,
    root: Any,
    proxy: ActorProxy[Any],
) -> dict[AttrPath, AttrInfo]:
    """Introspects the actor's attributes."""
    result: dict[AttrPath, AttrInfo] = {}
    attr_paths_to_visit: list[AttrPath] = [(attr_name,) for attr_name in dir(root)]

    while attr_paths_to_visit:
        attr_path = attr_paths_to_visit.pop(0)

        if attr_path[-1].startswith("_"):
            # Attribute names starting with _ are considered private and are
            # not exposed via ActorProxy.
            continue

        attr = get_attr_from_parent(root, attr_path)

        if attr == proxy:
            logger.warning(
                f"{root} attribute {'.'.join(attr_path)!r} "
                f"is a proxy to itself. "
                f"Consider making it private "
                f"by renaming it to {'_' + attr_path[-1]!r}."
            )
            continue

        attr_info = AttrInfo(
            callable=callable(attr),
            traversable=(
                getattr(attr, "_pykka_traversable", False) is True
                or getattr(attr, "pykka_traversable", False) is True
            ),
        )
        result[attr_path] = attr_info

        if attr_info.traversable:
            for attr_name in dir(attr):
                attr_paths_to_visit.append((*attr_path, attr_name))

    return result


def get_attr_from_parent(
    root: Any,
    attr_path: AttrPath,
) -> Any:
    """Get attribute information from ``__dict__`` on the parent."""
    parent = get_attr_directly(root, attr_path[:-1])
    parent_attrs = get_obj_dict(parent)
    attr_name = attr_path[-1]

    try:
        return parent_attrs[attr_name]
    except KeyError:
        raise AttributeError(
            f"type object {parent.__class__.__name__!r} "
            f"has no attribute {attr_name!r}"
        ) from None


def get_attr_directly(
    root: Any,
    attr_path: AttrPath,
) -> Any:
    """Traverses the path and returns the attribute at the end of the path."""
    attr = root
    for attr_name in attr_path:
        attr = getattr(attr, attr_name)
    return attr


def get_obj_dict(obj: Any) -> dict[str, Any]:
    """Combine ``__dict__`` from ``obj`` and all its superclasses."""
    result: dict[str, Any] = {}
    for cls in reversed(obj.__class__.mro()):
        result.update(cls.__dict__)
    if hasattr(obj, "__dict__"):
        result.update(obj.__dict__)
    return result

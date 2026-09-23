from __future__ import annotations

from prlab_eval.tools.greptile import GreptileTool

TOOLS = {
    GreptileTool.name: GreptileTool(),
}


def get_tool(name: str):
    try:
        return TOOLS[name]
    except KeyError as exc:
        known = ", ".join(sorted(TOOLS))
        raise SystemExit(f"unknown tool {name!r}. registered: {known}") from exc

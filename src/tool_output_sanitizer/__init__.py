"""Token-level sanitizer for indirect prompt injections in agent tool outputs."""

__version__ = "0.1.0"
__all__ = ["Sanitizer"]


def __getattr__(name: str):
    if name == "Sanitizer":  # imported on demand so that the MCP proxy and the hook start without loading torch
        from tool_output_sanitizer.sanitizer import Sanitizer
        return Sanitizer
    raise AttributeError(name)

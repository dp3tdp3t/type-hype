"""Bundled, hand-curated content used by the source modules.

This module exists primarily so the folder is a regular Python
package rather than an implicit namespace package — PyInstaller's
static analyzer reliably bundles regular packages, but can miss
namespace packages and crash the packaged app with
`ModuleNotFoundError: No module named 'engine.sources.data'`.
"""

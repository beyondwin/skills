# beyondwin-skills catalog

`beyondwin-skills` is a separately versioned Codex plugin catalog. It does not own skill product contracts. It adopts already-released skill versions and ships them together as a plugin bundle.

The last published catalog identity is `beyondwin-skills` `2.0.0`. That release locks the public `v2.0.0` standalone payloads for `image-workbench` and `korean-writing-editor`. Current `skills/` development, including unpublished `graspic`, is not the catalog source.

This catalog's contract is: only released plugin ZIPs are supported catalog artifacts; the repository root is for individual skill installs. Plugin metadata for catalog builds lives at `plugin/.codex-plugin/plugin.json` and is copied to the plugin ZIP root at catalog release time. `catalog.lock.json` records the immutable skill releases the catalog adopted.

# grok-video compatibility

Supported host is `grok`, as listed in the registry. Another host with a video
tool is not supported by that fact alone.

## Supported OS

macOS is the only supported OS. Windows and Linux are unsupported. CI may run
full verification on Ubuntu. That pass is not Linux support and is not macOS
support evidence.

## Required host abilities

- The skill is installed where Grok reads skills.
- `reference_to_video`, `image_gen`, and `image_edit` are available.
- The user can open the mp4.

The public support sentence is: grok-video: Grok supported; a clip needs the host reference_to_video tool and a way to open the result.

## Evidence without provider calls

The required evidence is `python3 scripts/verify.py --skill grok-video`.
Planner tests prove the ask, the pins, and the defaults. They do not prove
that a clip looks good.

Live clip checks are local, optional, and billable. CI does not require them.
Do not commit generated media, private references, credentials, or provider receipts.

## Adding a host

Do not claim Codex, Claude Code, or Cursor until a recorded smoke on that host
shows a video request loading this skill and a still request leaving it alone.
The shared user guide is [Compatibility](../../../users/en/compatibility.md).

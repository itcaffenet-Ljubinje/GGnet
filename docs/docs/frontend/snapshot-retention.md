# Snapshot & Writeback Retention Plan

## Scope
- Complementary documentation for managing snapshot/writeback retention policies and automation.
- Intended for inclusion in operations/administration docs.
- Based on Confluence export `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`.

## Audience
- System administrators needing to tune retention for their array.
- Support engineers guiding customers through cleanup configurations.

## Overview
- Explain why snapshots/writebacks accumulate and potential impact (array saturation, blocked PXE boots).
- Define key terms:
  - **Unutilized Snapshots** – snapshots not used by any machine over X days.
  - **Unprotected Snapshots** – snapshots not marked as protected/locked.
  - **Inactive Writebacks** – writebacks for machines that have remained offline for X days.

## Recommended Workflow
1. **Assess usage**
   - Review array capacity, reserved space, and growth trends.
   - Identify machines with “Keep Writebacks” enabled (exclude from automation).

2. **Configure retention**
   - Navigate to `Settings → Array & Images`.
   - Set values for unutilized/unprotected/inactive thresholds following support recommendations (provide table of suggested defaults by array size).
   - Enable automation toggle.

3. **Monitor results**
   - Check last cleanup summary (deleted snapshots count, freed space).
   - Respond to warnings (e.g., automation paused, failures).

4. **Manual interventions**
   - Protect critical snapshots before major updates.
   - Use “Run Cleanup Now” for urgent space recovery.
   - Remove “Keep Writebacks” flag when no longer needed.

## Operational Tips
- Schedule automation during maintenance windows to avoid user impact.
- Regularly review protected snapshot list and prune outdated entries.
- When array is near capacity, consider:
  - Increasing reserved disk space temporarily.
  - Exporting or archiving older snapshots externally.

## Troubleshooting
- Cleanup failed because snapshot in use: instruct to reboot machines or adjust snapshot selection.
- Writeback deletion blocked: verify machine status and “Keep Writebacks” setting.
- Automation disabled unexpectedly: check audit logs or upcoming maintenance windows.

## Related Docs & Links
- `docs/frontend/array-automation.md` (UI plan)
- `docs/frontend/array.md` (array dashboard features)
- Confluence export: `GGROCK/docs/Automated+Snapshot+and+Writeback+Removal.doc`


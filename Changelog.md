## Unreleased

- Added Action Bakery rig pairs so one source action can bake multiple control/game rig pairs into one shared multi-slot baked action.
- Fixed overwrite cleanup for multi-rig bakes when Blender removes an action that was active before baking.
- Removed the standalone Control Rig/Game Rig panel controls; selected rig-pair rows now drive pair-specific controls.
- Changed Connect/Disconnect and Toggle Rig controls to apply to every complete rig pair, with Toggle Rig using the first pair as the visibility basis.
- Baked NLA tracks now use the original source action name while keeping the baked action name on the strip/action.
- Fixed Generate/Regenerate Game Rig buttons so they open the options dialog from the side panel.
- Restored the Regenerate Game Rig dialog options by drawing them from the same settings path as the original generator UI.

GRT v4.2.1 - 06/8/2024

## Summary

- Regenerate Rig will no longer throw and error when no rig is provided and will generate a new rig instead
- Push To NLA now Also Rename NLA Tracks
- If Overwrite and Push To NLA is on, the Addon will Remove Strips that have the Baked Actions, it will also remove empty tracks (no strip) that have the same name as the action (track name)

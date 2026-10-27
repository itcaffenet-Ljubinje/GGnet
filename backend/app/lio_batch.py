"""
lio_batch: several LIO changes in one process, through rtslib-fb (the
library targetcli itself uses), for ISCSIManager.

Every targetcli call starts Python, loads the whole LIO configuration and
exits: about half a second each, and a restarting PC waited for about a
dozen of them. This script runs the same steps in one go. It is started
with the system Python (where Debian's python3-rtslib-fb lives), not the
backend's virtualenv:

    /usr/bin/python3 -I lio_batch.py '<JSON list of steps>'

and prints {"ok": true, "results": [...]} or {"ok": false, "failed": i,
"error": "...", "results": [...]} (exit 1). Exit 3 means rtslib-fb is not
installed; the caller then falls back to targetcli. Steps run in order and
stop at the first failure; the caller cleans up, as it does after a failed
targetcli command.

Steps ({"op": ..., ...}):
  delete_acl        target, initiator             (missing is fine)
  delete_backstore  name                          (its LUNs and mappings go too; missing is fine)
  delete_target     target                        (missing is fine)
  list_backstores                                 -> block backstore names
  create_backstore  name, dev                     (as targetcli: model alias = name)
  create_lun        target, backstore             -> the TPG LUN index (lowest free)
  create_acl        target, initiator
  map_lun           target, initiator, mapped_lun, backstore
  save                                            (/etc/rtslib-fb-target/saveconfig.json)

Only this file and the JSON from ISCSIManager are trusted: names and paths
are validated there before any step is sent.
"""

import json
import sys


def main(argv):
    try:
        steps = json.loads(argv[1])
    except (IndexError, ValueError) as e:
        print(json.dumps({"ok": False, "error": f"bad steps: {e}"}))
        return 2
    try:
        from rtslib_fb import BlockStorageObject, FabricModule, LUN, MappedLUN, NodeACL, RTSRoot, Target, TPG
        from rtslib_fb.root import default_save_file
        from rtslib_fb.utils import RTSLibNotInCFS
    except ImportError as e:
        print(json.dumps({"ok": False, "error": f"rtslib-fb is not available: {e}", "unavailable": True}))
        return 3

    fabric = FabricModule("iscsi")

    def tpg(iqn):
        return TPG(Target(fabric, iqn, mode="lookup"), 1, mode="lookup")

    def lun_of(t, backstore):
        for lun in t.luns:
            if lun.storage_object.name == backstore:
                return lun
        raise RuntimeError(f"no LUN for backstore {backstore}")

    def run(step):
        op = step["op"]
        if op == "delete_acl":
            try:
                NodeACL(tpg(step["target"]), step["initiator"], mode="lookup").delete()
            except RTSLibNotInCFS:
                pass
            return None
        if op == "delete_backstore":
            try:
                BlockStorageObject(step["name"]).delete()     # its LUNs (and their mappings) first
            except RTSLibNotInCFS:
                pass
            return None
        if op == "delete_target":
            try:
                Target(fabric, step["target"], mode="lookup").delete()
            except RTSLibNotInCFS:
                pass
            return None
        if op == "list_backstores":
            return sorted(so.name for so in RTSRoot().storage_objects if so.plugin == "block")
        if op == "create_backstore":
            so = BlockStorageObject(step["name"], dev=step["dev"])
            # targetcli's export_backstore_name_as_model: Windows sees the
            # backstore name as the disk model, as before.
            so.set_attribute("emulate_model_alias", 1)
            # Windows sees a disk with a write cache and groups its writes instead of
            # flushing each one; the writeback zvols are sync=disabled anyway.
            so.set_attribute("emulate_write_cache", 1)
            return None
        if op == "create_lun":
            t = tpg(step["target"])
            used = {lun.lun for lun in t.luns}
            index = next(i for i in range(len(used) + 1) if i not in used)
            LUN(t, index, storage_object=BlockStorageObject(step["backstore"]))
            return index
        if op == "create_acl":
            NodeACL(tpg(step["target"]), step["initiator"], mode="create")
            return None
        if op == "map_lun":
            t = tpg(step["target"])
            acl = NodeACL(t, step["initiator"], mode="lookup")
            MappedLUN(acl, int(step["mapped_lun"]), tpg_lun=lun_of(t, step["backstore"]), write_protect=False)
            return None
        if op == "save":
            RTSRoot().save_to_file(default_save_file)
            return None
        raise RuntimeError(f"unknown step {op!r}")

    results = []
    for i, step in enumerate(steps):
        try:
            results.append(run(step))
        except Exception as e:      # report which step failed and why; the caller cleans up
            print(json.dumps({"ok": False, "failed": i, "error": f"{step.get('op')}: {e}", "results": results}))
            return 1
    print(json.dumps({"ok": True, "results": results}))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))

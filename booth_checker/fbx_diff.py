import os
from collections import Counter, defaultdict


def _normalize_fbx_entries(fbx_records):
    entries = []
    for path_str, file_hash in sorted(fbx_records.items()):
        entries.append(
            {
                "path": path_str,
                "basename": os.path.basename(path_str),
                "hash": file_hash,
            }
        )
    return entries


def _remove_exact_name_hash_matches(previous_entries, current_entries):
    previous_by_key = defaultdict(list)
    current_by_key = defaultdict(list)

    for entry in previous_entries:
        previous_by_key[(entry["basename"], entry["hash"])].append(entry)
    for entry in current_entries:
        current_by_key[(entry["basename"], entry["hash"])].append(entry)

    remaining_previous = []
    remaining_current = []

    for key in sorted(set(previous_by_key) | set(current_by_key)):
        previous_list = previous_by_key.get(key, [])
        current_list = current_by_key.get(key, [])
        shared_count = min(len(previous_list), len(current_list))

        remaining_previous.extend(previous_list[shared_count:])
        remaining_current.extend(current_list[shared_count:])

    return remaining_previous, remaining_current


def calculate_fbx_diff(previous_fbx, current_fbx):
    previous_entries = _normalize_fbx_entries(previous_fbx)
    current_entries = _normalize_fbx_entries(current_fbx)

    remaining_previous, remaining_current = _remove_exact_name_hash_matches(
        previous_entries, current_entries
    )

    previous_by_name = defaultdict(list)
    current_by_name = defaultdict(list)

    for entry in remaining_previous:
        previous_by_name[entry["basename"]].append(entry)
    for entry in remaining_current:
        current_by_name[entry["basename"]].append(entry)

    added = []
    changed = []
    deleted = []

    for name in sorted(set(previous_by_name) | set(current_by_name)):
        previous_list = sorted(
            previous_by_name.get(name, []),
            key=lambda entry: (entry["hash"], entry["path"]),
        )
        current_list = sorted(
            current_by_name.get(name, []),
            key=lambda entry: (entry["hash"], entry["path"]),
        )

        shared_count = min(len(previous_list), len(current_list))
        for index in range(shared_count):
            changed.append(
                {
                    "basename": name,
                    "previous_hash": previous_list[index]["hash"],
                    "current_hash": current_list[index]["hash"],
                    "previous_path": previous_list[index]["path"],
                    "current_path": current_list[index]["path"],
                }
            )

        deleted.extend(previous_list[shared_count:])
        added.extend(current_list[shared_count:])

    return added, changed, deleted


def _short_hash(file_hash):
    return file_hash[:8]


def _append_path_context(label, basename, basename_counts, previous_path=None, current_path=None):
    is_ambiguous_name = basename_counts[basename] > 1
    path_changed = previous_path and current_path and previous_path != current_path

    if not is_ambiguous_name and not path_changed:
        return label

    if previous_path and current_path:
        if previous_path == current_path:
            return f"{label} {{{current_path}}}"
        return f"{label} {{from {previous_path} -> {current_path}}}"

    path_value = current_path or previous_path
    return f"{label} {{{path_value}}}"


def build_fbx_path_list(added_entries, changed_entries, deleted_entries):
    basename_counts = Counter()

    for entry in added_entries:
        basename_counts[entry["basename"]] += 1
    for entry in changed_entries:
        basename_counts[entry["basename"]] += 1
    for entry in deleted_entries:
        basename_counts[entry["basename"]] += 1

    path_list = []

    for entry in added_entries:
        label = _append_path_context(
            entry["basename"],
            entry["basename"],
            basename_counts,
            current_path=entry["path"],
        )
        path_list.append(
            {
                "line_str": f"{label} [new {_short_hash(entry['hash'])}]",
                "status": 1,
            }
        )

    for entry in changed_entries:
        label = _append_path_context(
            entry["basename"],
            entry["basename"],
            basename_counts,
            previous_path=entry["previous_path"],
            current_path=entry["current_path"],
        )
        path_list.append(
            {
                "line_str": (
                    f"{label} "
                    f"[{_short_hash(entry['previous_hash'])} -> {_short_hash(entry['current_hash'])}]"
                ),
                "status": 3,
            }
        )

    for entry in deleted_entries:
        label = _append_path_context(
            entry["basename"],
            entry["basename"],
            basename_counts,
            previous_path=entry["path"],
        )
        path_list.append(
            {
                "line_str": f"{label} [old {_short_hash(entry['hash'])}]",
                "status": 2,
            }
        )

    return path_list

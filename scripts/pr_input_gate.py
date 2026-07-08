from pr_input_guard import block_raw_source, evaluate_record


def gate_raw_source_export(*args, **kwargs):
    return block_raw_source(*args, **kwargs)


def gate_canonical_site_record(record, profile, *, scope, dry_run=False):
    return evaluate_record(record, profile, scope=scope, dry_run=dry_run)

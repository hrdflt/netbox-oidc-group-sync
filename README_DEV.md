# Developer Guide — NetBox OIDC Group Sync Plugin

This guide covers development workflow, iteration, and troubleshooting for contributors.

> **Tested on:** NetBox 4.5.3, Python 3.12, PostgreSQL 16  
> **Compatibility:** NetBox 4.0+ (only 4.5.3 verified)

## Table of Contents

- [Development Setup](#development-setup)
- [Edit → Deploy → Test Cycle](#edit--deploy--test-cycle)
- [Pip Caching Gotcha](#pip-caching-gotcha)
- [Database Management](#database-management)
  - [Clean Install](#clean-install)
  - [Full Wipe and Reinstall](#full-wipe-and-reinstall)
  - [Audit Current State](#audit-current-state)
- [Migration Development](#migration-development)
- [Complete Uninstall](#complete-uninstall)
- [Troubleshooting](#troubleshooting)

---

## Development Setup

```bash
# Clone the repo
git clone <repo-url> netbox-oidc-group-sync
cd netbox-oidc-group-sync

# Install in your NetBox venv
source /opt/netbox/venv/bin/activate
pip install --no-cache-dir /path/to/netbox-oidc-group-sync/

# Add to configuration.py
# PLUGINS = ['netbox_oidc_group_sync']

# Run migrations
cd /opt/netbox/netbox
python manage.py migrate netbox_oidc_group_sync

# Restart
sudo systemctl restart netbox netbox-rq
```

Expected migration output on first run:

```
Operations to perform:
  Apply all migrations: netbox_oidc_group_sync
Running migrations:
  Applying netbox_oidc_group_sync.0001_initial... OK
```

---

## Edit → Deploy → Test Cycle

After making code changes:

```bash
# 1. Copy updated source to server (if developing locally)
rsync -av netbox-oidc-group-sync/ server:/opt/netbox-plugins/netbox-oidc-group-sync/

# 2. Reinstall — MUST use --no-cache-dir --force-reinstall
#    (see "Pip Caching Gotcha" below)
pip install --no-cache-dir --force-reinstall /opt/netbox-plugins/netbox-oidc-group-sync/

# 3. Apply any new migrations
cd /opt/netbox/netbox
python manage.py migrate netbox_oidc_group_sync

# 4. Restart NetBox (gunicorn caches Python modules in worker memory)
sudo systemctl restart netbox netbox-rq
```

---

## Pip Caching Gotcha

⚠️ **Critical:** Pip caches built wheels by package name + version. If you reinstall the same version (`0.1.0`) after changing code, **pip may serve the cached wheel with old code**.

**Always use `--no-cache-dir --force-reinstall`** during development:

```bash
# WRONG — may install stale cached code
pip install /path/to/netbox-oidc-group-sync/

# CORRECT — forces rebuild from source
pip install --no-cache-dir --force-reinstall /path/to/netbox-oidc-group-sync/
```

To verify the installed code matches your source:

```bash
# Check where pip installed it
pip show netbox-oidc-group-sync | grep Location

# Verify a specific file (replace Location path)
grep "class OIDCGroupSyncConfig" $(pip show netbox-oidc-group-sync 2>/dev/null | grep Location | cut -d' ' -f2)/netbox_oidc_group_sync/models.py
```

To nuke the pip cache entirely:

```bash
pip cache purge
```

---

## Database Management

### Clean Install

For a brand-new installation (no existing tables):

```bash
cd /opt/netbox/netbox
python manage.py migrate netbox_oidc_group_sync
```

### Full Wipe and Reinstall

If you need to start fresh (e.g., migration schema changed during development):

> ⚠️ **This deletes ALL plugin data.** Only use during development.

```bash
# Step 1: Drop all plugin tables and clear migration records
cd /opt/netbox/netbox && python manage.py dbshell <<'EOF'
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupmapping_tags CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupmapping CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupsyncconfig_tags CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupsyncconfig CASCADE;
DELETE FROM django_migrations WHERE app = 'netbox_oidc_group_sync';
EOF
```

Expected output:

```
DROP TABLE
DROP TABLE
DROP TABLE       (or NOTICE: table does not exist, skipping)
DROP TABLE       (or NOTICE: table does not exist, skipping)
DELETE 1
```

```bash
# Step 2: Re-apply migrations from scratch
cd /opt/netbox/netbox && python manage.py migrate netbox_oidc_group_sync
```

Expected output:

```
Operations to perform:
  Apply all migrations: netbox_oidc_group_sync
Running migrations:
  Applying netbox_oidc_group_sync.0001_initial... OK
```

```bash
# Step 3: Restart
sudo systemctl restart netbox netbox-rq
```

### Audit Current State

To inspect what's actually in the database:

```bash
cd /opt/netbox/netbox && python manage.py dbshell <<'EOF'
-- What tables exist?
SELECT tablename FROM pg_tables WHERE tablename LIKE 'netbox_oidc_group_sync%';

-- Config table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'netbox_oidc_group_sync_oidcgroupsyncconfig'
ORDER BY ordinal_position;

-- Mapping table columns
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'netbox_oidc_group_sync_oidcgroupmapping'
ORDER BY ordinal_position;

-- Applied migrations
SELECT * FROM django_migrations WHERE app = 'netbox_oidc_group_sync';
EOF
```

To check what Django thinks needs to change vs. what's in the migration:

```bash
cd /opt/netbox/netbox && python -c "
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'netbox.settings'
django.setup()
from django.db.migrations.autodetector import MigrationAutodetector
from django.db.migrations.state import ProjectState
from django.db.migrations.loader import MigrationLoader
loader = MigrationLoader(None, ignore_no_migrations=True)
autodetector = MigrationAutodetector(loader.project_state(), ProjectState.from_apps(django.apps.apps))
changes = autodetector.changes(graph=loader.graph)
for app, migrations in changes.items():
    for m in migrations:
        for op in m.operations:
            print(f'{app}: {op.describe()}')
if not changes:
    print('No pending changes — migration matches models.')
"
```

---

## Migration Development

> **Important:** NetBox 4.5.3 blocks `makemigrations` for plugins by default. You must generate migrations in a standalone Django project or write them manually.

### Why `migrate zero` can fail

Django's `migrate zero` unapplies migrations in reverse. If you modified a migration file **after** it was already applied (e.g., added columns), Django tries to drop tables/columns that don't exist in the database, causing errors like:

```
table "..._tags" does not exist
```

**Solution:** Use the "Full Wipe and Reinstall" procedure above instead of `migrate zero`.

### Migration + model alignment

The migration file **must exactly match** the model's fields at the time Django applies it. If models inherit from `NetBoxModel`, the migration must include `custom_field_data`, `tags`, `created`, `last_updated` fields — these come from the parent class.

---

## Complete Uninstall

To completely remove the plugin:

```bash
# 1. Remove from PLUGINS in configuration.py
# PLUGINS = ['netbox_oidc_group_sync']  ← remove this line

# 2. Drop database tables and migration records
cd /opt/netbox/netbox && python manage.py dbshell <<'EOF'
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupmapping_tags CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupmapping CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupsyncconfig_tags CASCADE;
DROP TABLE IF EXISTS netbox_oidc_group_sync_oidcgroupsyncconfig CASCADE;
DELETE FROM django_migrations WHERE app = 'netbox_oidc_group_sync';
EOF

# 3. Uninstall the Python package
pip uninstall -y netbox-oidc-group-sync

# 4. Restart
sudo systemctl restart netbox netbox-rq
```

---

## Troubleshooting

### "models have changes that are not yet reflected in a migration"

This warning appears when the migration file doesn't perfectly match Django's model introspection. Common causes:

1. **NetBoxModel base class evolved** — NetBox 4.5.3's `NetBoxModel` may define `custom_field_data` or `tags` slightly differently than what's in the migration. Run the audit script above to check.
2. **Model was changed without updating the migration** — Use "Full Wipe and Reinstall" to reset.
3. **Cosmetic differences** — Minor field attribute changes (e.g., `encoder=None` vs no encoder) that don't affect the database schema. Safe to ignore.

### "column X does not exist" on page load

The installed model code expects columns that don't exist in the database. This means either:
- The migration wasn't applied after a code update
- The code is stale (pip cache — see "Pip Caching Gotcha")

Fix: verify installed code, reinstall with `--no-cache-dir --force-reinstall`, then run migrations.

### "'auth-api' is not a registered namespace"

This happens when using `DynamicModelChoiceField` with `django.contrib.auth.models.Group`. NetBox's `DynamicModelChoiceField` requires models registered in NetBox's API router. Django's `auth.Group` is not registered. Use `forms.ModelChoiceField` instead.

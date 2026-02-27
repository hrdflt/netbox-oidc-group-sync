# TODO — NetBox OIDC Group Sync Plugin

## README Improvements

- [ ] Add `associate_by_email` to the recommended pipeline in README and installation example
- [ ] Document SAML-to-OIDC migration: populate email fields from usernames when migrating from SAML
  ```sql
  UPDATE users_user SET email = username WHERE email = '' AND username LIKE '%@%';
  ```
- [ ] Add troubleshooting section: "Username has random hash appended" — caused by empty `email` field on existing users preventing `associate_by_email` from matching

## Plugin Enhancements

- [ ] Add custom `associate_existing_user` pipeline step that matches by both `email` and `username` fields (handles SAML migration case without manual SQL)
- [ ] Write actual unit tests (currently all test files are TODO stubs)
- [ ] Consider adding a config option for `PLUGINS_CONFIG` overrides (group_claim_name, auto_create_groups, sync_mode) in addition to the GUI

## Packaging

- [ ] Publish to PyPI
- [ ] Add CI pipeline (GitHub Actions) for linting and tests

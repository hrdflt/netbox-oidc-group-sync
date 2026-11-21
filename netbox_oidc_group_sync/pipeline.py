import logging

from users.models import Group

logger = logging.getLogger('netbox_oidc_group_sync.pipeline')


def _is_valid_group_name(value):
    """
    Return True if value is a non-empty string the database can store.

    PostgreSQL rejects NUL characters and text that is not valid UTF-8 (such
    as a lone surrogate), and either would abort the login.
    """
    if not isinstance(value, str) or not value or '\x00' in value:
        return False
    try:
        value.encode('utf-8')
    except UnicodeEncodeError:
        return False
    return True


def sync_oidc_groups(backend, user, response, *args, **kwargs):
    """
    Social-auth pipeline function to sync OIDC groups to Django groups.

    Add to SOCIAL_AUTH_PIPELINE in configuration.py:
        'netbox_oidc_group_sync.pipeline.sync_oidc_groups',
    """
    from netbox_oidc_group_sync.models import OIDCGroupMapping, OIDCGroupSyncConfig

    # --- Diagnostic logging: pipeline entry ---
    logger.debug(
        "sync_oidc_groups called — backend=%s, user=%s",
        type(backend).__name__, getattr(user, 'username', repr(user)),
    )
    logger.debug(
        "Pipeline kwargs keys: %s", list(kwargs.keys()),
    )

    # --- Diagnostic logging: response structure ---
    if isinstance(response, dict):
        logger.debug(
            "response is dict with %d keys: %s",
            len(response),
            list(response.keys()),
        )
        # Log types/lengths of values to help identify where groups might hide
        for key in sorted(response.keys()):
            val = response[key]
            if isinstance(val, (list, dict)):
                logger.debug(
                    "  response[%r] → %s (len=%d)",
                    key, type(val).__name__, len(val),
                )
            elif isinstance(val, str) and len(val) > 120:
                logger.debug(
                    "  response[%r] → str (len=%d, truncated)",
                    key, len(val),
                )
            else:
                logger.debug(
                    "  response[%r] → %s: %r",
                    key, type(val).__name__, val,
                )
    else:
        logger.warning(
            "response is NOT a dict — type=%s, repr=%r",
            type(response).__name__, response,
        )

    config = OIDCGroupSyncConfig.get_solo()
    claim_name = config.group_claim_name

    logger.debug(
        "Config: group_claim_name=%r, auto_create_groups=%s, sync_mode=%r",
        claim_name, config.auto_create_groups, config.sync_mode,
    )

    # Extract groups from the claims of this login only. Nothing is read from
    # social.extra_data: at this point in the pipeline it still holds the
    # previous login's values, so it could hand back groups the user has since
    # been removed from.
    raw_groups = response.get(claim_name) if isinstance(response, dict) else None

    # Some IdPs only put the claim in the ID token, which OIDC backends keep
    # separately from the userinfo response. Fall back to the ID token the
    # backend validated for this login.
    id_token = getattr(backend, 'id_token', None)
    if not isinstance(id_token, dict):
        id_token = None
    if raw_groups is None and id_token is not None:
        raw_groups = id_token.get(claim_name)
        if raw_groups is not None:
            logger.debug(
                "Claim %r not in response; using the ID token", claim_name,
            )

    # Handle string vs list (some providers return a single string)
    if isinstance(raw_groups, str):
        logger.debug(
            "oidc_groups was a string %r, converting to list", raw_groups,
        )
        raw_groups = [raw_groups]

    if isinstance(raw_groups, (list, tuple, set)):
        oidc_groups = [g for g in raw_groups if _is_valid_group_name(g)]
        if len(oidc_groups) != len(raw_groups):
            logger.warning(
                "Ignoring empty, non-string or invalid entries in claim %r for user %s",
                claim_name, user.username,
            )
    else:
        if raw_groups is not None:
            logger.warning(
                "Claim %r for user %s has unsupported type %s; treating it as empty",
                claim_name, user.username, type(raw_groups).__name__,
            )
        oidc_groups = []

    if not oidc_groups:
        # A missing or empty claim means the user is in no groups. It is
        # deliberately not skipped: returning early here would let a user who
        # was removed from every group at the IdP keep their NetBox groups and
        # superuser status.
        logger.warning(
            "No OIDC groups found in claim '%s' for user %s; treating the user "
            "as a member of no groups. "
            "Available response keys: %s. ID token claims: %s. "
            "If this is unexpected, verify: (1) the IdP app has a '%s' claim configured, "
            "(2) the 'groups' scope is requested, "
            "(3) group_claim_name matches the IdP claim name.",
            claim_name, user.username,
            list(response.keys()) if isinstance(response, dict) else 'N/A',
            list(id_token.keys()) if id_token is not None else 'N/A',
            claim_name,
        )

    logger.info(f"User {user.username} has OIDC groups: {oidc_groups}")

    # Look up mappings
    mappings = OIDCGroupMapping.objects.filter(
        oidc_group_name__in=oidc_groups
    ).select_related('group')
    mapped_groups = set()

    for mapping in mappings:
        mapped_groups.add(mapping.group)
        logger.debug(
            f"Mapped OIDC group '{mapping.oidc_group_name}' "
            f"→ Django group '{mapping.group.name}'"
        )

    # Auto-create groups if enabled (for OIDC groups without explicit mappings).
    # Groups are matched by name, so an existing NetBox group with the same
    # name as an unmapped OIDC group is assigned as well.
    if config.auto_create_groups:
        mapped_oidc_names = set(m.oidc_group_name for m in mappings)
        unmapped_oidc_names = set(oidc_groups) - mapped_oidc_names
        name_max_length = Group._meta.get_field('name').max_length
        for oidc_name in sorted(unmapped_oidc_names):
            if len(oidc_name) > name_max_length:
                logger.warning(
                    "Not auto-creating group for OIDC group %r: name exceeds "
                    "%d characters. Create an explicit mapping instead.",
                    oidc_name, name_max_length,
                )
                continue
            group, created = Group.objects.get_or_create(name=oidc_name)
            if created:
                logger.info(
                    f"Auto-created Django group '{oidc_name}' for user {user.username}"
                )
            mapped_groups.add(group)

    # Sync groups based on mode
    if config.sync_mode == 'replace':
        user.groups.set(mapped_groups)
        logger.info(
            f"Replaced groups for {user.username}: {[g.name for g in mapped_groups]}"
        )
    elif config.sync_mode == 'additive':
        for group in mapped_groups:
            user.groups.add(group)
        logger.info(
            f"Added groups for {user.username}: {[g.name for g in mapped_groups]}"
        )

    # Handle superuser flag
    # NOTE: NetBox 4.x removed is_staff from the User model entirely
    # (migration 0013_user_remove_is_staff). Only is_superuser is supported.
    superuser_groups = config.get_superuser_groups_list()

    if superuser_groups:
        should_be_superuser = bool(set(oidc_groups) & set(superuser_groups))
        if user.is_superuser != should_be_superuser:
            user.is_superuser = should_be_superuser
            user.save()
            logger.info(f"Set is_superuser={should_be_superuser} for {user.username}")

import logging

from users.models import Group

logger = logging.getLogger('netbox_oidc_group_sync.pipeline')


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
    logger.debug(
        "Pipeline 'social' in kwargs: %s (type=%s)",
        'social' in kwargs,
        type(kwargs.get('social')).__name__ if 'social' in kwargs else 'N/A',
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

    # Extract groups from OIDC token claims
    # Try response directly, then try extra_data, then try kwargs.get('social')
    oidc_groups = response.get(claim_name, [])
    if oidc_groups:
        logger.debug(
            "Found groups in response[%r]: %r",
            claim_name, oidc_groups,
        )
    else:
        logger.warning(
            "Claim %r NOT found in response (or empty). "
            "Available response keys: %s",
            claim_name, list(response.keys()) if isinstance(response, dict) else 'N/A',
        )

    if not oidc_groups and hasattr(user, 'social_auth'):
        logger.debug(
            "Falling back to social_auth extra_data lookup. "
            "user.social_auth.exists()=%s",
            user.social_auth.exists(),
        )
        # Some backends put claims in extra_data
        social = kwargs.get('social') or (
            user.social_auth.first() if user.social_auth.exists() else None
        )
        if social and social.extra_data:
            logger.debug(
                "social.extra_data keys: %s",
                list(social.extra_data.keys()) if isinstance(social.extra_data, dict) else type(social.extra_data).__name__,
            )
            oidc_groups = social.extra_data.get(claim_name, [])
            if oidc_groups:
                logger.debug(
                    "Found groups in social.extra_data[%r]: %r",
                    claim_name, oidc_groups,
                )
            else:
                logger.warning(
                    "Claim %r NOT found in social.extra_data either. "
                    "Available extra_data keys: %s",
                    claim_name,
                    list(social.extra_data.keys()) if isinstance(social.extra_data, dict) else 'N/A',
                )
        elif social:
            logger.warning(
                "social object exists but extra_data is empty/None: %r",
                social.extra_data,
            )
        else:
            logger.warning(
                "No social auth object available "
                "(kwargs['social']=%r, user.social_auth query returned None)",
                kwargs.get('social'),
            )
    elif not oidc_groups:
        logger.warning(
            "user %s has no social_auth attribute — cannot fall back to extra_data",
            getattr(user, 'username', repr(user)),
        )

    # Handle string vs list (some providers return a single string)
    if isinstance(oidc_groups, str):
        logger.debug(
            "oidc_groups was a string %r, converting to list", oidc_groups,
        )
        oidc_groups = [oidc_groups]

    if not oidc_groups:
        logger.warning(
            "No OIDC groups found in claim '%s' for user %s. "
            "All extraction attempts exhausted. "
            "Verify: (1) Okta app has a '%s' claim configured, "
            "(2) 'groups' scope is in SOCIAL_AUTH_OIDC_SCOPE, "
            "(3) group_claim_name matches the Okta claim name.",
            claim_name, user.username, claim_name,
        )
        return

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

    # Auto-create groups if enabled (for OIDC groups without explicit mappings)
    if config.auto_create_groups:
        mapped_oidc_names = set(m.oidc_group_name for m in mappings)
        unmapped_oidc_names = set(oidc_groups) - mapped_oidc_names
        for oidc_name in unmapped_oidc_names:
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

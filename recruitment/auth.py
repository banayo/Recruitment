from mozilla_django_oidc.auth import OIDCAuthenticationBackend


def _claim_str(claims, *keys, default=""):
    for key in keys:
        value = claims.get(key)
        if value is None:
            continue
        return str(value).strip()
    return default


def _claim_groups(claims):
    groups = claims.get("groups") or claims.get("roles") or []
    if isinstance(groups, str):
        return [groups]
    if not isinstance(groups, (list, tuple)):
        return []
    normalized = []
    for item in groups:
        if isinstance(item, dict):
            name = item.get("name") or item.get("id") or ""
            if name:
                normalized.append(str(name))
        elif item is not None:
            normalized.append(str(item))
    return normalized


class AuthentikOIDCBackend(OIDCAuthenticationBackend):
    """
    JIT provision User from Authentik claims.
    Roles stay in session only (oidc_groups) — never on the User model.
    OIDC tokens remain in the Django server-side session.
    """

    def filter_users_by_claims(self, claims):
        sub = _claim_str(claims, "sub")
        if not sub:
            return self.UserModel.objects.none()
        return self.UserModel.objects.filter(authentik_sub=sub)

    def create_user(self, claims):
        person_unid = _claim_str(claims, "person_unid")
        sub = _claim_str(claims, "sub")
        if not person_unid or not sub:
            return None

        username = person_unid
        user = self.UserModel.objects.create_user(
            username=username,
            email=_claim_str(claims, "email"),
            authentik_sub=sub,
            person_unid=person_unid,
        )
        user.set_unusable_password()
        self._apply_claims(user, claims)
        user.save()
        self._store_groups_in_session(claims)
        return user

    def update_user(self, user, claims):
        self._apply_claims(user, claims)
        user.save()
        self._store_groups_in_session(claims)
        return user

    def _apply_claims(self, user, claims):
        user.authentik_sub = _claim_str(claims, "sub") or user.authentik_sub
        user.person_unid = _claim_str(claims, "person_unid") or user.person_unid
        user.approve_code = _claim_str(claims, "approve_code")
        user.gender = _claim_str(claims, "gender")
        user.division = _claim_str(claims, "division")
        user.department = _claim_str(claims, "department")
        user.location = _claim_str(claims, "location")
        user.nickname = _claim_str(claims, "nickname")
        user.company_code = _claim_str(claims, "company_code")

        # OIDC given_name / family_name → AbstractUser first_name / last_name
        given_name = _claim_str(claims, "given_name")
        if given_name:
            user.first_name = given_name

        family_name = _claim_str(claims, "family_name")
        if family_name:
            user.last_name = family_name

        email = _claim_str(claims, "email")
        if email:
            user.email = email

    def _store_groups_in_session(self, claims):
        request = getattr(self, "request", None)
        if request is None:
            return
        request.session["oidc_groups"] = _claim_groups(claims)

from trade_remedies_client.client import Client


class TransientUser:
    """
    A TransientUser object mimics a Django auth User but does not
    persist anywhere. Insetad it is created on the fly by the
    APIUserMiddleware middleware using session data.
    """

    def __init__(self, **kwargs):
        self.id = None
        self.is_authenticated = True
        self.transient_user = True
        self.organisations = []
        self.representing = []
        self.init_fields(**kwargs)

    def init_fields(self, **kwargs):
        """
        Init all given kwargs to this model as attributes.
        Failure is acceptable.
        """
        for key, value in kwargs.items():
            try:
                setattr(self, key, value)
            except Exception:
                pass

    def has_group(self, groups):
        if not isinstance(groups, (list, tuple)):
            groups = [groups]
        return any([grp in self.groups for grp in groups])

    def has_perm(self, perms):
        if not isinstance(perms, list):
            perms = [perms]
        return any([prm in self.permissions for prm in perms])

    @property
    def organisation(self):
        if self.organisations:
            return self.organisations[0]
        return None

    @property
    def representing_ids(self):
        """
        Return a list of all represented organisation's ids
        """
        try:
            return self._representing
        except AttributeError:
            self._representing = list(set([org["id"] for org in self.representing]))
            return self._representing

    def is_representing(self, organisation_id, request=None):
        """
        Check if this user is representing a given organisation (by it's id)
        """
        if request:
            return Client(request.user.token).is_representing(organisation_id)
        return not organisation_id or (
            self.representing and organisation_id in self.representing_ids
        )

    def reload(self, request):
        """
        Reload the user from the API
        """
        user = Client(request.user.token).get_user(self.id, self.organisation["id"])
        request.session["user"] = user
        request.session.modified = True
        self.init_fields(**user)
        return user

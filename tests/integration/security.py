import causes, effects


def require_ssl(self, path):
    #-------------------------------------------------
    # If ssl is not on for GET, redirect to ssl page
    #-------------------------------------------------
    self.assertState(
        'GET',
        path,
        [
            causes.valid_domain,
            causes.owner_logged_in,
        ],
        [
            effects.redirected(path, status = 301, ssl = True)
        ]
    )
    #-------------------------------------------------
    # If ssl is not on for POST, 403 Forbidden
    #-------------------------------------------------
    self.assertState(
        'POST',
        path,
        [
            causes.valid_domain,
            causes.owner_logged_in,
        ],
        [
            effects.status(403)
        ]
    )
    
    
    
def check(self, path, *extra_causes):
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_logged_in,
            causes.valid_domain,
            causes.account_inactive,
        ] + list(extra_causes),
        [
            effects.redirected('/account/inactive/', ssl=True),
        ]
    )
    check_account_inactive_ok(self, path, *extra_causes)
    
    
def check_account_inactive_ok(self, path, *extra_causes):
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_not_logged_in,
            causes.valid_domain,
            causes.account_active,
        ] + list(extra_causes),
        [
            effects.redirected('/person/login/', ssl=True),
        ]
    )
    self.assertState(
        'GET/POST',
        path,
        [
            causes.owner_logged_in,
            causes.mismatched_domain,
        ] + list(extra_causes),
        [
            effects.redirected('/person/login/', ssl=True),
        ]
    )
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_not_logged_in,
            causes.invalid_domain,
        ] + list(extra_causes),
        [
            effects.status(404),
        ]
    )
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_logged_in,
            causes.invalid_domain,
        ] + list(extra_causes),
        [
            effects.status(404),
        ]
    )
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_not_logged_in,
            causes.invalid_domain,
        ] + list(extra_causes),
        [
            effects.status(404),
        ]
    )
    self.assertState(
        'GET/POST',
        path,
        [
            causes.person_logged_in,
            causes.valid_domain,
            causes.account_active,
        ] + list(extra_causes),
        [
            effects.status(403),
        ]
    )
    
    

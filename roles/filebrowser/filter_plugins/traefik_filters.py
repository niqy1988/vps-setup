"""Custom Ansible filters for generating Traefik routing expressions.

This module is loaded automatically by Ansible when the role is executed.
Each public function exposed through ``FilterModule.filters`` can then be used
inside Jinja2 templates as a normal Ansible filter.
"""


def service_rule(domain_list, service):
    """Build a Traefik Host rule for one service across multiple domains.

    Args:
        domain_list: Iterable of root domains, for example
            ``["example.net", "example.org"]``.
        service: Service/subdomain name to prepend to every root domain,
            for example ``"app"``.

    Returns:
        A Traefik rule expression joined with logical OR operators, for example:
        ``Host(`app.example.net`) || Host(`app.example.org`)``.
    """
    # Traefik accepts multiple Host matchers joined with ``||`` in one router
    # rule, so each generated hostname can point to the same backend service.
    return " || ".join([
        # Compose the FQDN that Traefik should match for this service.
        f"Host(`{service}.{domain}`)"
        for domain in domain_list
    ])


class FilterModule(object):
    """Expose this module's helper functions as Ansible filter plugins."""

    def filters(self):
        """Return the mapping from Jinja2 filter names to Python callables."""
        return {
            # This makes ``{{ domains | service_rule('app') }}`` available in
            # Ansible templates, with ``domains`` passed as ``domain_list`` and
            # the explicit argument passed as ``service``.
            'service_rule': service_rule
        }

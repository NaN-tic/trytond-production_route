# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
try:
    from trytond.modules.production_route.tests.test_production_route import suite
except ImportError:
    from .test_production_route import suite

__all__ = ['suite']

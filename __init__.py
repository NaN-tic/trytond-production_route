# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from trytond.pool import Pool
from . import route
from . import product


def register():
    Pool.register(
        route.WorkCenterCategory,
        route.WorkCenter,
        route.OperationType,
        route.Route,
        route.RouteOperation,
        product.ProductBom,
        module='production_route', type_='model')

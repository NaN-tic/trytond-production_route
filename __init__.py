#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .route import *
from .product import *

def register():
    Pool.register(
        WorkCenterCategory,
        WorkCenter,
        OperationType,
        Route,
        RouteOperation,
        ProductBom,
        module='production_route', type_='model')

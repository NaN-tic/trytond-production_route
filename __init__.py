#The COPYRIGHT file at the top level of this repository contains the full
#copyright notices and license terms.

from trytond.pool import Pool
from .route import *


def register():
    Pool.register(
        WorkCenterCategory,
        WorkCenter,
        OperationType,
        Route,
        RouteOperation,
        module='production_route', type_='model')

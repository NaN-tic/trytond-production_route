from trytond.model import ModelView, ModelSQL, fields
# from trytond.pyson import Eval, Get, If, Bool
from trytond.pool import PoolMeta

__all__ = ['ProductBom']
__metaclass__ = PoolMeta


class ProductBom(ModelSQL, ModelView):
    __name__ = 'product.product-production.bom'

    # TODO: Add domain filter
    route = fields.Many2One('production.route', 'Route', ondelete='SET NULL')
    #    domain=[
    #        ('uom', '=', Get(Eval('_parent_product', {}), 'default_uom', 0)),
    #        ], depends=['product']

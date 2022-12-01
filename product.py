from trytond.model import fields
from trytond.pool import PoolMeta


class ProductBom(metaclass=PoolMeta):
    __name__ = 'product.product-production.bom'

    # TODO: Add domain filter
    route = fields.Many2One('production.route', 'Route', ondelete='SET NULL')
    #    domain=[
    #        ('uom', '=', Get(Eval('_parent_product', {}), 'default_uom', 0)),
    #        ], depends=['product']

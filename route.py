from decimal import Decimal
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta
from trytond.pyson import Eval, If, Bool

__all__ = ['WorkCenterCategory', 'WorkCenter', 'OperationType', 'Route',
    'RouteOperation', 'BOM']
__metaclass__ = PoolMeta


class WorkCenterCategory(ModelSQL, ModelView):
    'Work Center Category'
    __name__ = 'production.work_center.category'

    name = fields.Char('Name', required=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), required=True)
    uom = fields.Many2One('product.uom', 'Uom', required=True)
    uom_category = fields.Function(fields.Many2One(
            'product.uom.category', 'Uom Category',
            on_change_with=['uom']), 'on_change_with_uom_category')
    active = fields.Boolean('Active', select=True)

    def on_change_with_uom_category(self, name=None):
        if self.uom:
            return self.uom.category.id

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_cost_price():
        return Decimal('0.0')


class WorkCenter(ModelSQL, ModelView):
    'Work Center'
    __name__ = 'production.work_center'

    name = fields.Char('Name', required=True)
    category = fields.Many2One('production.work_center.category', 'Category',
        on_change=['category', 'cost_price', 'uom'], required=True)
    type = fields.Selection([
            ('machine', 'Machine'),
            ('employee', 'Employee'),
            ], 'Type')
    employee = fields.Many2One('company.employee', 'Employee', states={
            'invisible': Eval('type') != 'employee',
            'required': Eval('type') == 'employee',
            }, depends=['type'], on_change=['employee'])
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), required=True)
    uom_category = fields.Function(fields.Many2One(
            'product.uom.category', 'Uom Category',
            on_change_with=['category']), 'on_change_with_uom_category')
    uom = fields.Many2One('product.uom', 'Uom', required=True, domain=[
            If(Bool(Eval('uom_category', 0)),
                ('category', '=', Eval('uom_category')),
                (),
                )], depends=['uom_category'])
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_type():
        return 'machine'

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_cost_price():
        return Decimal('0.0')

    def on_change_category(self):
        res = {'uom': None, 'cost_price': None}
        if not self.category:
            return res
        if not self.uom or self.uom.category != self.category.uom_category:
            res['uom'] = self.category.uom.id
            res['uom.rec_name'] = self.category.uom.rec_name
        if not self.cost_price or self.cost_price == Decimal('0.0'):
            res['cost_price'] = self.category.cost_price
        return res

    def on_change_with_uom_category(self, name=None):
        if self.category:
            return self.category.uom_category.id


class OperationType(ModelSQL, ModelView):
    'Operation Type'
    __name__ = 'production.operation.type'

    name = fields.Char('Name', required=True)


class Route(ModelSQL, ModelView):
    'Production Route'
    __name__ = 'production.route'

    name = fields.Char('Name', required=True)
    operations = fields.One2Many('production.route.operation', 'route',
        'Operations')
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_active():
        return True


class RouteOperation(ModelSQL, ModelView):
    'Route Operation'
    __name__ = 'production.route.operation'

    route = fields.Many2One('production.route', 'Route', required=True)
    sequence = fields.Integer('Sequence')
    operation_type = fields.Many2One('production.operation.type',
        'Operation Type', required=True)
    work_center_category = fields.Many2One('production.work_center.category',
        'Work Center Category', required=True)
    work_center = fields.Many2One('production.work_center', 'Work Center',
        domain=[
            ('category', '=', Eval('work_center_category'),
            )], depends=['work_center_category'])
    uom_category = fields.Function(fields.Many2One(
            'product.uom.category', 'Uom Category',
            on_change_with=['work_center_category', 'work_center']),
        'on_change_with_uom_category')
    uom = fields.Many2One('product.uom', 'Uom', required=True,
        on_change_with=['work_center_category', 'work_center'], domain=[
                ('category', '=', Eval('uom_category', 0)),
                ], depends=['uom_category'])
    unit_digits = fields.Function(fields.Integer('Unit Digits',
            on_change_with=['uom']), 'on_change_with_unit_digits')
    quantity = fields.Float('Quantity', required=True,
        digits=(16, Eval('unit_digits', 2)), depends=['unit_digits'])

    @classmethod
    def __setup__(cls):
        super(RouteOperation, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    def on_change_with_uom(self, name=None):
        if self.work_center_category:
            return self.work_center_category.uom.id
        if self.work_center:
            return self.work_center.uom.id

    def on_change_with_unit_digits(self, name=None):
        if self.uom:
            return self.uom.digits
        return 2

    def on_change_with_uom_category(self, name=None):
        if self.work_center_category:
            return self.work_center_category.uom.category.id
        if self.work_center:
            return self.work_center.uom.category.id


class BOM:
    __name__ = 'production.bom'

    route = fields.Many2One('production.route', 'Route')

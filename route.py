from decimal import Decimal
from trytond.model import fields, ModelSQL, ModelView
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Eval, If, Bool, Id

__all__ = ['WorkCenterCategory', 'WorkCenter', 'OperationType', 'Route',
    'RouteOperation']
__metaclass__ = PoolMeta


class WorkCenterCategory(ModelSQL, ModelView):
    'Work Center Category'
    __name__ = 'production.work_center.category'

    name = fields.Char('Name', required=True)
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), required=True)
    uom = fields.Many2One('product.uom', 'Uom', required=True, domain=[
            ('category', '=', Id('product', 'uom_cat_time')),
            ])
    active = fields.Boolean('Active', select=True)

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_cost_price():
        return Decimal('0.0')

    @staticmethod
    def default_uom():
        ModelData = Pool().get('ir.model.data')
        return ModelData.get_id('product', 'uom_hour')


class WorkCenter(ModelSQL, ModelView):
    'Work Center'
    __name__ = 'production.work_center'

    name = fields.Char('Name', required=True)
    category = fields.Many2One('production.work_center.category', 'Category',
        on_change=['category', 'cost_price', 'uom'], required=True)
    type = fields.Selection([
            ('machine', 'Machine'),
            ('employee', 'Employee'),
            ], 'Type', required=True)
    employee = fields.Many2One('company.employee', 'Employee', states={
            'invisible': Eval('type') != 'employee',
            'required': Eval('type') == 'employee',
            }, depends=['type'], on_change=['employee'])
    cost_price = fields.Numeric('Cost Price', digits=(16, 4), required=True)
    uom = fields.Many2One('product.uom', 'Uom', required=True, domain=[
            ('category', '=', Id('product', 'uom_cat_time')),
            ])
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
        res = {
            'uom': None,
            'cost_price': None,
            }
        if not self.category:
            return res
        if not self.uom:
            res['uom'] = self.category.uom.id
            res['uom.rec_name'] = self.category.uom.rec_name
        if not self.cost_price or self.cost_price == Decimal('0.0'):
            res['cost_price'] = self.category.cost_price
        return res

    def on_change_employee(self):
        ModelData = Pool().get('ir.model.data')
        # Check employee is not empty and timesheet_cost module is installed
        if not self.employee or not hasattr(self.employee, 'cost_price'):
            return {}
        return {
            'cost_price': self.employee.cost_price,
            'uom': ModelData.get_id('product', 'uom_hour'),
            }


class OperationType(ModelSQL, ModelView):
    'Operation Type'
    __name__ = 'production.operation.type'
    name = fields.Char('Name', required=True)


class Route(ModelSQL, ModelView):
    'Production Route'
    __name__ = 'production.route'

    name = fields.Char('Name', required=True)
    active = fields.Boolean('Active', select=True)
    operations = fields.One2Many('production.route.operation', 'route',
        'Operations')
    uom = fields.Many2One('product.uom', 'UOM', required=True)

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
    time = fields.Float('Time', required=True,
        digits=(16, Eval('time_uom_digits', 2)), depends=['time_uom_digits'])
    time_uom = fields.Many2One('product.uom', 'Time UOM', required=True,
        domain=[
            ('category', '=', Id('product', 'uom_cat_time')),
            ], on_change_with=['work_center_category', 'work_center'])
    time_uom_digits = fields.Function(fields.Integer('Time UOM Digits',
            on_change_with=['time_uom']), 'on_change_with_time_uom_digits')
    quantity = fields.Float('Quantity', states={
            'required': Eval('calculation') == 'standard',
            'invisible': Eval('calculation') != 'standard',
            },
        digits=(16, Eval('quantity_uom_digits', 2)),
        depends=['quantity_uom_digits', 'calculation'],
        help='Quantity of the production product processed by the specified '
        'time.' )
    quantity_uom = fields.Many2One('product.uom', 'Quantity UOM', states={
            'required': Eval('calculation') == 'standard',
            'invisible': Eval('calculation') != 'standard',
            }, domain=[
            If(Bool(Eval('quantity_uom_category', 0)),
            ('category', '=', Eval('quantity_uom_category')),
            (),
            )], depends=['quantity_uom_category'])
    calculation = fields.Selection([
            ('standard', 'Standard'),
            ('fixed', 'Fixed'),
            ], 'Calculation', required=True, help='Use Standard to multiply '
        'the amount of time by the number of units produced. Use Fixed to use '
        'the indicated time in the production without considering the '
        'quantities produced. The latter is useful for a setup or cleaning '
        'operation, for example.')
    quantity_uom_digits = fields.Function(fields.Integer('Quantity UOM Digits',
            on_change_with=['quantity_uom']),
        'on_change_with_quantity_uom_digits')
    quantity_uom_category = fields.Function(fields.Many2One(
            'product.uom.category', 'Quantity UOM Category'),
        'get_quantity_uom_category')

    @staticmethod
    def default_calculation():
        return 'standard'

    @classmethod
    def __setup__(cls):
        super(RouteOperation, cls).__setup__()
        cls._order.insert(0, ('sequence', 'ASC'))

    @staticmethod
    def order_sequence(tables):
        table, _ = tables[None]
        return [table.sequence == None, table.sequence]

    def get_quantity_uom_category(self, name):
        if self.route and self.route.uom:
            return self.route.uom.category.id

    def on_change_with_time_uom(self, name=None):
        if self.work_center_category:
            return self.work_center_category.uom.id
        if self.work_center:
            return self.work_center.uom.id

    def on_change_with_time_uom_digits(self, name=None):
        if self.time_uom:
            return self.time_uom.digits
        return 2

    def on_change_with_quantity_uom_digits(self, name=None):
        if self.quantity_uom:
            return self.quantity_uom.digits
        return 2

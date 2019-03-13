from decimal import Decimal
from trytond.model import fields, ModelSQL, ModelView, sequence_ordered
from trytond.pool import Pool
from trytond.pyson import Eval, If, Bool, Id
from trytond.transaction import Transaction
from trytond.modules.product import price_digits

__all__ = ['WorkCenterCategory', 'WorkCenter', 'OperationType', 'Route',
    'RouteOperation']


class WorkCenterCategory(ModelSQL, ModelView):
    'Work Center Category'
    __name__ = 'production.work_center.category'

    name = fields.Char('Name', required=True)
    cost_price = fields.Numeric('Cost Price', digits=price_digits,
        required=True)
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
        required=True)
    type = fields.Selection([
            ('machine', 'Machine'),
            ('employee', 'Employee'),
            ], 'Type', required=True)
    employee = fields.Many2One('company.employee', 'Employee',
        states={
            'invisible': Eval('type') != 'employee',
            'required': Eval('type') == 'employee',
            }, depends=['type'])
    cost_price = fields.Numeric('Cost Price', digits=price_digits,
        required=True)
    uom = fields.Many2One('product.uom', 'Uom', required=True,
        domain=[
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

    @fields.depends('category', 'cost_price', 'uom')
    def on_change_category(self):
        self.uom = None
        self.cost_price = None

        if self.category:
            if not self.uom:
                self.uom = self.category.uom.id
                self.uom.rec_name = self.category.uom.rec_name
            if not self.cost_price or self.cost_price == Decimal('0.0'):
                self.cost_price = self.category.cost_price

    @fields.depends('employee')
    def on_change_employee(self):
        ModelData = Pool().get('ir.model.data')
        # Check employee is not empty and timesheet_cost module is installed
        if self.employee and hasattr(self.employee, 'cost_price'):
            self.cost_price = self.employee.cost_price
            self.uom = ModelData.get_id('product', 'uom_hour')


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
        'Operations', context={
            'route_uom': Eval('uom', 0),
            })
    uom = fields.Many2One('product.uom', 'UOM', required=True)

    @staticmethod
    def default_active():
        return True


class RouteOperation(sequence_ordered(), ModelSQL, ModelView):
    'Route Operation'
    __name__ = 'production.route.operation'

    route = fields.Many2One('production.route', 'Route', required=True,
        ondelete='CASCADE')
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
            ])
    time_uom_digits = fields.Function(fields.Integer('Time UOM Digits'),
        'on_change_with_time_uom_digits')
    quantity = fields.Float('Quantity',
        states={
            'required': Eval('calculation') == 'standard',
            'invisible': Eval('calculation') != 'standard',
            },
        digits=(16, Eval('quantity_uom_digits', 2)),
        depends=['quantity_uom_digits', 'calculation'],
        help='Quantity of the production product processed by the specified '
        'time.')
    quantity_uom = fields.Many2One('product.uom', 'Quantity UOM',
        states={
            'required': Eval('calculation') == 'standard',
            'invisible': Eval('calculation') != 'standard',
            },
        domain=[
            If(Bool(Eval('quantity_uom_category', 0)),
                ('category', '=', Eval('quantity_uom_category')),
                ()),
            ],
        depends=['quantity_uom_category'])
    calculation = fields.Selection([
            ('standard', 'Standard'),
            ('fixed', 'Fixed'),
            ], 'Calculation', required=True, help='Use Standard to multiply '
        'the amount of time by the number of units produced. Use Fixed to use '
        'the indicated time in the production without considering the '
        'quantities produced. The latter is useful for a setup or cleaning '
        'operation, for example.')
    quantity_uom_digits = fields.Function(fields.Integer(
            'Quantity UOM Digits'),
        'on_change_with_quantity_uom_digits')
    quantity_uom_category = fields.Function(fields.Many2One(
            'product.uom.category', 'Quantity UOM Category'),
        'on_change_with_quantity_uom_category')
    notes = fields.Text('Notes')

    @staticmethod
    def default_calculation():
        return 'standard'

    @staticmethod
    def default_quantity_uom_category():
        pool = Pool()
        Uom = pool.get('product.uom')
        context = Transaction().context
        if 'route_uom' in context:
            route_uom = Uom(context['route_uom'])
            return route_uom.category.id

    def compute_time(self, quantity, uom):
        Uom = Pool().get('product.uom')
        if self.calculation == 'standard':
            quantity = Uom.compute_qty(uom, quantity, to_uom=self.quantity_uom,
                round=False)
            factor = quantity / self.quantity
            return self.time_uom.round(self.time * factor)
        return self.time

    @fields.depends('route')
    def on_change_with_quantity_uom_category(self, name=None):
        if self.route and self.route.uom:
            return self.route.uom.category.id
        return None

    @fields.depends('work_center_category', 'work_center')
    def on_change_with_time_uom(self, name=None):
        if self.work_center_category:
            return self.work_center_category.uom.id
        if self.work_center:
            return self.work_center.uom.id

    @fields.depends('time_uom')
    def on_change_with_time_uom_digits(self, name=None):
        if self.time_uom:
            return self.time_uom.digits
        return 2

    @fields.depends('quantity_uom')
    def on_change_with_quantity_uom_digits(self, name=None):
        if self.quantity_uom:
            return self.quantity_uom.digits
        return 2

from openerp import api, fields, models
import datetime
import time
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from openerp.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
#         _logger.info("PAYROLL ID=%i",record.payroll_id.name.id)
# _logger.info should be inside function
class hr_contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Extends hr.contract to add new fields'
    bagged_mult = fields.Float('Bagged Multiplier', digits=(5, 2), required=True, default=2,
                               help="Multiplier for Bagger Commission. Varies per Bagger")
    bagsold_mult = fields.Float('Bags Sold Multiplier', digits=(5, 2), required=True, default=1,
                               help="Multiplier for Bag Seller Commission. Varies per seller")
    cratesold_mult = fields.Float('Crates Sold Multiplier', digits=(5, 2), required=True, default=5,
                               help="Multiplier for Crates Seller Commission. Varies per seller")
    dispsold_mult = fields.Float('Dispenser Sold Multiplier', digits=(5, 2), required=True, default=25,
                               help="Multiplier for Dispenser Seller Commission. Varies per seller")
    sal_adv = fields.Float('Salary Advance Ded', digits=(7, 2), required=True, 
                               help="Salary Advance. Varies per individual")
    loan_adv = fields.Float('Loan Advance Ded', digits=(7, 2), required=True, 
                               help="Loan Advance. Varies per individual")
    payee = fields.Float('PAYEE TAX Ded', digits=(7, 2), required=True, 
                               help="PAYEE TAX. Varies per individual")
    days_absent = fields.Float('Days Absent', digits=(4,2), required=True,
                               help="Days absent from Work in Month. Affects Base Salary")

    
class fido_payroll(models.Model):
    _name = "fido.payroll"
    _inherit = 'mail.thread'
    _description = 'Fido Payroll Architecture'
    name = fields.Many2one('hr.employee', string='Payroll Staff', domain="[('company_id','=','FIDO PRODUCING LTD')]", required=True)
    phone = fields.Char(related='name.mobile_phone',store=True)
    start_date = fields.Date('Date Begin',default=(date.today() + relativedelta(day=1)))
    end_date = fields.Date('Date End',default=date.today())
        
    work_days_tot = fields.Integer(compute='get_workdays', string='Total Work Days',store=True)
    note = fields.Text(string='Miscellaneous Notes')
    payroll_ref = fields.Char(compute='get_workdays',readonly=True,string='Payroll ID',store=True)
    payroll_line_ids = fields.One2many('fido.payroll.line', 'payroll_id')
    f_mnth = fields.Char('Month',required=True, readonly=True, store=True, default=date.today().strftime('%B'))
    pay_year = fields.Char('Year',required=True, readonly=True, store=True, default=date.today().strftime('%Y'))
    payroll_total = fields.Float(compute='create_lines',digits=(9, 2), string='Total', store=True)
    absent_days = fields.Float(compute='get_absentdays',digits=(4,2),string='Absent Days',store=True)
    
    job_title = fields.Char(related='name.job_id.name',store=True)
    
    bank_account = fields.Char(related='name.bank_account_id.acc_number',store=True)
    item_id = fields.Char(compute='create_lines',string='Item Name',store=True)
    item_qty = fields.Float(compute='create_lines',string='Qty',store=True)
    item_mult = fields.Float(compute='create_lines',string='Multiplier',store=True)
    line_total = fields.Float(compute='create_lines',string='Amount',store=True)
    product_cat = fields.Char( string='Product Category')

    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_valids(self):
        if self.start_date > self.end_date:
            raise ValidationError("Field start_date must be before end_date")
        clause = [('payroll_ref', '=', self.payroll_ref)]
        if self.search(clause):
            raise ValidationError("Payroll Already Created for this staff, Delete First")
    
    @api.one
    @api.depends('name')
    def get_absentdays(self):
        clause_contract =  [('employee_id', '=', self.name.id)]
        contract_ids = self.env['hr.contract'].search(clause_contract)
        for contract in contract_ids:
            self.absent_days = contract.days_absent
    
    @api.one
    @api.depends('payroll_line_ids.line_total')
    def compute_payroll_total(self):
        self.payroll_total = sum(line.line_total for line in self.payroll_line_ids)
    
    top_name = fields.Char(compute='get_top_name', store=True)
    @api.one
    @api.depends('f_mnth','name')
    def get_top_name(self):
        if (self.f_mnth and self.name):            
            self.top_name = self.f_mnth.upper() + ' Record' + ' for ' + self.name.name
        else:
            self.top_name = date.today().strftime('%B') + ' Payslip '
       
    @api.one
    @api.depends('name','start_date','end_date')
    def get_workdays(self):
        
        fmt = '%Y-%m-%d'
        workdays = datetime.datetime.strptime(self.end_date, fmt) - datetime.datetime.strptime(self.start_date, fmt)          
        sundays = workdays.days / 7 
        self.work_days_tot = workdays.days - sundays
        self.payroll_ref =  'Payslip/' + str(self.name.name) + '/' + str(self.f_mnth)

    @api.one
    @api.depends('name','start_date','end_date')
    def get_invoice_totals(self):
        
        account_invoice_obj = self.env['account.invoice.report']
        clause = [('date','>=',self.start_date),('date','<=',self.end_date),
                    ('categ_id.name','=',self.product_cat),('user_id.name','=', self.name.user_id.name)]
        gotten_fields = account_invoice_obj.search(clause)
        total=0.0
        for account_invoice in gotten_fields:
            total += account_invoice.product_qty
        self.item_qty = total
    
    @api.one
    @api.depends('name')
    def get_bagger_totals(self):
        bagger_obj = self.env['fido.bagger']
        month_f_end_date = datetime.datetime.strftime(date.today(), '%B').lower()
        clause =  [('name.name', '=', self.name.name),('x_month', '=', self.f_mnth)]
        _logger.info("*** LOGGING Processing  bagger Derived month %s",month_f_end_date)
        bagger_ids = bagger_obj.search(clause)
        total = 0.0
        self.item_qty = 0.0
        for bagger in bagger_ids:
            self.item_qty = bagger.qty_total
            _logger.info("*** LOGGING Processing  bagger totl  %s bagger Month: %s Derived month %s",bagger.qty_total,bagger.x_month,month_f_end_date)           
    #                 Get from the employee Contract.        
        
    @api.one
    @api.depends('name','start_date','end_date')
    def create_lines(self):
        item_obj = self.env['fido.payroll.item']
        itemid = item_obj.search([])    
        for item in itemid:
            _logger.info("*** LOGGING Processing CREATE_LINES ITEM.Name %s ",item.name)
           # self.item_id = item.name
            self.set_items(item.name)
            self.line_total = self.item_qty * self.item_mult
            self.payroll_total += self.line_total       
            _logger.info("*** LOGGING Processing CREATE_LINES ITEM ID %s ",self.item_id)
            self.env['fido.payroll.line'].create({'payroll_id':self.id,'item_id':self.item_id,'item_qty':self.item_qty,'item_mult':self.item_mult,'line_total':self.line_total})
            self.line_total = 0.0
          
    
    @api.multi
    @api.depends('name','start_date','end_date')
    def set_items(self,item_id):        
        
        contract_obj = self.env['hr.contract']
        clause_contract =  [('employee_id', '=', self.name.id)]
        contract_ids = contract_obj.search(clause_contract)
                
        begin_date = self.start_date
        end_date = self.end_date
        
#         This assumes Payroll are prepared latest end of month
        month_f_end_date = datetime.datetime.strftime(date.today(), '%B').lower()
        total_work_days = self.work_days_tot
         
        
        self.item_qty = 0
        self.item_mult = 0
        self.line_total = 0
        self.item_id = item_id
        # self.item_id = item_id
        if self.item_id == 'Bags Sales Commission':            
            self.product_cat = 'PUREWATER'
            self.get_invoice_totals()
    #                 Get from the employee Contract.
            for contract in contract_ids:
                self.item_mult = contract.bagsold_mult
          
        elif self.item_id == 'Dispenser Sales Commission':
            self.product_cat = 'DISPENSER'
            self.get_invoice_totals()
    #                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.dispsold_mult
          
        elif self.item_id == 'Crates Sales Commission':
            self.product_cat = 'BOTTLE CRATES'
            self.get_invoice_totals()
                    
            for contract in contract_ids:
                self.item_mult = contract.cratesold_mult
          
        elif self.item_id == 'Bagging Commission':  
            self.get_bagger_totals()                                
            for contract in contract_ids:                
                self.item_mult = contract.bagged_mult
          
                
        elif self.item_id == 'Salary Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.item_qty = -1
    #                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.sal_adv
        elif self.item_id == 'Base Salary':
            _logger.info("*** LOGGING Processing %s of %s for month %s  ",self.item_id,self.name.name,self.f_mnth)
            self.item_mult = 1
                    
            for contract in contract_ids:
                self.item_qty = contract.wage
                
        elif self.item_id == 'Loan Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.item_qty = -1
    #                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.loan_adv
                
        elif self.item_id == 'PAYEE TAX Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.item_qty = -1
    #                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.payee
                
        elif self.item_id == 'Absentee Deductions':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.item_qty = -1
    #                 Get from the employee Contract.                
            for contract in contract_ids:        
                _logger.info("*** LOGGING Processing  Mulitplier is = %s ",self.item_mult)
                    #if self.payroll_id.work_days_tot != 0:
                try:       
                    self.item_mult = (contract.days_absent / float(total_work_days)) * contract.wage
                except ZeroDivisionError:
                    _logger.exception("division by zero error work days total")
                        
class fido_payroll_item(models.Model):
    _name = "fido.payroll.item"
    _description = "Fido Payroll Items"
    name = fields.Char("Fido Payroll Commission Item")


class fido_payroll_line(models.Model):
    _name = "fido.payroll.line"
    _description = "Fido Payroll lines"
    payroll_id = fields.Many2one('fido.payroll', string='Fido Reference')
#  Fields for Bags, disp and crates sold totals
    
# base_salary pick from staff record
#  Each line is for a payroll commission item
# Items vary and can be bags, dispensers, crates
# See Model payroll items
#     item_id = fields.Many2one('fido.payroll.item','Commission Item')
    item_id = fields.Char('Commission Item')
    item_qty = fields.Float(string='Qty')
    item_mult = fields.Float(string='Multiplier')
    line_total = fields.Float(string='Amount')

            
class fido_payroll_employee_inherit(models.Model):
    _inherit ='hr.employee'
    _name = 'hr.employee'
    _description = "Fido Payroll Inherits from hr.employee to add payroll counts"
    pay_log = fields.Float(compute='pay_count', string='Fido Slip')
    
    @api.one
    def pay_count(self):
        for record in self:
            record_count = self.pool.get('fido.payroll')
            pay_logger = record_count.search(self._cr,self._uid, [('name','=',record.id)])
            record.pay_log = len(pay_logger)

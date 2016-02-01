from openerp import api, fields, models
import datetime
import time
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from openerp.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)
class fido_batch(models.Model):
    _name = "fido.batch"
    _description = 'Fido Batch Payroll Architecture'
    start_date = fields.Date('Date Begin',default=(date.today() + relativedelta(day=1)))
    end_date = fields.Date('Date End',default=date.today())
    payroll_line_ids = fields.One2many('fido.payroll.line', 'payroll_id')
    emp_name = fields.Char('Employee')
    pay_item = fields.Char('Pay Item')
    line_total = fields.Float(string='Line Total',digits=(9,2))
    payroll_total = fields.Float(string='Payslip Total',digits=(9,2))
#     payroll_total = fields.Float(compute='compute_payroll_total',digits=(9, 2), string='Total', store=True)

#     @api.one
#     @api.depends('payroll_line_ids.line_total')
#     def compute_payroll_total(self):
#         self.payroll_total = sum(line.line_total for line in self.payroll_line_ids)
#         
  # For each employee in hr.employee, do this
    @api.one 
    @api.depends('start_date','end_date')
    def create_payslips(self):
        employee_id = fields.Many2one('hr.employee','Employee ID')
        employee_obj = self.env['hr.employee'].search([('active', '=', True)])
        for employee in employee_obj:
            self.emp_name = employee.name
            for pay_item in self.env['fido.payroll.item'].search([(len('name'), '>', '0')]):
                self.pay_item = pay_item
                paylines = self.env['fido.payroll.line'].search([(('name'),'=',self.emp_name),
                    (('item_id.name'),'=',self.pay_item),(('start_date'),'=',self.start_date),
                    (('end_date'),'=',self.end_date)]) # knowing emp_name and pay_item, get payline
                _logger.info("LOGGING Pay Lines|%s|%s", paylines)
                
            self.payroll_total = sum(payline.line_total for payline in paylines)
            _logger.info("LOGGING Payroll Total %s for %s", self.emp_name,self.payroll_total)
            payslip = {
                'name' : self.emp_name,
                'start_date' : self.start_date,
                'end_date' : self.end_date,
                'f_mnth' : self.month,
                'payroll_line_ids' : paylines,
                'payroll_total' : self.payroll_total
            }      
            
            self.env['fido.payroll'].create(payslip)
            
                    
            
                
                
            
            

class fido_payroll_item(models.Model):
    _name = "fido.payroll.item"
    _description = "Fido Payroll Items"
    name = fields.Char("Fido Payroll Commission Item")

# Model the payroll lines per Employee
class fido_payroll_line(models.Model):
    _name = "fido.payroll.line"
    payroll_id = fields.Many2one('fido.batch', string='Fido Reference')
#  Fields for Bags, disp and crates sold totals
    
# base_salary pick from staff record
#  Each line is for a payroll commission item
# Items vary and can be bags, dispensers, crates
# See Model payroll items
    item_id = fields.Many2one('fido.payroll.item','Commission Item')
    item_qty = fields.Float(compute='get_values',string='Qty')
    item_mult = fields.Float(compute='get_values',string='Multiplier')
    line_total = fields.Float(compute='compute_line_total', string='Amount')
    
 #     This function returns the quantity and multiplier once a payroll item is selected       
    @api.one 
    @api.depends('item_id','payroll_id')
    def get_values(self):
        cursor = self._cr
        user = self._uid
        
        contract_obj = self.env['hr.contract']
        bagger_obj = self.env['fido.bagger']
        account_invoice_obj = self.env['account.invoice.report']
                
        product_1 = "PUREWATER"
        product_2 = "DISPENSER"
        product_3 = "BOTTLE CRATES"
        self.item_qty = 0
        self.item_mult = 0
        begin_date = self.payroll_id.start_date
        end_date = self.payroll_id.end_date
        
#         This assumes Payroll are prepared latest end of month
        month_f_end_date = datetime.datetime.strftime(date.today(), '%B').lower()
        total_work_days = self.payroll_id.work_days_tot
        
        clause_contract =  [('employee_id', '=', self.payroll_id.name.id)]
        contract_ids = contract_obj.search(clause_contract)
        
        
        if self.item_id.name == 'Bags Sales Commission':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id.name)
            gotten_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),
                                                            ('categ_id.name','=',product_1),('user_id.name','=', self.payroll_id.name.user_id.name)])
            total=0.0
            for account_invoice in gotten_fields:
                total += account_invoice.product_qty
                _logger.info("LOGGING INVOICE.Date,Categ_id.name, QTY...|%s|%s|%s", account_invoice.date,account_invoice.categ_id.name,account_invoice.product_qty)
                self.item_qty = total
#                 Get from the employee Contract.
            for contract in contract_ids:
                self.item_mult = contract.bagsold_mult
            return
        if self.item_id.name == 'Dispenser Sales Commission':
                
            disp_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),('categ_id.name','=',product_2),('user_id.name','=', self.payroll_id.name.user_id.name)])
            _logger.info("LOGGING Processing %s for ... %s", self.item_id.name, self.payroll_id.name.user_id.name)
            disp_total=0.0
            for account_invoice in disp_fields:
                disp_total += account_invoice.product_qty
                
            self.item_qty = disp_total
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.dispsold_mult
                
            return
        if self.item_id.name == 'Crates Sales Commission':
            _logger.info("*** LOGGING Processing  = %s  for %s",self.item_id.name,self.payroll_id.name.user_id.name)
            crate_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),('categ_id.name','=',product_3),('user_id.name','=', self.payroll_id.name.user_id.name)])
            crate_total=0.0
            for account_invoice in crate_fields:
                crate_total += account_invoice.product_qty
            self.item_qty = crate_total
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.cratesold_mult
            return
        if self.item_id.name == 'Bagging Commission':  
            _logger.info("*** LOGGING Processing  %s for %s for Month %s",self.item_id.name,self.payroll_id.name.name,self.payroll_id.f_mnth)  
            bclause_final =  [('name.name', '=', self.payroll_id.name.name),('x_month', '=', month_f_end_date)]
             
            bagger_ids = bagger_obj.search(bclause_final)
            for bagger in bagger_ids:
                _logger.info("*** LOGGING Processing  bagger ids len %s bagger Month: %s Derived month %s",len(bagger_ids),bagger.x_month,month_f_end_date)
                self.item_qty = bagger.qty_total               
#                 Get from the employee Contract.                    
            for contract in contract_ids:
                self.item_mult = contract.bagged_mult
            return
        if self.item_id.name == 'Base Salary':
            _logger.info("*** LOGGING Processing %s of %s for month %s  ",self.item_id.name,self.payroll_id.name.name,self.payroll_id.f_mnth)
            self.item_mult = 1
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_qty = contract.wage
            return
        if self.item_id.name == 'Salary Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  %s ",self.item_id.name)
            self.item_qty = -1
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.sal_adv
            return
        if self.item_id.name == 'Loan Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id.name)
            self.item_qty = -1
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.loan_adv
            return
        if self.item_id.name == 'PAYEE TAX Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id.name)
            self.item_qty = -1
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.payee
            return
        if self.item_id.name == 'Absentee Deductions':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id.name)
            self.item_qty = -1
#                 Get from the employee Contract.                
            for contract in contract_ids:        
                _logger.info("*** LOGGING Processing  Mulitplier is = %s ",self.item_mult)
                #if self.payroll_id.work_days_tot != 0:
                try:       
                    self.item_mult = (contract.days_absent / float(total_work_days)) * contract.wage
                except ZeroDivisionError:
                    _logger.exception("division by zero error work days total")
                
            return








from openerp import api, fields, models
import datetime
import time
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)

class fido_total(models.Model):
    _name = 'fido.total'
    
    _description = 'Key Monthly Totals for Fido PL Factories'
    
    employee_name = fields.Many2One('hr.employee', 'employee')
    disp_product = fields.Char('Dispenser')
    crate_product = fields.Char('Crates')
    pwater_product = fields.Char('Purewater')
    bag_product = fields.Char('Baggings')
    
    
    pwater_totals = fields.Float(compute='get_totals', string='Pure Water Totals', store=True)
    crate_totals = fields.Float(compute='get_totals', string='Pure Water Totals', store=True)
    disp_totals = fields.Float(compute='get_totals', string='Pure Water Totals', store=True)
    bag_totals = fields.Float(compute='get_totals', string='Pure Water Totals', store=True)
    start_date = fields.Date('Date Begin',default=(date.today() + relativedelta(day=1)))
    end_date = fields.Date('Date End',default=date.today())
    
# Totals for Reporting and QC
    @api.one
    @api.depends('start_date','end_date','product')
    def get_totals(self):
        contract_obj = self.env['hr.contract']
        employee_obj = self.env['hr.employee']
        bagger_obj = self.env['fido.bagger']
        account_invoice_obj = self.env['account.invoice.report']
        
        product_1 = "PUREWATER"
        product_3 = "BOTTLE CRATES"
        product_2 = "DISPENSER"
        self.disp_product = product_1
        self.crate_product = product_3
        self.pwater_product = product_2
        self.bag_product = "BAGGINGS"
        # month_f_end_date = datetime.datetime.strftime(date.today(), '%B').lower()
        
        begin_date = self.start_date
        end_date = self.end_date
        month_f_end_date = datetime.datetime.strftime(self.end_date, '%B').lower()
        
        for employee in employee_obj.search([('context','=',None)]):
            # do for bagger totals
            bclause_final =  [('name', '=', employee.name),('x_month', '=', month_f_end_date)]
            bagger_ids = bagger_obj.search(bclause_final)
            for bagger in bagger_ids:                
                self.bag_totals += bagger.qty_total
                _logger.info("*** LOGGING Processing  bagger totals %s ",self.bag_totals)
                
            # do for bags sold totals
            bagsold_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),
                        ('categ_id.name','=',product_1),('user_id.name','=', employee.name.user_id.name)]) 
            for account_invoice in bagsold_fields:
                self.pwater_totals += account_invoice.product_qty
                _logger.info("LOGGING INVOICE. Bagsold totals |%s|", self.bag_totals)
                
#           # Do for dispenser sold totals
            disp_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),('categ_id.name','=',product_2),('user_id.name','=', employee.name.user_id.name)])
            for account_invoice in disp_fields:
                self.disp_totals += account_invoice.product_qty
            
            # Do for crates sold totals
            crate_fields = account_invoice_obj.search([('date','>=',begin_date),('date','<=',end_date),('categ_id.name','=',product_3),('user_id.name','=', employee.name.user_id.name)])
            for account_invoice in crate_fields:
                self.crate_totals += account_invoice.product_qty
            
            
            
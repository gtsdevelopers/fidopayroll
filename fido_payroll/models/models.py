from openerp import api, fields, models
import datetime
import logging
_logger = logging.getLogger(__name__)
#         _logger.info("PAYROLL ID=%i",record.payroll_id.name.id)
# _logger.info should be inside function
class hr_contract(models.Model):
    _inherit = 'hr.contract'
    _description = 'Extends hr.contract to add these fields'
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

    
class fido_payroll(models.Model):
    _name = "fido.payroll"
    _description = 'Fido Payroll Architecture'
    name = fields.Many2one('hr.employee',string='Payroll Staff', size=32, required=True)
    start_date = fields.Date('Date Begin')
    end_date = fields.Date('Date End')   
    note = fields.Text(string='Miscellaneous Notes')
    payroll_line_ids = fields.One2many('fido.payroll.line', 'payroll_id')
    
    f_mnth = fields.Selection([('january','January'),('february','February'),
                              ('march','March'),('april','April'),('may','May'),
                             ('june','June'),('july','July'),('august','August'),
                             ('september','September'),('october','October'),
                             ('november','November'),('december','December')],
                             string='Month', required=True, default='january')
    payroll_total = fields.Float(compute='compute_payroll_total', string='Total', store=True)
    @api.one
    @api.depends('payroll_line_ids.line_total')
    def compute_payroll_total(self):
        self.payroll_total = sum(line.line_total for line in self.payroll_line_ids)
    
    top_name = fields.Char(compute='get_month', store=True)
    @api.one
    @api.depends('f_mnth')
    def get_month(self):
#        if self.f_month in self:
        for record in self:
            record.top_name = record.f_mnth.title() + ' Record'
    
    line_total = fields.Float(related='payroll_line_ids.line_total', string='Line Total',
                            store=True, readonly=True)
    
    job_title = fields.Char(compute='get_job_title', string="Job Title")
    @api.one
    @api.depends('name')
    def get_job_title(self):
        for record in self:
            record.job_title = record.name.job_id.name
    
    bank_account = fields.Char(compute='get_bank_account', string="Bank Account")
    
    @api.one
    @api.depends('name')
    def get_bank_account(self):
        for record in self:
            record.bank_account = record.name.bank_account_id.acc_number
    
                
class fido_payroll_item(models.Model):
    _name = "fido.payroll.item"
    _description = "Fido Payroll Items"
    name = fields.Char("Fido Payroll Commission Item")

class fido_payroll_line(models.Model):
    _name = "fido.payroll.line"
    payroll_id = fields.Many2one('fido.payroll', string='Fido Reference')
#  Fields for Bags, disp and crates sold totals
    
#    fido_date = fields.Date(default=fields.Date.today(), required=True)
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
#         account_invoice_obj = self.pool.get('account.invoice.report')
        account_invoice_obj = self.env['account.invoice.report']
                
        _logger.info("*** LOGGING Self Count|self  = %i|%s ",len(self),self)
        product_1 = "PUREWATER"
        product_2 = "DISPENSER"
        product_3 = "BOTTLE CRATES"
        self.item_qty = 0
        self.item_mult = 0
        begin_date = self.payroll_id.start_date
        end_date = self.payroll_id.end_date
        clause_contract =  [('employee_id', '=', self.payroll_id.name.id)]
        contract_ids = contract_obj.search(clause_contract)
            
        _logger.info("*** LOGGING Item_id.name = %s ",self.item_id.name)
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
            bclause_final =  [('name.name', '=', self.payroll_id.name.name),('x_month', '=', self.payroll_id.f_mnth)]
             
            bagger_ids = bagger_obj.search(bclause_final)
            for bagger in bagger_ids:
                self.item_qty = bagger.qty_total               
#                 Get from the employee Contract.                    
            for contract in contract_ids:
                self.item_mult = contract.bagged_mult
            return
        if self.item_id.name == 'Base Salary':
            _logger.info("*** LOGGING Processing %s of %s for month %s  ",self.item_id.name,self.payroll_id.name.name,self.payroll_id.f_mnth)
            self.item_qty = 1
#                 Get from the employee Contract.                
            for contract in contract_ids:
                self.item_mult = contract.wage
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
            
               
#     Every Pay Payroll line should have a total        
    @api.one
    @api.depends('item_id')
    def compute_line_total(self):
        self.line_total = self.item_qty * self.item_mult
            
class fido_payroll_employee_inherit(models.Model):
    _inherit ='hr.employee'
    _name = 'hr.employee'
    pay_log = fields.Float(compute='pay_count', string='Fido Slip')
    
    @api.one
    def pay_count(self):
        for record in self:
            record_count = self.pool.get('fido.payroll')
            pay_logger = record_count.search(self._cr,self._uid, [('name','=',record.id)])
            record.pay_log = len(pay_logger)
            
            

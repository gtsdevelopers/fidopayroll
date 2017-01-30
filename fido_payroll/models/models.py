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
    kpbg_sold = fields.Float('Kpansia Sold Qty', digits=(7,1), required=True, default=0,
                               help="Quantity Sold This Month")
    obbg_sold = fields.Float('Obunna Sold Qty', digits=(7,1), required=True, default=0,
                               help="Obunna Quantity Sold This Month")

    bagsold_mult = fields.Float('Bags Sold Multiplier', digits=(5, 2), required=True, default=1,
                               help="Multiplier for Bag Seller Commission. Varies per seller")
    obbgsold_mult = fields.Float('OB Bags Sold Multiplier', digits=(5, 2), required=True, default=1,
                               help="Multiplier for Bag Seller Commission. Varies per seller")
    kpbgsold_mult = fields.Float('KP Bags Sold Multiplier', digits=(5, 2), required=True, default=1,
                               help="Multiplier for KP Bag Seller Commission. Varies per seller")
    
    cratesold_mult = fields.Float('Crates Sold Multiplier', digits=(5, 2), required=True, default=5,
                               help="Multiplier for Crates Seller Commission. Varies per seller")
    crate_sold = fields.Float('Crate Sold Qty', digits=(7,1), required=True, default=0,
                               help="Crate Quantity Sold This Month")
    disp_sold = fields.Float('Disp Sold Qty', digits=(7,1), required=True, default=0,
                               help="Disp Quantity Sold This Month")
    
    
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
#     paybatch_id = fields.Many2one('fido.payroll.batch', string='Fido Batch Reference')
        
    work_days_tot = fields.Integer(compute='get_workdays', string='Total Work Days',store=True)
    note = fields.Text(string='Miscellaneous Notes')
    payroll_ref = fields.Char(compute='get_ref',readonly=True,string='Payroll ID',store=True)
    payroll_line_ids = fields.One2many('fido.payroll.line', 'payroll_id')
    f_mnth = fields.Char(compute='get_month', string='Month', store=True)
    
    pay_year = fields.Char('Year', readonly=True, store=True, default=date.today().strftime('%Y'))
    payroll_total = fields.Float(digits=(9, 2), string="Net Pay")
    grosstot = fields.Float(digits=(9, 2), string='Gross')
    deductions = fields.Float(digits=(9, 2), string='Deduction')
    absent_days = fields.Float(compute='get_absentdays',digits=(4,2),string='Absent Days',store=True)
    
    job_title = fields.Char(related='name.job_id.name',store=True)
    
    bank_account = fields.Char(related='name.bank_account_id.acc_number',store=True)
    item_id = fields.Char(string='Item Name',store=True)
    item_qty = fields.Float(string='Qty',store=True)
    item_mult = fields.Float(string='Multiplier',store=True)
#     line_total = fields.Float(string='Amount',store=True)
    product_cat = fields.Char( string='Product Category')
    state = fields.Selection([
        ('draft', "DRAFT"),
        ('compute', "COMPUTE"),
        ('paid', "PAID"),
        ('cancel', "CANCEL"),
    ],string='Status', readonly=True, copy=False, index=True,track_visibility='onchange', default='draft',
        help='* When the record is created the status is \'Draft\'.\
            \n* If the Record is Coomputed, the status is \'Compute\'. \
            \n* If the Record is Paid then status is set to \'Paid\'.\
            \n* When user cancel Record the status is change to either Draft or Sent depending on previous state ')
    
    x_year = fields.Selection([('2016','2016'),('2017','2017'),('2018','2018'),
                            ('2019','2019'),('2020','2020'),('2021','2021'),('2022','2022'),
                            ('2023','2023'),('2024','2024'),('2025','2025'),
                            ('2026','2026'),('2027','2027')],string='YEAR', required=True , default='2016')
    daysabsent = fields.Float('Days Absent_', digits=(4,2), required=True,default='0.0',
                               help="Days absent from Work in Month. Affects Base Salary")
    
        
    @api.one
    @api.constrains('start_date', 'end_date')
    def _check_valids(self):
        if self.start_date > self.end_date:
            raise ValidationError("Field start_date must be before end_date")
        clause = [('payroll_ref', '=', self.payroll_ref)]
        if self.search(clause):
            raise ValidationError("Payroll Already Created for this staff, Delete First")
        # check if year is current year
        fmt = '%Y-%m-%d'
        pdayofwk = datetime.datetime.strptime(self.end_date, fmt)
        thisyear = datetime.datetime.strftime(pdayofwk, '%Y')
        if self.x_year != thisyear:
            raise ValidationError("Year is not this year")
    
    @api.one
    @api.depends('name')
    def get_absentdays(self):
        clause_contract =  [('employee_id', '=', self.name.id)]
        contract_ids = self.env['hr.contract'].search(clause_contract)
        for contract in contract_ids:
            self.absent_days = contract.days_absent
            self.absent_days = self.daysabsent
            """
            The above needs to be fixed 
            so reference to contract.days_absent is removed
            """
            
    
    @api.one
    @api.depends('payroll_line_ids.line_total')
    def compute_payroll_total(self):
        self.payroll_total = sum(line.line_total for line in self.payroll_line_ids)
    
    top_name = fields.Char(compute='get_top_name', store=True)
    
    @api.one
    @api.depends('f_mnth','name')
    def get_top_name(self):
        if (self.f_mnth and self.name):            
            self.top_name = self.f_mnth.upper() + ' '+ self.x_year + ' Record' + ' for ' + self.name.name
        else:
            self.top_name = date.today().strftime('%B') + ' Payslip '
            
    @api.one
    @api.depends('name','start_date','end_date')
    def get_month(self):        
        fmt = '%Y-%m-%d'
        pdayofwk = datetime.datetime.strptime(self.end_date, fmt)
        self.f_mnth = datetime.datetime.strftime(pdayofwk, '%B')
     
        
        
       
    @api.one
    @api.depends('name','start_date','end_date')
    def get_workdays(self):
        
        fmt = '%Y-%m-%d'
        workdays = datetime.datetime.strptime(self.end_date, fmt) - datetime.datetime.strptime(self.start_date, fmt)          
        sundays = workdays.days / 7
        pdayofwk = datetime.datetime.strptime(self.end_date, fmt)
        spdayofwk = datetime.datetime.strptime(self.start_date, fmt)
        edayofwk = datetime.datetime.strftime(pdayofwk, '%A') 
        sdayofwk = datetime.datetime.strftime(spdayofwk, '%A')
        # if end_date is not sunday, add 1
        if  edayofwk == 'Sunday' or sdayofwk == 'Sunday':
            self.work_days_tot = workdays.days - sundays
        else:
            self.work_days_tot = workdays.days - sundays  + 1
    
    @api.one
    @api.depends('name','x_year')
    def get_ref(self):        
        self.payroll_ref =  'Payslip/' + str(self.name.name) + '/' + str(self.f_mnth) +'/' + self.x_year

    @api.one
    @api.depends('name','start_date','end_date')
    def get_invoice_totals(self,empnameidname):
        # Now get from contract
        account_invoice_obj = self.env['account.invoice.report']
        clause = [('date','>=',self.start_date),('date','<=',self.end_date),('categ_id.name','=',self.product_cat),('user_id.name','=', empnameidname)]
        gotten_fields = account_invoice_obj.search(clause)
        _logger.info("*** LOGGING Processing INVOICE ids len %i, CATEG %s",len(gotten_fields), self.product_cat)
        total=0.0
        for account_invoice in gotten_fields:
            total += account_invoice.product_qty
        self.item_qty = total
    
    def get_contract(self,empid):
        contract_obj = self.env['hr.contract']
        clause_contract =  [('employee_id', '=', empid)]
        contract_ids = contract_obj.search(clause_contract)
        return contract_ids
    
    @api.one    
    def get_kpcommission(self,empid):
        contract_ids = self.get_contract(empid)
        
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0
            else:
                self.item_qty = contract.kpbg_sold
                self.item_mult = contract.kpbgsold_mult
    
    @api.one    
    def get_obcommission(self,empid):
        contract_ids = self.get_contract(empid)
        
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0
            else:
                self.item_qty = contract.obbg_sold
                self.item_mult = contract.obbgsold_mult

    @api.one    
    def get_crcommission(self,empid):
        contract_ids = self.get_contract(empid)
        
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0
            else:
                self.item_qty = contract.crate_sold
                self.item_mult = contract.cratesold_mult

    @api.one    
    def get_dispcommission(self,empid):
        contract_ids = self.get_contract(empid)
        
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0
            else:
                self.item_qty = contract.disp_sold
                self.item_mult = contract.dispsold_mult


        
    @api.one
    def get_mult(self,empid,itemid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
#         
        for contract in contract_ids:
            if itemid == 'KP Bags Sales Commission':
                self.item_mult = contract.kpbgsold_mult
            elif itemid == 'OB Bags Sales Commission':
                self.item_mult = contract.obbgsold_mult            
            elif itemid == 'Crates Sales Commission':
                self.item_mult = contract.cratesold_mult
            elif itemid == 'Dispenser Sales Commission':
                self.item_mult = contract.dispsold_mult
            
    
    @api.one
    @api.depends('name','start_date','end_date')
    def get_bagger_totals(self,empid,empname):
        self.item_qty = 0
        self.item_mult = 0
        bagger_obj = self.env['fido.bagger']
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
#         month_f_end_date = datetime.datetime.strftime(date.today(), '%B').lower()
        month_f_end_date = self.f_mnth.lower()
        theyear = self.x_year
        _logger.info("*** LOGGING Processing BAGGER MONTH %s",month_f_end_date)
        clause =  [('name.name', '=', empname),('x_month', '=', month_f_end_date),('x_year', '=', theyear)]
        bagger_ids = bagger_obj.search(clause)
        _logger.info("*** LOGGING Processing LEN BAGGER ids %s",len(bagger_ids))
        if len(contract_ids) > 0:
            for contract in contract_ids:
                self.item_mult = contract.bagged_mult
        if len(bagger_ids) > 0:
            for bagger in bagger_ids:            
                self.item_qty = bagger.qty_total
                _logger.info("*** LOGGING Processing BAGGER TOTALs %s",bagger.qty_total)
            
    @api.one    
    def get_wage(self,empid):
        contract_ids = self.get_contract(empid)
        
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0
            else:
                self.item_qty = contract.wage
                self.item_mult = 1
            
    @api.one   
    def get_loan(self,empid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            self.item_qty = -1
            self.item_mult = contract.loan_adv
            
    @api.one    
    def get_sal(self,empid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            self.item_qty = -1
            self.item_mult = contract.sal_adv

    @api.one    
    def get_tax(self,empid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            self.item_qty = -1
            self.item_mult = contract.payee
    
    @api.one    
    def get_bag_mult(self,empid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        for contract in contract_ids:
            self.item_mult = contract.bagged_mult
    
    
    @api.one    
    def get_absentee(self,empid):
        contract_ids = self.get_contract(empid)
#         contract_obj = self.env['hr.contract']
#         clause_contract =  [('employee_id', '=', empid)]
#         contract_ids = contract_obj.search(clause_contract)
        self.item_qty = -1
        _logger.info("*** daysabsent_  = %s ",self.daysabsent)
        for contract in contract_ids:
            _logger.info("*** Contracttype  = %s ",contract.type_id.name)
            
            # if staff is disengaged, no need to compute absentee days
            if contract.date_end and contract.date_end <= self.start_date:
                self.item_qty = 0
                self.item_mult = 0        
            else:
                try:       
                    self.item_mult = (self.daysabsent / float(self.work_days_tot)) * contract.wage
                    _logger.info("*** absentdays,workdays,wage,ded  = %s %s %s %s ",self.daysabsent,self.work_days_tot,contract.wage,self.item_mult )
                    self.item_qty = -1
                except ZeroDivisionError:
                    _logger.exception("division by zero error work days total")
    
    @api.one
    @api.depends('name','start_date', 'end_date')
    def create_payslip(self):
        self.create_lines(self.name.id,self.name.name,self.name.user_id.name,self.f_mnth,self.work_days_tot)
        
    @api.multi 
    def computesheet(self, context=None):
        #_logger.info("login user is %s",self.user_id.login)
        self.create_payslip()
        return self.write({'state': 'compute'})        
        
    
    # state after Payroll is paid
    @api.multi 
    def pay(self, context=None):
        #_logger.info("login user is %s",self.user_id.login)
        
#         if (self.env.user.login == 'admin' or self.env.user.login == 'odia.gabriel@gtsng.com'):
#             _logger.info("PAYING BY %s",self.env.user.login)
#             self.pay_slip() # to xfer from bank to salary journal with staff name in memo
#             return self.write({'state': 'paid'})        
#         raise UserError(_('SORRY: Only MD or DMD Can Pay'))
#         return False
        self.pay_slip()
        return self.write({'state': 'paid'})
#         
    
    @api.multi 
    def pay_slip(self, context=None):
        # to xfer from bank to salary journal with staff name in memo
        
        """ Create a transfer from a FPL850 Bank Account to Salary journal """
        payment_model = self.env['account.payment']
        currency_ngn_id = self.env.ref("base.NGN").id
        _logger.info("**** base.NGN.id %s",currency_ngn_id)
        source_journal = self.env['account.journal'].search([('name', '=','FPL8520')])
        _logger.info("**** Source Journal %s",source_journal)
        salary_journal = self.env['account.journal'].search([('name', '=','Salary Journal')])
        _logger.info("**** Salary Journal %s",salary_journal)
        payment_method = self.env.ref("account.account_payment_method_manual_out")
        _logger.info("**** Payment Method %s",payment_method)
        memo = self.name.name + ' Payslip for ' + self.f_mnth
        payment = payment_model.create({
                            
#            'payment_date': time.strftime('%Y-%m-%d'),
            'payment_date': self.end_date,
            'payment_type': 'transfer',
            
            'communication': memo,
            'amount': self.payroll_total,
            'currency_id': currency_ngn_id,
            'journal_id': source_journal.id,
            'destination_journal_id': salary_journal.id,
            'payment_method_id': payment_method.id,
        })
        payment.post()                
        return True
            
    @api.one
#     @api.depends('name','start_date','end_date')
    def create_lines(self,empid,empname,empnameidname,month,workdaystot):
        item_obj = self.env['fido.payroll.item']
        itemid = item_obj.search([])    
#         empid = self.name.id
#         empname = self.name.name
#         empnameidname = self.name.user_id.name
        deduct = 0
        for item in itemid:

            self.set_items(item.name,empid,empname,empnameidname,month, workdaystot)
            item_id = self.item_id
            item_qty = self.item_qty
            item_mult = self.item_mult
            if (item_qty < 0) or (item_mult < 0):
                deduct += item_qty * item_mult
            line_total = item_qty * item_mult
            self.payroll_total += line_total
            self.deductions = deduct
            self.grosstot = self.payroll_total - self.deductions
            _logger.info("*** MAJOR CREATE_LINE ITEM ID,QTY, MULT for %s %s %s %s",item_id, item_qty, item_mult,empname)
            self.env['fido.payroll.line'].create({'payroll_id':self.id,'item_id':item_id,'item_qty':item_qty,'item_mult':item_mult,'line_total':line_total})
#             self.env['fido.payroll.line'].create({'payroll_id':self.id,'item_id':self.item_id,'item_qty':self.item_qty,'item_mult':self.item_mult,'line_total':self.line_total})
            #self.line_total = 0.0
    
    @api.one
    def set_items(self,item_id,empid,empname,empnameidname,month,workdaystot):        
        self.item_id = item_id
        self.item_qty = 0
        self.item_mult = 0
        
        # self.item_id = item_id
        if item_id == 'KP Bags Sales Commission':            
            self.product_cat = 'PUREWATER'
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.get_kpcommission(empid)
            
        elif item_id == 'OB Bags Sales Commission':            
            self.product_cat = 'PUREWATER'
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.get_obcommission(empid)
            
        elif item_id == 'Crates Sales Commission':            
            self.product_cat = 'BOTTLE CRATES'
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.get_crcommission(empid)
        elif item_id == 'Bagging Commission': 
            self.get_bagger_totals(empid,empname)                                
        
            
        elif item_id == 'Dispenser Sales Commission':            
            self.product_cat = 'DISPENSER'
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.get_dispcommission(empid)        
                
        elif item_id == 'Salary Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  %s ",self.item_id)
            self.get_sal(empid)
            
        elif item_id == 'Base Salary':
            self.get_wage(empid)        
                
        elif item_id == 'Loan Advance Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.get_loan(empid)
                
        elif item_id == 'PAYEE TAX Deduction(-ve)':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.get_tax(empid)
            
        elif item_id == 'Absentee Deductions':
            _logger.info("*** LOGGING Processing  = %s ",self.item_id)
            self.get_absentee(empid)
            
                        
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

#     @api.one
#     @api.constrains('item_id')
#     def _check_valids(self):
#         clause = [('item_id', '=', self.item_id)]
#         if self.search(clause):
#             raise ValidationError("Payroll Line Already added for this staff, Delete First")
# 
#             
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

# class account_invoice_inherit(models.Model):
#     _inherit = 'account.invoice'
#     _description = 'Changes the link between Customer name and salesperson'
#     partner_id = fields.Many2one('res.partner', string='Partner', change_default=True,
#         required=True, readonly=True, states={'draft': [('readonly', False)]},
#         track_visibility='always')
#     user_id = fields.Many2one(related='partner_id.user_id',string='Salesperson', track_visibility='onchange',
#         readonly=True, states={'draft': [('readonly', False)]})
#     date_invoice = fields.Date(string='Invoice Date',default=date.today(),
#         readonly=True, states={'draft': [('readonly', False)]}, index=True,
#         help="Change to correct date.", copy=False)

#     

# class fido_payroll_batch(models.Model):
#     _name = 'fido.payroll.batch'      
# #     _inherit = 'fido.payroll'
#     _description = 'create multiple payslips'
# #     payslip_ids = fields.One2many('fido.payroll', 'paybatch_id')
#     name = fields.Char(compute='get_name',readonly=True,string='Batch Name')
# #     batch_ref = fields.Char(compute='get_name',readonly=True,string='Batch Ref',store=True)
#     topname = fields.Char(compute='get_name',readonly=True,string='Top Name',store=True)
#     work_days_tot = fields.Integer(compute='get_name',readonly=True,string='Total Workdays',store=True)
#     
#     start_date = fields.Date('Date Begin',default=(date.today() + relativedelta(day=1)))
#     end_date = fields.Date('Date End',default=date.today())
#     b_month = fields.Char(string='Month',default=date.today().strftime('%B'))
#     
#     @api.one
#     @api.constrains('start_date', 'end_date')
#     def _check_valids(self):
#         if self.start_date > self.end_date:
#             raise ValidationError("Field start_date must be before end_date")
#        
#     @api.one
#     @api.depends('start_date','end_date')
#     def get_name(self):       
#         if (self.b_month):            
#             self.topname = 'Batch Payroll for ' + str(self.b_month)
#             self.name = 'Payroll for ' + str(self.b_month) 
#             self.batch_ref = 'Fido/Payroll/' + str(self.b_month)
#         else:
#             self.b_month =  date.today().strftime('%B') 
#             self.topname = 'Batch Payroll for ' + str(self.b_month)
#             self.name = 'Payroll for ' + str(self.b_month) 
#             self.batch_ref = 'Fido/Payroll/' + str(self.b_month)
#         fmt = '%Y-%m-%d'
#         workdays = datetime.datetime.strptime(self.end_date, fmt) - datetime.datetime.strptime(self.start_date, fmt)          
#         sundays = workdays.days / 7 
#         self.work_days_tot = workdays.days - sundays
#         
#     @api.one    
#     @api.depends('start_date','end_date')
#     def create_batch(self):
#         emp_obj = self.env['hr.employee']
#         for emp in emp_obj.search([]):
#             _logger.info("*** BATCH Processing  = %s | %s ",emp.name,emp.user_id.name)
#             self.env['fido.payroll'].create({'paybatch_id':self.id,'name':emp_obj,'start_date':self.start_date,'end_date':self.end_date,'f_mnth':self.b_month})
#             
#             _logger.info("*** BATCH Processing  AFTER Create LINES %s ",emp.name)
#             
#    
#         # bagger needs name
#             
#     
#     
#     
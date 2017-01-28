# Execute a method in hr.employee with parameters from cmd prompt I guess

# models.execute_kw(db, uid, password, ‘hr.employee’, 
#        ‘attendance_action_change’, [employee_id], 
#          {'action':'sign_in', 'action_date':'2014-04-01' })
#          
# Create x number of dummy invoices, 
# export them to a csv to get their invoice_ids and 
#   use the IDs to import new invoices

#   Extend account.invoice
#   include createdummy button under 'customer invoices' menu
#   provide number of dummy invoices and prefix (optional)
#   then create the invoices
#   then retrieve/expose the External_IDs of the newly created invoices
#   TO be used for import statement.
#

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
class account_invoice(models.Model):
    _inherit = 'account.invoice'
    _description = 'Extends account.invoive to add new menus'
    
    def cr_customer_invoice(self):
        # Create a customer invoice
        self.account_invoice_obj = self.env['account.invoice']
        self.payment_term = self.env.ref('account.account_payment_term_advance')
        self.journalrec = self.env['account.journal'].search([('type', '=', 'sale')])[0]
        self.partner3 = self.env.ref('base.res_partner_3') # use valid partner
        account_user_type = self.env.ref('account.data_account_type_receivable')
        self.ova = self.env['account.account'].search([('user_type_id', '=', 
                    self.env.ref('account.data_account_type_current_assets').id)], limit=1)
        
        #only adviser can create an account
        # create an Account ID or use Account Receivable
        self.account_rec1_id = self.env['account.account'].search([('account_id.name', 
                    '=', 'Account Receivable')])
        
        self.account_invoice_customer0 = self.account_invoice_obj.sudo(self.account_user.id).create(dict(
            name="Test Customer Invoice",
            reference_type="none",
            payment_term_id=self.payment_term.id,
            journal_id=self.journalrec.id,
            partner_id=self.partner3.id, # we can use existing partner id
            account_id=self.account_rec1_id.id,  # This should be Account receivable
            invoice_line_ids= Null
        ))

    
    
    



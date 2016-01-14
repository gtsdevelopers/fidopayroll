from openerp import api, fields, models
import datetime

class fido_bagging(models.Model):
	_name = "fido.bagger"
	name = fields.Many2one('hr.employee',string='Bagger', size=32, required=True)
	bagger_line_ids = fields.One2many('fido.bagger.line', 'bagger_id')
	x_month = fields.Selection([('january','January'),('february','February'),('march','March'),
							('april','April'),('may','May'),('june','June'),('july','July'),
							('august','August'),('september','September'),('october','October'),
							('november','November'),('december','December')],string='Month', required=True , default='january')
	qty_total = fields.Float(compute='compute_bagging_total', string='Total')
	top_name = fields.Char(compute='get_month')
	
	@api.one
	@api.depends('x_month')
	def get_month(self):
#		if self.x_month in self:
		for record in self:
			record.top_name = record.x_month.title() + ' Record'
		
	
	@api.one
	@api.depends('bagger_line_ids.x_quantity')
	def compute_bagging_total(self):
		self.qty_total = sum(line.x_quantity for line in self.bagger_line_ids)
		

class fido_bagger_line(models.Model):
	_name ="fido.bagger.line"
	bagger_id = fields.Many2one('fido.bagger', string='Fido Reference')
	fido_date = fields.Date(default=fields.Date.today(), required=True)
	x_quantity = fields.Integer(string="No of Bags", required=True)
	
	
	

class fido_bagging_inherit(models.Model):
	_inherit =  "hr.employee"
	@api.one
	def compute_bag_total(self):
		cursor = self._cr
		user = self._uid
		for employees in self:
			today = datetime.datetime.today()
			start_date = str(today.replace(day=1).strftime('%Y-%m-%d'))
			next_month = today.replace(day=28) + datetime.timedelta(days=4)
			end_date = str(next_month - datetime.timedelta(days=next_month.day))
			#look up the bagging records
			fido_bagger_obj = self.pool.get('fido.bagger')
			bagger_ids = fido_bagger_obj.search(cursor, user,[('fido_date','>=',start_date),('fido_date','<=',end_date),('name','=',employees.name)])
#			bagger_ids = fido_bagger_obj.search(cursor, user, [('name','=',employees.id)])
			total = 0.0
			for fido_bagger in fido_bagger_obj.browse(cursor, user, bagger_ids):
				total += fido_bagger.x_quantity
			employees.mtd_bag = total
# 	mtd_bag = fields.Float(compute='compute_bag_total',string="Month Bag")
	
	

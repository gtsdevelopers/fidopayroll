from openerp import api, fields, models
import datetime

class fido_bagging(models.Model):
	_name = "fido.bagger"
	name = fields.Many2one('hr.employee',string='Bagger', size=32, required=True)
	fido_date = fields.Date(string='Date')
	x_quantity = fields.Integer(string="No of Bags")
	

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
	
	

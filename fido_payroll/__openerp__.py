{
	'name': 'FIDO PAYROLL',
	'version': '1.0',
	'description': """
	FIDO PAYROLL 
	Extends HR Contract to include commission Multipliers and
	Computes Fido Payroll Automatically from Sales Invoices
	and Bagger Details and Employee Contracts
	""",
	'category': 'Human Resources',
	'website': 'http://gts.com.ng',
	'author': 'GTS LTD',
	'depends': ['account_accountant','hr','hr_payroll'],
	'data': ['views/fidopayroll_view.xml','views/fidopayroll_item.xml',
			'views/fidopayroll_button_view.xml','views/hr_contract_view.xml',
			'views/fidopayroll_report_view.xml','views/fidopayroll_report.xml'],
	'demo': [],
	'installabe': True,
	'auto_install': False,
}

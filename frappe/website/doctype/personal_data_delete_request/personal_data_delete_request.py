# -*- coding: utf-8 -*-
# Copyright (c) 2019, Frappe Technologies and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.verified_command import get_signed_params, verify_request

class PersonalDataDeleteRequest(Document):

	def after_insert(self):
		if frappe.session.user in ['Administrator', 'Guest']:
			frappe.throw(_("This user's data cannot be requested for deletion"))
		else:
			self.send_verification_mail()

	def send_verification_mail(self):
		url = frappe.utils.get_url("/api/method/frappe.website.doctype.personal_data_delete_request.personal_data_delete_request.confirm_deletion") +\
		"?" + get_signed_params({"email": self.email})

		frappe.sendmail(recipients= self.email,
		subject=_("ERPNext: Confirm Deletion of Data"),
		template="delete_data_confirmation",
		args={'email':self.email, 'link':url},
		header=[_("ERPNext: Confirm Deletion of Data"), "green"])

	def anonymize_data(self):
		privacy_docs = frappe.get_hooks("user_privacy_documents")
		for ref_doc in privacy_docs:
			for email_field in ref_doc.get('email_fields'):
				frappe.db.sql("""UPDATE `tab{0}` 
					SET `{1}` = '{2}', {3}
					WHERE `{1}` = '{4}' """.format(ref_doc['doctype'], email_field, self.name,
						', '.join(map(lambda u :'`'+ u+'`=\''+str(u)+'\'', ref_doc.get('personal_fields',[]))), self.email))

@frappe.whitelist(allow_guest=True)
def confirm_deletion(email):
	if not verify_request:
		return
	frappe.set_value("Personal Data Delete Request", {'email':email}, 'status', 'Pending Approval')
	frappe.db.commit()
	frappe.respond_as_web_page(_("Confirmed"),
		_("The process for deletion of ERPNext Data associated with {0} has been initiated.").format(email),
		indicator_color='green')
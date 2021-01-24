from odoo import api, fields, models, _, tools
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.exceptions import ValidationError
from odoo.exceptions import Warning
from dateutil.relativedelta import relativedelta
from datetime import date


class preventivechecklist(models.Model):
    _name = 'preventive.checklist'
    _rec_name = 'name'
    name = fields.Char(string="Name", required=False, )
    html_field = fields.Html(string="  ", )

class NewModule(models.Model):
    _inherit = 'project.project'

    new_field_id = fields.Many2one(comodel_name="preventive.checklist", string="Maintenance Check List", required=False, )


class orderrepair(models.Model):
    _inherit = 'repair.order'

    new_field_project_id = fields.Many2one(comodel_name="project.project", string="Project", required=False, )

    name_center_point = fields.Char(string="", required=False,related='new_field_project_id.new_field_id.name')
    cp_id = fields.Html(string="", required=False,related='new_field_project_id.new_field_id.html_field',readonly= False)

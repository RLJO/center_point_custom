# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import models, fields, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partner_project = fields.Many2one('project.project', string='Partner Branch')


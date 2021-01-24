# -*- coding: utf-8 -*-
# from odoo import http


# class CenterPointRepairTotalInvoices(http.Controller):
#     @http.route('/center_point_repair_total_invoices/center_point_repair_total_invoices/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/center_point_repair_total_invoices/center_point_repair_total_invoices/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('center_point_repair_total_invoices.listing', {
#             'root': '/center_point_repair_total_invoices/center_point_repair_total_invoices',
#             'objects': http.request.env['center_point_repair_total_invoices.center_point_repair_total_invoices'].search([]),
#         })

#     @http.route('/center_point_repair_total_invoices/center_point_repair_total_invoices/objects/<model("center_point_repair_total_invoices.center_point_repair_total_invoices"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('center_point_repair_total_invoices.object', {
#             'object': obj
#         })

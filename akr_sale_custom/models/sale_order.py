# -*- coding: utf-8 -*-

from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()   # Confirm the sale order 1st

        for order in self:
            product_lines = {}
            for line in order.order_line:
                picking_ids  = line.order_id.picking_ids
                moves = picking_ids.mapped('move_ids_without_package').filtered(lambda x: x.product_id == line.product_id)
                moves.write({'group_id': False})
                if line.product_id in product_lines:
                    product_lines[line.product_id]['quantity'] += line.product_uom_qty
                else:
                    product_lines[line.product_id] = {
                        'product_id': line.product_id,
                        'quantity': line.product_uom_qty,
                        'uom': line.product_uom,
                    }

            for product, values in product_lines.items():
                picking = self.env['stock.picking'].create({
                    'partner_id': order.partner_id.id,
                    'picking_type_id': order.warehouse_id.out_type_id.id,
                    'location_id': order.warehouse_id.lot_stock_id.id,
                    'location_dest_id': order.partner_id.property_stock_customer.id,
                    'sale_id': order.id,
                    'origin': order.name,
                    'move_ids_without_package' : [(0, 0, {
                        'name': product.name,
                        'product_id': product.id,
                        'product_uom_qty': values['quantity'],
                        'product_uom': values['uom'].id,
                        'location_id': order.warehouse_id.lot_stock_id.id,
                        'location_dest_id': order.partner_id.property_stock_customer.id,
                    })]
                })

                picking.action_confirm()

        return res
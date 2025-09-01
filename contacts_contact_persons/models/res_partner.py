from odoo import models, fields, api, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    contact_persons_ids = fields.One2many('contact.persons', 'partner_id', string='Contactos Adicionales')
    contact_persons_count = fields.Integer(string='Número de Contactos Adicionales', compute='_compute_contact_persons_count')
    
    @api.depends('contact_persons_ids')
    def _compute_contact_persons_count(self):
        for record in self:
            record.contact_persons_count = len(record.contact_persons_ids)
    
    def action_view_contact_persons(self):
        self.ensure_one()
        return {
            'name': _('Contactos Adicionales de %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'contact.persons',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
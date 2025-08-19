import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";
import { patch } from "@web/core/utils/patch";

patch(PartnerList.prototype, {

    getPartners() {
        const partners = super.getPartners(...arguments);

        const filteredPartners = partners.filter(partner => partner.pos_customer === true);

        return filteredPartners;
    },
});

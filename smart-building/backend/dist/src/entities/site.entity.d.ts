import { Zone } from './zone.entity';
import { Organization } from './organization.entity';
import { Gateway } from './gateway.entity';
export declare class Site {
    id: string;
    name: string;
    type: string;
    address: string;
    city: string;
    postalCode: string;
    country: string;
    latitude: number;
    longitude: number;
    zones: Zone[];
    organization: Organization;
    organizationId: string;
    gateways: Gateway[];
    deletedAt: Date;
}

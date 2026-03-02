import { User } from './user.entity';
import { Site } from './site.entity';
export declare class Organization {
    id: string;
    name: string;
    type: string;
    country: string;
    contactFirstName: string;
    contactLastName: string;
    city: string;
    address: string;
    postalCode: string;
    phone: string;
    email: string;
    establishmentDate: string;
    legalForm: string;
    subscriptionPlan: string;
    maxUsers: number;
    maxDevices: number;
    maxSites: number;
    createdAt: Date;
    users: User[];
    sites: Site[];
}

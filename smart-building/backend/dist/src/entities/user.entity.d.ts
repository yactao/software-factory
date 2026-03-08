import { Organization } from './organization.entity';
import { CustomRole } from './custom-role.entity';
export declare enum UserRole {
    SUPER_ADMIN = "SUPER_ADMIN",
    ADMIN_FONCTIONNEL = "ADMIN_FONCTIONNEL",
    CLIENT = "CLIENT"
}
export declare class User {
    id: string;
    email: string;
    name: string;
    password: string;
    role: UserRole;
    organization: Organization;
    customRole: CustomRole;
    createdAt: Date;
}

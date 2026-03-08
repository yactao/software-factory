import { Entity, PrimaryGeneratedColumn, Column, CreateDateColumn, ManyToOne, JoinColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { CustomRole } from './custom-role.entity';

export enum UserRole {
    SUPER_ADMIN = 'SUPER_ADMIN',
    ADMIN_FONCTIONNEL = 'ADMIN_FONCTIONNEL',
    CLIENT = 'CLIENT',
}

@Entity('users')
export class User {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    email: string;

    @Column()
    name: string;

    @Column({ default: 'password123' })
    password: string;

    @Column({
        type: 'varchar',
        default: UserRole.CLIENT,
    })
    role: UserRole;

    @ManyToOne(() => Organization, org => org.users, { nullable: true, onDelete: 'CASCADE' })
    @JoinColumn({ name: 'organizationId' })
    organization: Organization;

    // Added to fix CustomRole relationship
    @ManyToOne(() => CustomRole, customRole => customRole.users, { nullable: true, onDelete: 'SET NULL' })
    @JoinColumn({ name: 'customRoleId' })
    customRole: CustomRole;

    @CreateDateColumn()
    createdAt: Date;
}

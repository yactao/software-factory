import { Entity, PrimaryGeneratedColumn, Column, ManyToOne, OneToMany, JoinColumn, CreateDateColumn } from 'typeorm';
import { Organization } from './organization.entity';
import { User } from './user.entity';

@Entity('custom_roles')
export class CustomRole {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column({ nullable: true })
    description: string;

    @Column('simple-json', { default: '[]' })
    permissions: string[]; // Exemple: ['view:dashboard', 'edit:equipments']

    @ManyToOne(() => Organization, org => org.customRoles, { nullable: true, onDelete: 'CASCADE' })
    @JoinColumn({ name: 'organizationId' })
    organization: Organization;

    @OneToMany(() => User, user => user.customRole)
    users: User[];

    @CreateDateColumn()
    createdAt: Date;
}

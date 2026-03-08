import { Entity, Column, PrimaryGeneratedColumn, CreateDateColumn, ManyToOne } from 'typeorm';
import { User } from './user.entity';

@Entity('audit_logs')
export class AuditLog {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    action: string; // e.g., 'UPDATE_HVAC', 'CREATE_USER', 'DELETE_ZONE'

    @Column()
    resource: string; // e.g., 'Zone: Bureau12', 'Equipment: HVAC_01'

    @Column({ type: 'text', nullable: true })
    details: string; // Additional JSON context or description

    @ManyToOne(() => User, { nullable: true, onDelete: 'SET NULL' })
    user: User; // Who performed the action

    @Column({ nullable: true })
    organizationId: string; // To split logs per client

    @CreateDateColumn()
    timestamp: Date;
}

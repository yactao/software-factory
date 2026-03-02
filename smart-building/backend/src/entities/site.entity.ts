import { Entity, Column, PrimaryGeneratedColumn, OneToMany, ManyToOne, JoinColumn } from 'typeorm';
import { Zone } from './zone.entity';
import { Organization } from './organization.entity';
import { Gateway } from './gateway.entity';

@Entity()
export class Site {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column({ nullable: true })
    type: string; // 'Bureaux', 'Usine', 'Magasin'

    @Column()
    address: string;

    @Column()
    city: string;

    @Column({ nullable: true })
    postalCode: string;

    @Column({ nullable: true })
    country: string;

    @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
    latitude: number;

    @Column({ type: 'decimal', precision: 10, scale: 6, nullable: true })
    longitude: number;

    @OneToMany(() => Zone, (zone) => zone.site)
    zones: Zone[];

    @ManyToOne(() => Organization, org => org.sites, { nullable: true, onDelete: 'CASCADE' })
    @JoinColumn({ name: 'organizationId' })
    organization: Organization;

    @Column({ nullable: true })
    organizationId: string;

    @OneToMany(() => Gateway, gateway => gateway.site)
    gateways: Gateway[];
}

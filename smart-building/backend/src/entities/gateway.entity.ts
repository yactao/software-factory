import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, OneToMany, CreateDateColumn, DeleteDateColumn } from 'typeorm';
import { Site } from './site.entity';
import { Sensor } from './sensor.entity';

@Entity()
export class Gateway {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    serialNumber: string; // MAC address or serial number

    @Column()
    name: string;

    @Column({ default: 'online' })
    status: string; // online, offline, maintenance

    @Column({ nullable: true })
    ipAddress: string;

    @Column({ nullable: true })
    protocol: string; // zigbee, lorawan, zwave, modbus, wifi, enocean

    @CreateDateColumn()
    createdAt: Date;

    @ManyToOne(() => Site, site => site.gateways, { onDelete: 'CASCADE' })
    site: Site;

    @OneToMany(() => Sensor, sensor => sensor.gateway)
    sensors: Sensor[];

    @DeleteDateColumn()
    deletedAt: Date;
}

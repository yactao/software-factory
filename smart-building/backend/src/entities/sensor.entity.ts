import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, OneToMany, DeleteDateColumn } from 'typeorm';
import { Zone } from './zone.entity';
import { Reading } from './reading.entity';
import { Gateway } from './gateway.entity';

@Entity()
export class Sensor {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column({ unique: true })
    externalId: string; // e.g., devEUI or MQTT client ID

    @Column()
    name: string;

    @Column()
    type: string; // 'temperature', 'humidity', 'co2', 'presence', 'energy'

    @Column({ nullable: true })
    unit: string;

    @ManyToOne(() => Zone, (zone) => zone.sensors)
    zone: Zone;

    @OneToMany(() => Reading, (reading) => reading.sensor)
    readings: Reading[];

    @ManyToOne(() => Gateway, gateway => gateway.sensors, { nullable: true })
    gateway: Gateway;

    @DeleteDateColumn()
    deletedAt: Date;
}

import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, OneToMany, DeleteDateColumn } from 'typeorm';
import { Site } from './site.entity';
import { Sensor } from './sensor.entity';

@Entity()
export class Zone {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column()
    name: string;

    @Column()
    type: string; // 'Office', 'Meeting Room', 'Hall', etc.

    @Column({ nullable: true })
    floor: string; // e.g. 'RDC', 'R+1', 'Sous-sol'

    @ManyToOne(() => Site, (site) => site.zones)
    site: Site;

    @OneToMany(() => Sensor, (sensor) => sensor.zone)
    sensors: Sensor[];

    @DeleteDateColumn()
    deletedAt: Date;
}

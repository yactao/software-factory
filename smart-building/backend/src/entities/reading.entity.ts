import { Entity, Column, PrimaryGeneratedColumn, ManyToOne, Index } from 'typeorm';
import { Sensor } from './sensor.entity';

@Entity()
@Index(['sensor', 'timestamp'])
export class Reading {
    @PrimaryGeneratedColumn('uuid')
    id: string;

    @Column('float')
    value: number;

    @Index()
    @Column() // For SQLite, simple column is fine for dates or use 'datetime'
    timestamp: Date;

    @ManyToOne(() => Sensor, (sensor) => sensor.readings)
    sensor: Sensor;
}

import { Zone } from './zone.entity';
import { Reading } from './reading.entity';
import { Gateway } from './gateway.entity';
export declare class Sensor {
    id: string;
    externalId: string;
    name: string;
    type: string;
    unit: string;
    zone: Zone;
    readings: Reading[];
    gateway: Gateway;
    deletedAt: Date;
}

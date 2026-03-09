import { Site } from './site.entity';
import { Sensor } from './sensor.entity';
export declare class Gateway {
    id: string;
    serialNumber: string;
    name: string;
    status: string;
    ipAddress: string;
    protocol: string;
    createdAt: Date;
    site: Site;
    sensors: Sensor[];
    deletedAt: Date;
}

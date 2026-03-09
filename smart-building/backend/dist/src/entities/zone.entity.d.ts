import { Site } from './site.entity';
import { Sensor } from './sensor.entity';
export declare class Zone {
    id: string;
    name: string;
    type: string;
    floor: string;
    site: Site;
    sensors: Sensor[];
    deletedAt: Date;
}

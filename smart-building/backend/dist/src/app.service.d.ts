import { OnModuleInit } from '@nestjs/common';
import { Repository } from 'typeorm';
import { Site } from './entities/site.entity';
import { Zone } from './entities/zone.entity';
import { Sensor } from './entities/sensor.entity';
import { Reading } from './entities/reading.entity';
import { Alert } from './entities/alert.entity';
import { Organization } from './entities/organization.entity';
import { User } from './entities/user.entity';
import { Gateway } from './entities/gateway.entity';
import { PayloadFormatterService } from './iot/payload-formatter.service';
import { RulesEngineService } from './rules-engine.service';
import { EventsGateway } from './iot/events.gateway';
export declare class AppService implements OnModuleInit {
    private siteRepo;
    private zoneRepo;
    private sensorRepo;
    private readingRepo;
    private alertRepo;
    private orgRepo;
    private userRepo;
    private gatewayRepo;
    private payloadFormatter;
    private rulesEngine;
    private eventsGateway;
    constructor(siteRepo: Repository<Site>, zoneRepo: Repository<Zone>, sensorRepo: Repository<Sensor>, readingRepo: Repository<Reading>, alertRepo: Repository<Alert>, orgRepo: Repository<Organization>, userRepo: Repository<User>, gatewayRepo: Repository<Gateway>, payloadFormatter: PayloadFormatterService, rulesEngine: RulesEngineService, eventsGateway: EventsGateway);
    checkHealth(): Promise<{
        status: string;
        timestamp: string;
        uptime: number;
        memory: {
            rss: string;
            heapTotal: string;
            heapUsed: string;
        };
        database: string;
        error?: undefined;
    } | {
        status: string;
        timestamp: string;
        database: string;
        error: string;
        uptime?: undefined;
        memory?: undefined;
    }>;
    onModuleInit(): Promise<void>;
    getHello(): string;
    getSites(orgId?: string): Promise<{
        statusColor: string;
        id: string;
        name: string;
        type: string;
        address: string;
        city: string;
        postalCode: string;
        country: string;
        latitude: number;
        longitude: number;
        zones: Zone[];
        organization: Organization;
        organizationId: string;
        gateways: Gateway[];
    }[]>;
    getOrganizations(): Promise<{
        sitesCount: number;
        usersCount: number;
        gatewaysCount: number;
        devicesCount: number;
        id: string;
        name: string;
        type: string;
        country: string;
        contactFirstName: string;
        contactLastName: string;
        city: string;
        address: string;
        postalCode: string;
        phone: string;
        email: string;
        establishmentDate: string;
        legalForm: string;
        subscriptionPlan: string;
        maxUsers: number;
        maxDevices: number;
        maxSites: number;
        createdAt: Date;
        users: User[];
        sites: Site[];
    }[]>;
    private geocodeAddress;
    createOrganization(orgData: any): Promise<Organization[]>;
    updateOrganization(id: string, orgData: any): Promise<Organization | null>;
    deleteOrganization(id: string): Promise<import("typeorm").DeleteResult>;
    createSite(siteData: any, orgId: string): Promise<Site[]>;
    updateSite(id: string, siteData: any): Promise<Site | null>;
    deleteSite(id: string): Promise<import("typeorm").DeleteResult>;
    createZone(zoneData: any, siteId: string): Promise<Zone[]>;
    getGateways(orgId?: string): Promise<Gateway[]>;
    createGateway(gatewayData: any): Promise<Gateway[]>;
    getSensors(orgId?: string): Promise<Sensor[]>;
    getReadings(limit?: number, orgId?: string): Promise<Reading[]>;
    getGlobalEnergy(orgId?: string, siteId?: string): Promise<{
        timestamp: string;
        globalValue: number;
        hvacValue: number;
        unit: string;
    }[]>;
    getAverageTemperature(orgId?: string, siteId?: string): Promise<{
        day: string;
        averageTemp: number;
    }[]>;
    getAlerts(orgId?: string, siteId?: string): Promise<Alert[]>;
    getHvacPerformance(orgId?: string, siteId?: string): Promise<{
        day: string;
        runtime: number;
        setpoint: number;
        actual: number;
    }[]>;
    processIotWebhook(webhookData: any): Promise<{
        success: boolean;
        readingId: string;
        decoded: import("./iot/payload-formatter.service").DecodedPayload;
    }>;
    globalSearch(query: string, orgId: string, role: string): Promise<any[]>;
    getUsers(organizationId?: string): Promise<User[]>;
    createUser(userData: any): Promise<User[]>;
    updateUser(id: string, userData: any): Promise<User | null>;
    deleteUser(id: string): Promise<{
        success: boolean;
    }>;
    executeEquipmentAction(payload: {
        equipmentId: string;
        action: string;
        value?: any;
    }): Promise<{
        success: boolean;
        message: string;
        details: {
            equipmentId: string;
            action: string;
            value?: any;
        };
    }>;
    getDashboardKpis(orgId: string, role: string): Promise<{
        totalClients: number;
        totalSites: number;
        activeIncidents: number;
        offlineGateways: number;
        totalZones: number;
        totalSensors: number;
        outOfTargetSites: number;
        globalHealthScore: number;
        activeUsers: number;
        criticalAlerts: number;
    }>;
}

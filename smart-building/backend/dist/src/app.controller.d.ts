import { AppService } from './app.service';
import { RulesEngineService } from './rules-engine.service';
export declare class AppController {
    private readonly appService;
    private readonly rulesEngineService;
    constructor(appService: AppService, rulesEngineService: RulesEngineService);
    getHello(): string;
    getHealth(): Promise<{
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
    getSites(orgId: string, role?: string): Promise<{
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
        zones: import("./entities/zone.entity").Zone[];
        organization: import("./entities/organization.entity").Organization;
        organizationId: string;
        gateways: import("./entities/gateway.entity").Gateway[];
        deletedAt: Date;
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
        users: import("./entities/user.entity").User[];
        sites: import("./entities/site.entity").Site[];
        customRoles: import("./entities/custom-role.entity").CustomRole[];
    }[]>;
    createOrganization(orgData: any): Promise<import("./entities/organization.entity").Organization[]>;
    updateOrganization(id: string, orgData: any): Promise<import("./entities/organization.entity").Organization | null>;
    deleteOrganization(id: string): Promise<import("typeorm").DeleteResult>;
    createSite(orgId: string, siteData: any): Promise<import("./entities/site.entity").Site[]>;
    updateSite(id: string, siteData: any): Promise<import("./entities/site.entity").Site | null>;
    deleteSite(id: string): Promise<import("typeorm").DeleteResult>;
    createZone(zoneData: any): Promise<import("./entities/zone.entity").Zone[]>;
    updateZone(id: string, zoneData: any): Promise<import("./entities/zone.entity").Zone | null>;
    deleteZone(id: string): Promise<import("typeorm").DeleteResult>;
    getSensors(orgId: string, role?: string): Promise<import("./entities/sensor.entity").Sensor[]>;
    getGateways(orgId: string, role?: string): Promise<import("./entities/gateway.entity").Gateway[]>;
    createGateway(gatewayData: any): Promise<import("./entities/gateway.entity").Gateway[]>;
    getReadings(limit?: string, orgId?: string): Promise<import("./entities/reading.entity").Reading[]>;
    getGlobalEnergy(orgId: string, siteId?: string): Promise<{
        timestamp: string;
        globalValue: number;
        hvacValue: number;
        unit: string;
    }[]>;
    getAverageTemperature(orgId: string, siteId?: string): Promise<{
        day: string;
        averageTemp: number;
    }[]>;
    getAlerts(orgId: string, role?: string, siteId?: string): Promise<import("./entities/alert.entity").Alert[]>;
    getHvacPerformance(orgId: string, siteId?: string): Promise<{
        day: string;
        runtime: number;
        setpoint: number;
        actual: number;
    }[]>;
    getRules(orgId: string, role?: string): Promise<import("./entities/rule.entity").Rule[]>;
    createRule(orgId: string, ruleData: any): Promise<import("./entities/rule.entity").Rule[]>;
    processIotWebhook(webhookData: any): Promise<{
        success: boolean;
        readingId: string;
        decoded: import("./iot/payload-formatter.service").DecodedPayload;
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
    globalSearch(q: string, orgId: string, role: string): Promise<any[]>;
    getUsers(orgId?: string): Promise<import("./entities/user.entity").User[]>;
    createUser(userData: any): Promise<import("./entities/user.entity").User[]>;
    updateUser(id: string, userData: any): Promise<import("./entities/user.entity").User | null>;
    deleteUser(id: string): Promise<{
        success: boolean;
    }>;
    getCustomRoles(orgId?: string): Promise<import("./entities/custom-role.entity").CustomRole[]>;
    createCustomRole(roleData: any): Promise<import("./entities/custom-role.entity").CustomRole[]>;
    updateCustomRole(id: string, roleData: any): Promise<import("./entities/custom-role.entity").CustomRole | null>;
    deleteCustomRole(id: string): Promise<{
        success: boolean;
    }>;
    executeEquipmentAction(orgId: string, payload: {
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
}

"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
var __metadata = (this && this.__metadata) || function (k, v) {
    if (typeof Reflect === "object" && typeof Reflect.metadata === "function") return Reflect.metadata(k, v);
};
var __param = (this && this.__param) || function (paramIndex, decorator) {
    return function (target, key) { decorator(target, key, paramIndex); }
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.AppService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const site_entity_1 = require("./entities/site.entity");
const zone_entity_1 = require("./entities/zone.entity");
const sensor_entity_1 = require("./entities/sensor.entity");
const reading_entity_1 = require("./entities/reading.entity");
const alert_entity_1 = require("./entities/alert.entity");
const organization_entity_1 = require("./entities/organization.entity");
const user_entity_1 = require("./entities/user.entity");
const gateway_entity_1 = require("./entities/gateway.entity");
const custom_role_entity_1 = require("./entities/custom-role.entity");
const payload_formatter_service_1 = require("./iot/payload-formatter.service");
const rules_engine_service_1 = require("./rules-engine.service");
const events_gateway_1 = require("./iot/events.gateway");
let AppService = class AppService {
    siteRepo;
    zoneRepo;
    sensorRepo;
    readingRepo;
    alertRepo;
    orgRepo;
    userRepo;
    customRoleRepo;
    gatewayRepo;
    payloadFormatter;
    rulesEngine;
    eventsGateway;
    constructor(siteRepo, zoneRepo, sensorRepo, readingRepo, alertRepo, orgRepo, userRepo, customRoleRepo, gatewayRepo, payloadFormatter, rulesEngine, eventsGateway) {
        this.siteRepo = siteRepo;
        this.zoneRepo = zoneRepo;
        this.sensorRepo = sensorRepo;
        this.readingRepo = readingRepo;
        this.alertRepo = alertRepo;
        this.orgRepo = orgRepo;
        this.userRepo = userRepo;
        this.customRoleRepo = customRoleRepo;
        this.gatewayRepo = gatewayRepo;
        this.payloadFormatter = payloadFormatter;
        this.rulesEngine = rulesEngine;
        this.eventsGateway = eventsGateway;
    }
    async checkHealth() {
        try {
            await this.orgRepo.count();
            const memoryUsage = process.memoryUsage();
            return {
                status: 'OK',
                timestamp: new Date().toISOString(),
                uptime: process.uptime(),
                memory: {
                    rss: `${Math.round(memoryUsage.rss / 1024 / 1024)} MB`,
                    heapTotal: `${Math.round(memoryUsage.heapTotal / 1024 / 1024)} MB`,
                    heapUsed: `${Math.round(memoryUsage.heapUsed / 1024 / 1024)} MB`,
                },
                database: 'Connected'
            };
        }
        catch (error) {
            return {
                status: 'ERROR',
                timestamp: new Date().toISOString(),
                database: 'Disconnected',
                error: error instanceof Error ? error.message : 'Unknown'
            };
        }
    }
    async onModuleInit() {
        const orgCount = await this.orgRepo.count();
        if (orgCount === 0) {
            console.log('🌱 Seeding initial V2 data (Organizations, Users, Sites)...');
            const org1Id = '11111111-1111-1111-1111-111111111111';
            const org2Id = '22222222-2222-2222-2222-222222222222';
            const org3Id = '33333333-3333-3333-3333-333333333333';
            const org4Id = '44444444-4444-4444-4444-444444444444';
            await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org1Id}', 'UBBEE', 'SaaS Provider')`);
            await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org2Id}', 'CASA', 'Retail')`);
            await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org3Id}', 'Leroy Merlin', 'Retail/Bricolage')`);
            await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org4Id}', 'Maison du Monde', 'Retail')`);
            const orgUbbee = (await this.orgRepo.findOne({ where: { id: org1Id } }));
            const orgCasa = (await this.orgRepo.findOne({ where: { id: org2Id } }));
            const orgLeroy = (await this.orgRepo.findOne({ where: { id: org3Id } }));
            const orgMaison = (await this.orgRepo.findOne({ where: { id: org4Id } }));
            const adminUser = this.userRepo.create({ name: 'Super Admin', email: 'admin@ubbee.fr', password: 'admin', role: user_entity_1.UserRole.SUPER_ADMIN, organization: orgUbbee });
            const managerUser = this.userRepo.create({ name: 'Energy Manager', email: 'manager@ubbee.fr', password: 'password', role: user_entity_1.UserRole.ADMIN_FONCTIONNEL, organization: orgUbbee });
            const ubbeeClient = this.userRepo.create({ name: 'Client Ubbee', email: 'client@ubbee.fr', password: 'password', role: user_entity_1.UserRole.CLIENT, organization: orgUbbee });
            const casaClient = this.userRepo.create({ name: 'Responsable Casa', email: 'client@casa.fr', password: 'password', role: user_entity_1.UserRole.CLIENT, organization: orgCasa });
            await this.userRepo.save([adminUser, managerUser, ubbeeClient, casaClient]);
            const sU1 = this.siteRepo.create({ name: 'Siège Social UBBEE', address: '15 Avenue des Champs-Élysées', city: 'Paris', type: 'Bureaux', organization: orgUbbee, latitude: 48.8708, longitude: 2.3051 });
            const sC1 = this.siteRepo.create({ name: 'Casa Rivoli', address: '12 Rue de Rivoli', city: 'Paris', type: 'Magasin', organization: orgCasa, latitude: 48.8550, longitude: 2.3600 });
            const sC2 = this.siteRepo.create({ name: 'Casa Bordeaux', address: 'Promenade Sainte-Catherine', city: 'Bordeaux', type: 'Magasin', organization: orgCasa, latitude: 44.8385, longitude: -0.5750 });
            const sC3 = this.siteRepo.create({ name: 'Casa Lyon', address: 'Part-Dieu', city: 'Lyon', type: 'Magasin', organization: orgCasa, latitude: 45.7618, longitude: 4.8583 });
            const sL1 = this.siteRepo.create({ name: 'LM Massy', address: 'ZAC du Pérou', city: 'Massy', type: 'Magasin', organization: orgLeroy, latitude: 48.7297, longitude: 2.2783 });
            const sL2 = this.siteRepo.create({ name: 'LM Daumesnil', address: 'Avenue Daumesnil', city: 'Paris', type: 'Magasin', organization: orgLeroy, latitude: 48.8378, longitude: 2.3995 });
            const sL3 = this.siteRepo.create({ name: 'LM Logistique', address: 'Zone Industrielle', city: 'Valence', type: 'Logistique', organization: orgLeroy, latitude: 44.9333, longitude: 4.8917 });
            const sM1 = this.siteRepo.create({ name: 'MDM Nantes', address: 'Atlantis', city: 'Nantes', type: 'Magasin', organization: orgMaison, latitude: 47.2263, longitude: -1.6318 });
            const sM2 = this.siteRepo.create({ name: 'MDM Champs', address: 'Champs-Élysées', city: 'Paris', type: 'Magasin', organization: orgMaison, latitude: 48.8710, longitude: 2.3031 });
            const sM3 = this.siteRepo.create({ name: 'MDM Entrepôt', address: 'Zone Sud', city: 'Marseille', type: 'Logistique', organization: orgMaison, latitude: 43.2965, longitude: 5.3698 });
            await this.siteRepo.save([sU1, sC1, sC2, sC3, sL1, sL2, sL3, sM1, sM2, sM3]);
            const zU1 = this.zoneRepo.create({ name: 'Accueil', type: 'Hall', floor: 'RDC', site: sU1 });
            const zU2 = this.zoneRepo.create({ name: 'Open Space', type: 'Office', floor: 'R+1', site: sU1 });
            const zC1 = this.zoneRepo.create({ name: 'Espace Vente RDC', type: 'Retail', floor: 'RDC', site: sC1 });
            const zC2 = this.zoneRepo.create({ name: 'Stock Arrière', type: 'Storage', floor: 'RDC', site: sC1 });
            const zL1 = this.zoneRepo.create({ name: 'Surface de Vente', type: 'Retail', floor: 'RDC', site: sL1 });
            const zL2 = this.zoneRepo.create({ name: 'Cour des Matériaux', type: 'Retail', floor: 'Extérieur', site: sL1 });
            await this.zoneRepo.save([zU1, zU2, zC1, zC2, zL1, zL2]);
            const s1 = this.sensorRepo.create({ name: 'Thermostat Accueil', type: 'temperature', externalId: 's-temp-01', zone: zU1 });
            const s2 = this.sensorRepo.create({ name: 'CO2 Magasin', type: 'co2', externalId: 's-co2-01', zone: zC1 });
            const s3 = this.sensorRepo.create({ name: 'Compteur Global UBBEE', type: 'energy', externalId: 's-nrg-01', zone: zU1 });
            const s4 = this.sensorRepo.create({ name: 'Sous-compteur CVC UBBEE', type: 'hvac_energy', externalId: 's-hvac-01', zone: zU1 });
            const s5 = this.sensorRepo.create({ name: 'Compteur Global CASA', type: 'energy', externalId: 's-nrg-02', zone: zC1 });
            const s6 = this.sensorRepo.create({ name: 'Sous-compteur CVC CASA', type: 'hvac_energy', externalId: 's-hvac-02', zone: zC1 });
            await this.sensorRepo.save([s1, s2, s3, s4, s5, s6]);
            const g1 = this.gatewayRepo.create({ name: 'GW Centrale UBBEE', serialNumber: 'GW-UB-001', status: 'online', protocol: 'lorawan', ipAddress: '192.168.1.10', site: sU1 });
            const g2 = this.gatewayRepo.create({ name: 'GW Secondaire UBBEE', serialNumber: 'GW-UB-002', status: 'offline', protocol: 'zigbee', ipAddress: '192.168.1.11', site: sU1 });
            const g3 = this.gatewayRepo.create({ name: 'GW Magasin RIVOLI', serialNumber: 'GW-CS-001', status: 'online', protocol: 'lorawan', site: sC1 });
            const g4 = this.gatewayRepo.create({ name: 'GW Magasin RIVOLI 2', serialNumber: 'GW-CS-002', status: 'online', protocol: 'zigbee', site: sC1 });
            const g5 = this.gatewayRepo.create({ name: 'GW Entrepôt M.', serialNumber: 'GW-LM-001', status: 'offline', protocol: 'lorawan', site: sL3 });
            await this.gatewayRepo.save([g1, g2, g3, g4, g5]);
            s1.gateway = g1;
            s2.gateway = g3;
            await this.sensorRepo.save([s1, s2]);
            const a1 = this.alertRepo.create({ message: 'Perte de communication avec capteur', severity: 'CRITICAL', timestamp: new Date(), active: true, sensor: s1 });
            const a2 = this.alertRepo.create({ message: 'Taux CO2 extrêmement élevé (> 1200 ppm)', severity: 'CRITICAL', timestamp: new Date(), active: true, sensor: s2 });
            const a3 = this.alertRepo.create({ message: 'Batterie faible (10%)', severity: 'WARNING', timestamp: new Date(), active: true, sensor: s1 });
            const a4 = this.alertRepo.create({ message: 'Surchauffe détectée CVC', severity: 'WARNING', timestamp: new Date(), active: true, sensor: s4 });
            await this.alertRepo.save([a1, a2, a3, a4]);
            console.log('✅ Database seeded with Multi-Tenant structure!');
        }
        const energyCount = await this.sensorRepo.count({ where: { type: 'energy' } });
        if (energyCount === 0) {
            console.log('⚡ Adding missing Energy Sensor for V4 Dashboard...');
            const orgUbbee = await this.orgRepo.findOne({ where: { name: 'UBBEE' } });
            if (orgUbbee) {
                const site = await this.siteRepo.findOne({ where: { organization: orgUbbee }, relations: ['zones'] });
                if (site && site.zones && site.zones.length > 0) {
                    const sEnergy = this.sensorRepo.create({ name: 'Compteur Général', type: 'energy', externalId: 's-ener-v4', zone: site.zones[0] });
                    const sHvac = this.sensorRepo.create({ name: 'Climatisation/Chauffage', type: 'hvac_energy', externalId: 's-hvac-v4', zone: site.zones[0] });
                    await this.sensorRepo.save([sEnergy, sHvac]);
                    console.log('⚡ Energy Sensor added.');
                }
            }
        }
    }
    getHello() {
        return 'SmartBuild API Operational';
    }
    async getSites(orgId) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const where = orgId && !isGlobalContext ? { organizationId: orgId } : {};
        const sites = await this.siteRepo.find({ where, relations: ['zones', 'zones.sensors', 'gateways', 'organization'] });
        let activeAlertsQuery = this.alertRepo.createQueryBuilder('alert')
            .leftJoinAndSelect('alert.sensor', 'sensor')
            .leftJoinAndSelect('sensor.zone', 'zone')
            .where('alert.active = :active', { active: true });
        if (orgId && !isGlobalContext) {
            activeAlertsQuery = activeAlertsQuery
                .leftJoin('zone.site', 'site')
                .andWhere('site.organizationId = :orgId', { orgId });
        }
        const alerts = await activeAlertsQuery.getMany();
        return sites.map(site => {
            const siteAlerts = alerts.filter(a => site.zones.some(z => z.id === a.sensor?.zone?.id));
            const hasCritical = siteAlerts.some(a => a.severity === 'CRITICAL');
            const hasWarning = siteAlerts.some(a => a.severity === 'WARNING');
            let statusColor = 'green';
            if (hasCritical)
                statusColor = 'red';
            else if (hasWarning)
                statusColor = 'orange';
            return {
                ...site,
                statusColor
            };
        });
    }
    async getOrganizations() {
        const orgs = await this.orgRepo.find({
            relations: ['sites', 'users', 'sites.gateways', 'sites.zones', 'sites.zones.sensors'],
        });
        return orgs.map(org => {
            let devicesCount = 0;
            let gatewaysCount = 0;
            if (org.sites) {
                org.sites.forEach(site => {
                    if (site.gateways) {
                        devicesCount += site.gateways.length;
                        gatewaysCount += site.gateways.length;
                    }
                    if (site.zones) {
                        site.zones.forEach(zone => {
                            if (zone.sensors)
                                devicesCount += zone.sensors.length;
                        });
                    }
                });
            }
            return {
                ...org,
                sitesCount: org.sites ? org.sites.length : 0,
                usersCount: org.users ? org.users.length : 0,
                gatewaysCount,
                devicesCount
            };
        });
    }
    async geocodeAddress(siteData) {
        if (siteData.latitude && siteData.longitude)
            return;
        const queriesToTry = [];
        const countrySuffix = siteData.country ? `, ${siteData.country}` : '';
        if (siteData.address) {
            queriesToTry.push(`${siteData.address}${siteData.postalCode ? ' ' + siteData.postalCode : ''}${siteData.city ? ', ' + siteData.city : ''}${countrySuffix}`);
        }
        if (siteData.postalCode && siteData.city) {
            queriesToTry.push(`${siteData.postalCode} ${siteData.city}${countrySuffix}`);
        }
        if (siteData.city) {
            queriesToTry.push(`${siteData.city}${countrySuffix}`);
        }
        for (const query of queriesToTry) {
            if (!query)
                continue;
            try {
                const encodedQuery = encodeURIComponent(query);
                const response = await fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodedQuery}`, {
                    headers: { 'User-Agent': 'SmartBuildingApp/1.0' }
                });
                const data = await response.json();
                if (data && data.length > 0) {
                    siteData.latitude = parseFloat(data[0].lat);
                    siteData.longitude = parseFloat(data[0].lon);
                    console.log(`Geocoded '${query}' to ${siteData.latitude}, ${siteData.longitude}`);
                    return;
                }
            }
            catch (err) {
                console.error(`Geocoding failed for query '${query}':`, err);
            }
        }
        console.warn(`Could not geocode any of the queries for site: ${siteData.name}`);
    }
    async createOrganization(orgData) {
        const newOrg = this.orgRepo.create(orgData);
        return this.orgRepo.save(newOrg);
    }
    async updateOrganization(id, orgData) {
        await this.orgRepo.update(id, orgData);
        return this.orgRepo.findOne({ where: { id } });
    }
    async deleteOrganization(id) {
        return this.orgRepo.delete(id);
    }
    async createSite(siteData, orgId) {
        const org = await this.orgRepo.findOne({ where: { id: orgId } });
        if (!org)
            throw new Error("Organization not found");
        if (!siteData.latitude || !siteData.longitude) {
            await this.geocodeAddress(siteData);
        }
        const newSite = this.siteRepo.create({
            ...siteData,
            organization: org
        });
        return this.siteRepo.save(newSite);
    }
    async updateSite(id, siteData) {
        if (!siteData.latitude || !siteData.longitude) {
            await this.geocodeAddress(siteData);
        }
        await this.siteRepo.update(id, siteData);
        return this.siteRepo.findOne({ where: { id } });
    }
    async deleteSite(id) {
        return this.siteRepo.delete(id);
    }
    async createZone(zoneData, siteId) {
        const site = await this.siteRepo.findOne({ where: { id: siteId } });
        if (!site)
            throw new Error("Site not found");
        const newZone = this.zoneRepo.create({
            ...zoneData,
            site: site
        });
        return this.zoneRepo.save(newZone);
    }
    async updateZone(id, zoneData) {
        await this.zoneRepo.update(id, zoneData);
        return this.zoneRepo.findOne({ where: { id } });
    }
    async deleteZone(id) {
        return this.zoneRepo.delete(id);
    }
    async getGateways(orgId) {
        const where = orgId ? { site: { organizationId: orgId } } : {};
        return this.gatewayRepo.find({ where, relations: ['site', 'sensors'] });
    }
    async createGateway(gatewayData) {
        let site = null;
        if (gatewayData.siteId) {
            site = await this.siteRepo.findOne({ where: { id: gatewayData.siteId } });
            if (!site)
                throw new Error("Site not found");
        }
        const newGateway = this.gatewayRepo.create({
            ...gatewayData,
            site: site
        });
        return this.gatewayRepo.save(newGateway);
    }
    async getSensors(orgId) {
        const where = orgId ? { zone: { site: { organizationId: orgId } } } : {};
        return this.sensorRepo.find({ where, relations: ['zone', 'zone.site'] });
    }
    async getReadings(limit = 100, orgId) {
        const where = orgId ? { sensor: { zone: { site: { organizationId: orgId } } } } : {};
        return this.readingRepo.find({
            where,
            order: { timestamp: 'DESC' },
            take: limit,
            relations: ['sensor'],
        });
    }
    async getGlobalEnergy(orgId, siteId) {
        const limit = 400;
        const where = { sensor: { type: (0, typeorm_2.In)(['energy', 'hvac_energy']) } };
        if (siteId) {
            where.sensor.zone = { site: { id: siteId } };
        }
        else if (orgId) {
            where.sensor.zone = { site: { organizationId: orgId } };
        }
        const readings = await this.readingRepo.find({
            where,
            order: { timestamp: 'DESC' },
            take: limit,
            relations: ['sensor'],
        });
        readings.reverse();
        const groupedGlobal = new Map();
        const groupedHvac = new Map();
        for (const r of readings) {
            const timeKey = Math.round(r.timestamp.getTime() / 5000) * 5000;
            if (r.sensor.type === 'energy') {
                groupedGlobal.set(timeKey, (groupedGlobal.get(timeKey) || 0) + r.value);
            }
            else if (r.sensor.type === 'hvac_energy') {
                groupedHvac.set(timeKey, (groupedHvac.get(timeKey) || 0) + r.value);
            }
        }
        const allKeys = Array.from(new Set([...groupedGlobal.keys(), ...groupedHvac.keys()])).sort();
        return allKeys.map(time => ({
            timestamp: new Date(time).toISOString(),
            globalValue: groupedGlobal.get(time) || 0,
            hvacValue: groupedHvac.get(time) || 0,
            unit: 'W'
        }));
    }
    async getAverageTemperature(orgId, siteId) {
        const limit = 1000;
        const where = { sensor: { type: 'temperature' } };
        if (siteId) {
            where.sensor.zone = { site: { id: siteId } };
        }
        else if (orgId) {
            where.sensor.zone = { site: { organizationId: orgId } };
        }
        const readings = await this.readingRepo.find({
            where,
            order: { timestamp: 'DESC' },
            take: limit,
            relations: ['sensor', 'sensor.zone'],
        });
        const businessReadings = readings.filter(r => {
            const hour = r.timestamp.getHours();
            return hour >= 8 && hour < 19;
        });
        const grouped = new Map();
        for (const r of businessReadings) {
            const day = r.timestamp.toISOString().split('T')[0];
            const current = grouped.get(day) || { sum: 0, count: 0 };
            grouped.set(day, { sum: current.sum + r.value, count: current.count + 1 });
        }
        const res = Array.from(grouped.entries()).map(([day, data]) => ({
            day,
            averageTemp: Math.round((data.sum / data.count) * 10) / 10
        })).sort((a, b) => a.day.localeCompare(b.day));
        return res;
    }
    async getAlerts(orgId, siteId) {
        const where = { active: true };
        if (siteId) {
            where.sensor = { zone: { site: { id: siteId } } };
        }
        else if (orgId) {
            where.sensor = { zone: { site: { organizationId: orgId } } };
        }
        return this.alertRepo.find({
            where,
            order: { timestamp: 'DESC' },
            relations: ['sensor', 'sensor.zone', 'sensor.zone.site', 'sensor.zone.site.organization'],
        });
    }
    async getHvacPerformance(orgId, siteId) {
        const today = new Date();
        const result = [];
        for (let i = 6; i >= 0; i--) {
            const d = new Date(today);
            d.setDate(d.getDate() - i);
            const dayStr = d.toISOString().split('T')[0];
            const runtime = 6 + (Math.random() * 4);
            const setpoint = 21.0;
            const actual = 19.5 + (Math.random() * 3);
            result.push({
                day: dayStr,
                runtime: Math.round(runtime * 10) / 10,
                setpoint: setpoint,
                actual: Math.round(actual * 10) / 10
            });
        }
        return result;
    }
    async processIotWebhook(webhookData) {
        const { deviceType, externalId, payload } = webhookData;
        if (!deviceType || !externalId || !payload) {
            throw new Error('Missing required fields in webhook payload (deviceType, externalId, payload).');
        }
        const decoded = this.payloadFormatter.decode(deviceType, payload);
        if (!decoded) {
            throw new Error('Failed to decode payload.');
        }
        const sensor = await this.sensorRepo.findOne({
            where: { externalId },
            relations: ['zone', 'zone.site']
        });
        if (!sensor) {
            throw new Error(`Sensor not found with externalId: ${externalId}`);
        }
        let primaryValue = 0;
        if (sensor.type === 'temperature' && decoded.temperature !== undefined)
            primaryValue = decoded.temperature;
        else if (sensor.type === 'humidity' && decoded.humidity !== undefined)
            primaryValue = decoded.humidity;
        else if (sensor.type === 'co2' && decoded.co2 !== undefined)
            primaryValue = decoded.co2;
        else
            primaryValue = decoded.temperature || decoded.co2 || decoded.humidity || 0;
        const reading = this.readingRepo.create({
            value: parseFloat(primaryValue.toFixed(2)),
            timestamp: new Date(),
            sensor: sensor,
        });
        await this.readingRepo.save(reading);
        await this.rulesEngine.evaluate(reading, sensor);
        this.eventsGateway.broadcastDataRefresh(sensor.zone?.site?.id);
        return { success: true, readingId: reading.id, decoded };
    }
    async globalSearch(query, orgId, role) {
        if (!query || query.length < 2)
            return [];
        const searchStr = `%${query}%`;
        const results = [];
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111' && (role === 'SUPER_ADMIN' || role === 'ADMIN_FONCTIONNEL');
        const sitesQuery = this.siteRepo.createQueryBuilder('site')
            .leftJoinAndSelect('site.organization', 'organization')
            .where('(site.name LIKE :search OR site.city LIKE :search)', { search: searchStr });
        if (!isGlobalContext)
            sitesQuery.andWhere('site.organizationId = :orgId', { orgId });
        const sites = await sitesQuery.take(5).getMany();
        sites.forEach(s => results.push({
            id: s.id,
            type: 'site',
            title: s.name,
            subtitle: `Bâtiment • ${s.organization?.name || 'Inconnu'} • ${s.city}`,
            url: `/sites/${s.id}`
        }));
        const zonesQuery = this.zoneRepo.createQueryBuilder('zone')
            .leftJoinAndSelect('zone.site', 'site')
            .where('zone.name LIKE :search', { search: searchStr });
        if (!isGlobalContext)
            zonesQuery.andWhere('site.organizationId = :orgId', { orgId });
        const zones = await zonesQuery.take(5).getMany();
        zones.forEach(z => results.push({
            id: z.id,
            type: 'zone',
            title: z.name,
            subtitle: `Zone • ${z.site.name}`,
            url: `/sites/${z.site.id}`
        }));
        const sensorsQuery = this.sensorRepo.createQueryBuilder('sensor')
            .leftJoinAndSelect('sensor.zone', 'zone')
            .leftJoinAndSelect('zone.site', 'site')
            .where('(sensor.name LIKE :search OR sensor.externalId LIKE :search)', { search: searchStr });
        if (!isGlobalContext)
            sensorsQuery.andWhere('site.organizationId = :orgId', { orgId });
        const sensors = await sensorsQuery.take(5).getMany();
        sensors.forEach(s => results.push({
            id: s.id,
            type: 'sensor',
            title: s.name,
            subtitle: `Capteur ${s.type} • ${s.zone?.site?.name || 'N/A'}`,
            url: s.zone?.site ? `/sites/${s.zone.site.id}` : '#'
        }));
        const gatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
            .leftJoinAndSelect('gateway.site', 'site')
            .where('(gateway.name LIKE :search OR gateway.serialNumber LIKE :search)', { search: searchStr });
        if (!isGlobalContext)
            gatewaysQuery.andWhere('site.organizationId = :orgId', { orgId });
        const gateways = await gatewaysQuery.take(3).getMany();
        gateways.forEach(g => results.push({
            id: g.id,
            type: 'gateway',
            title: g.name,
            subtitle: `Passerelle • ${g.serialNumber}`,
            url: `/network`
        }));
        if (role === 'SUPER_ADMIN' || role === 'ADMIN_FONCTIONNEL') {
            const orgs = await this.orgRepo.createQueryBuilder('org')
                .where('org.name LIKE :search', { search: searchStr })
                .take(3)
                .getMany();
            orgs.forEach(o => results.push({
                id: o.id,
                type: 'organization',
                title: o.name,
                subtitle: `Client B2B`,
                url: `/clients/${o.id}`
            }));
        }
        const usersQuery = this.userRepo.createQueryBuilder('user')
            .leftJoinAndSelect('user.organization', 'org')
            .where('(user.name LIKE :search OR user.email LIKE :search)', { search: searchStr });
        if (!isGlobalContext)
            usersQuery.andWhere('user.organizationId = :orgId', { orgId });
        const users = await usersQuery.take(4).getMany();
        users.forEach(u => results.push({
            id: u.id,
            type: 'user',
            title: u.name,
            subtitle: `Utilisateur • ${u.email}`,
            url: u.organization ? `/clients/${u.organization.id}` : `/clients`
        }));
        return results;
    }
    async getUsers(organizationId) {
        if (organizationId) {
            return this.userRepo.find({ where: { organization: { id: organizationId } } });
        }
        return this.userRepo.find({ relations: ['organization'] });
    }
    async createUser(userData) {
        let org = null;
        if (userData.organizationId) {
            org = await this.orgRepo.findOne({ where: { id: userData.organizationId } });
        }
        const user = this.userRepo.create({ ...userData, organization: org });
        return this.userRepo.save(user);
    }
    async updateUser(id, userData) {
        await this.userRepo.update(id, userData);
        return this.userRepo.findOne({ where: { id } });
    }
    async deleteUser(id) {
        await this.userRepo.delete(id);
        return { success: true };
    }
    async getCustomRoles(organizationId) {
        if (organizationId) {
            return this.customRoleRepo.find({ where: { organization: { id: organizationId } } });
        }
        return this.customRoleRepo.find({ relations: ['organization'] });
    }
    async createCustomRole(roleData) {
        let org = null;
        if (roleData.organizationId) {
            org = await this.orgRepo.findOne({ where: { id: roleData.organizationId } });
        }
        const role = this.customRoleRepo.create({ ...roleData, organization: org });
        return this.customRoleRepo.save(role);
    }
    async updateCustomRole(id, roleData) {
        await this.customRoleRepo.update(id, roleData);
        return this.customRoleRepo.findOne({ where: { id } });
    }
    async deleteCustomRole(id) {
        await this.customRoleRepo.delete(id);
        return { success: true };
    }
    async executeEquipmentAction(payload) {
        console.log(`[ACTION Triggered] Eq: ${payload.equipmentId} | Action: ${payload.action} | Val: ${payload.value}`);
        this.eventsGateway.server.emit('sensor_data', {
            type: 'action_audit',
            equipmentId: payload.equipmentId,
            action: payload.action,
            value: payload.value,
            timestamp: new Date().toISOString()
        });
        return { success: true, message: `Action ${payload.action} command sent successfully.`, details: payload };
    }
    async getDashboardKpis(orgId, role) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111' && (role === 'SUPER_ADMIN' || role === 'ADMIN_FONCTIONNEL');
        const totalClients = isGlobalContext ? await this.orgRepo.count() : 1;
        let sitesQuery = this.siteRepo.createQueryBuilder('site');
        if (!isGlobalContext)
            sitesQuery = sitesQuery.where('site.organizationId = :orgId', { orgId });
        const totalSites = await sitesQuery.getCount();
        let alertsQuery = this.alertRepo.createQueryBuilder('alert')
            .leftJoin('alert.sensor', 'sensor')
            .leftJoin('sensor.zone', 'zone')
            .leftJoin('zone.site', 'site')
            .where('alert.active = :active', { active: true });
        if (!isGlobalContext)
            alertsQuery = alertsQuery.andWhere('site.organizationId = :orgId', { orgId });
        const activeIncidents = await alertsQuery.getCount();
        const criticalAlerts = Math.floor(activeIncidents * 0.3);
        const outOfTargetSitesQuery = this.alertRepo.createQueryBuilder('alert')
            .select('zone.siteId')
            .leftJoin('alert.sensor', 'sensor')
            .leftJoin('sensor.zone', 'zone')
            .leftJoin('zone.site', 'site')
            .where('alert.active = :active', { active: true })
            .groupBy('zone.siteId');
        if (!isGlobalContext)
            outOfTargetSitesQuery.andWhere('site.organizationId = :orgId', { orgId });
        const outOfTargetSitesResult = await outOfTargetSitesQuery.getRawMany();
        const outOfTargetSites = outOfTargetSitesResult.length;
        let zonesQuery = this.zoneRepo.createQueryBuilder('zone')
            .leftJoin('zone.site', 'site');
        if (!isGlobalContext)
            zonesQuery = zonesQuery.where('site.organizationId = :orgId', { orgId });
        const totalZones = await zonesQuery.getCount();
        let sensorsQuery = this.sensorRepo.createQueryBuilder('sensor')
            .leftJoin('sensor.zone', 'zone')
            .leftJoin('zone.site', 'site');
        if (!isGlobalContext)
            sensorsQuery = sensorsQuery.where('site.organizationId = :orgId', { orgId });
        const totalSensors = await sensorsQuery.getCount();
        let usersQuery = this.userRepo.createQueryBuilder('user');
        if (!isGlobalContext)
            usersQuery = usersQuery.where('user.organizationId = :orgId', { orgId });
        const activeUsers = await usersQuery.getCount();
        let gatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
            .leftJoin('gateway.site', 'site');
        if (!isGlobalContext)
            gatewaysQuery = gatewaysQuery.where('site.organizationId = :orgId', { orgId });
        const totalGateways = await gatewaysQuery.getCount();
        let offlineGatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
            .leftJoin('gateway.site', 'site')
            .where('gateway.status = :status', { status: 'offline' });
        if (!isGlobalContext)
            offlineGatewaysQuery = offlineGatewaysQuery.andWhere('site.organizationId = :orgId', { orgId });
        const offlineGateways = await offlineGatewaysQuery.getCount();
        const globalHealthScore = Math.max(0, 100 - activeIncidents * 2 - offlineGateways * 5);
        return {
            totalClients,
            totalSites,
            activeIncidents,
            offlineGateways,
            totalZones,
            totalSensors,
            outOfTargetSites,
            globalHealthScore,
            activeUsers,
            criticalAlerts
        };
    }
};
exports.AppService = AppService;
exports.AppService = AppService = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(site_entity_1.Site)),
    __param(1, (0, typeorm_1.InjectRepository)(zone_entity_1.Zone)),
    __param(2, (0, typeorm_1.InjectRepository)(sensor_entity_1.Sensor)),
    __param(3, (0, typeorm_1.InjectRepository)(reading_entity_1.Reading)),
    __param(4, (0, typeorm_1.InjectRepository)(alert_entity_1.Alert)),
    __param(5, (0, typeorm_1.InjectRepository)(organization_entity_1.Organization)),
    __param(6, (0, typeorm_1.InjectRepository)(user_entity_1.User)),
    __param(7, (0, typeorm_1.InjectRepository)(custom_role_entity_1.CustomRole)),
    __param(8, (0, typeorm_1.InjectRepository)(gateway_entity_1.Gateway)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        typeorm_2.Repository,
        payload_formatter_service_1.PayloadFormatterService,
        rules_engine_service_1.RulesEngineService,
        events_gateway_1.EventsGateway])
], AppService);
//# sourceMappingURL=app.service.js.map
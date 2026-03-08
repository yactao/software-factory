import { Injectable, OnModuleInit } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository, In } from 'typeorm';
import { Site } from './entities/site.entity';
import { Zone } from './entities/zone.entity';
import { Sensor } from './entities/sensor.entity';
import { Reading } from './entities/reading.entity';
import { Alert } from './entities/alert.entity';
import { Organization } from './entities/organization.entity';
import { User, UserRole } from './entities/user.entity';
import { Gateway } from './entities/gateway.entity';
import { CustomRole } from './entities/custom-role.entity';
import { PayloadFormatterService } from './iot/payload-formatter.service';
import { RulesEngineService } from './rules-engine.service';
import { EventsGateway } from './iot/events.gateway';

@Injectable()
export class AppService implements OnModuleInit {
  constructor(
    @InjectRepository(Site)
    private siteRepo: Repository<Site>,
    @InjectRepository(Zone)
    private zoneRepo: Repository<Zone>,
    @InjectRepository(Sensor)
    private sensorRepo: Repository<Sensor>,
    @InjectRepository(Reading)
    private readingRepo: Repository<Reading>,
    @InjectRepository(Alert)
    private alertRepo: Repository<Alert>,
    @InjectRepository(Organization)
    private orgRepo: Repository<Organization>,
    @InjectRepository(User)
    private userRepo: Repository<User>,
    @InjectRepository(CustomRole)
    private customRoleRepo: Repository<CustomRole>,
    @InjectRepository(Gateway)
    private gatewayRepo: Repository<Gateway>,
    private payloadFormatter: PayloadFormatterService,
    private rulesEngine: RulesEngineService,
    private eventsGateway: EventsGateway,
  ) { }

  async checkHealth() {
    try {
      // Basic query to verify the database connection is alive
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
    } catch (error) {
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

      // 1. Create Organizations with fixed UUIDs for Frontend Demo Switcher
      const org1Id = '11111111-1111-1111-1111-111111111111';
      const org2Id = '22222222-2222-2222-2222-222222222222'; // CASA
      const org3Id = '33333333-3333-3333-3333-333333333333'; // Leroy Merlin
      const org4Id = '44444444-4444-4444-4444-444444444444'; // Maison du Monde

      await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org1Id}', 'UBBEE', 'SaaS Provider')`);
      await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org2Id}', 'CASA', 'Retail')`);
      await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org3Id}', 'Leroy Merlin', 'Retail/Bricolage')`);
      await this.orgRepo.query(`INSERT INTO "organizations" ("id", "name", "type") VALUES ('${org4Id}', 'Maison du Monde', 'Retail')`);

      const orgUbbee = (await this.orgRepo.findOne({ where: { id: org1Id } }))!;
      const orgCasa = (await this.orgRepo.findOne({ where: { id: org2Id } }))!;
      const orgLeroy = (await this.orgRepo.findOne({ where: { id: org3Id } }))!;
      const orgMaison = (await this.orgRepo.findOne({ where: { id: org4Id } }))!;

      // 2. Create Default Users
      const adminUser = this.userRepo.create({ name: 'Super Admin', email: 'admin@ubbee.fr', password: 'admin', role: UserRole.SUPER_ADMIN, organization: orgUbbee });
      const managerUser = this.userRepo.create({ name: 'Energy Manager', email: 'manager@ubbee.fr', password: 'password', role: UserRole.ADMIN_FONCTIONNEL, organization: orgUbbee });
      const ubbeeClient = this.userRepo.create({ name: 'Client Ubbee', email: 'client@ubbee.fr', password: 'password', role: UserRole.CLIENT, organization: orgUbbee });
      const casaClient = this.userRepo.create({ name: 'Responsable Casa', email: 'client@casa.fr', password: 'password', role: UserRole.CLIENT, organization: orgCasa });
      await this.userRepo.save([adminUser, managerUser, ubbeeClient, casaClient]);

      // 3. Create Sites and assign to Organizations
      // UBBEE
      const sU1 = this.siteRepo.create({ name: 'Siège Social UBBEE', address: '15 Avenue des Champs-Élysées', city: 'Paris', type: 'Bureaux', organization: orgUbbee, latitude: 48.8708, longitude: 2.3051 });

      // CASA
      const sC1 = this.siteRepo.create({ name: 'Casa Rivoli', address: '12 Rue de Rivoli', city: 'Paris', type: 'Magasin', organization: orgCasa, latitude: 48.8550, longitude: 2.3600 });
      const sC2 = this.siteRepo.create({ name: 'Casa Bordeaux', address: 'Promenade Sainte-Catherine', city: 'Bordeaux', type: 'Magasin', organization: orgCasa, latitude: 44.8385, longitude: -0.5750 });
      const sC3 = this.siteRepo.create({ name: 'Casa Lyon', address: 'Part-Dieu', city: 'Lyon', type: 'Magasin', organization: orgCasa, latitude: 45.7618, longitude: 4.8583 });

      // Leroy Merlin
      const sL1 = this.siteRepo.create({ name: 'LM Massy', address: 'ZAC du Pérou', city: 'Massy', type: 'Magasin', organization: orgLeroy, latitude: 48.7297, longitude: 2.2783 });
      const sL2 = this.siteRepo.create({ name: 'LM Daumesnil', address: 'Avenue Daumesnil', city: 'Paris', type: 'Magasin', organization: orgLeroy, latitude: 48.8378, longitude: 2.3995 });
      const sL3 = this.siteRepo.create({ name: 'LM Logistique', address: 'Zone Industrielle', city: 'Valence', type: 'Logistique', organization: orgLeroy, latitude: 44.9333, longitude: 4.8917 });

      // Maison du Monde
      const sM1 = this.siteRepo.create({ name: 'MDM Nantes', address: 'Atlantis', city: 'Nantes', type: 'Magasin', organization: orgMaison, latitude: 47.2263, longitude: -1.6318 });
      const sM2 = this.siteRepo.create({ name: 'MDM Champs', address: 'Champs-Élysées', city: 'Paris', type: 'Magasin', organization: orgMaison, latitude: 48.8710, longitude: 2.3031 });
      const sM3 = this.siteRepo.create({ name: 'MDM Entrepôt', address: 'Zone Sud', city: 'Marseille', type: 'Logistique', organization: orgMaison, latitude: 43.2965, longitude: 5.3698 });

      await this.siteRepo.save([sU1, sC1, sC2, sC3, sL1, sL2, sL3, sM1, sM2, sM3]);

      // 4. Zones for Sites
      // UBBEE Zones
      const zU1 = this.zoneRepo.create({ name: 'Accueil', type: 'Hall', floor: 'RDC', site: sU1 });
      const zU2 = this.zoneRepo.create({ name: 'Open Space', type: 'Office', floor: 'R+1', site: sU1 });

      // CASA Zones
      const zC1 = this.zoneRepo.create({ name: 'Espace Vente RDC', type: 'Retail', floor: 'RDC', site: sC1 });
      const zC2 = this.zoneRepo.create({ name: 'Stock Arrière', type: 'Storage', floor: 'RDC', site: sC1 });

      // Leroy Merlin Zones
      const zL1 = this.zoneRepo.create({ name: 'Surface de Vente', type: 'Retail', floor: 'RDC', site: sL1 });
      const zL2 = this.zoneRepo.create({ name: 'Cour des Matériaux', type: 'Retail', floor: 'Extérieur', site: sL1 });

      await this.zoneRepo.save([zU1, zU2, zC1, zC2, zL1, zL2]);

      // 5. Sensors (minimal)
      const s1 = this.sensorRepo.create({ name: 'Thermostat Accueil', type: 'temperature', externalId: 's-temp-01', zone: zU1 });
      const s2 = this.sensorRepo.create({ name: 'CO2 Magasin', type: 'co2', externalId: 's-co2-01', zone: zC1 });

      // Energy sensors required for correlation charts
      const s3 = this.sensorRepo.create({ name: 'Compteur Global UBBEE', type: 'energy', externalId: 's-nrg-01', zone: zU1 });
      const s4 = this.sensorRepo.create({ name: 'Sous-compteur CVC UBBEE', type: 'hvac_energy', externalId: 's-hvac-01', zone: zU1 });
      const s5 = this.sensorRepo.create({ name: 'Compteur Global CASA', type: 'energy', externalId: 's-nrg-02', zone: zC1 });
      const s6 = this.sensorRepo.create({ name: 'Sous-compteur CVC CASA', type: 'hvac_energy', externalId: 's-hvac-02', zone: zC1 });

      await this.sensorRepo.save([s1, s2, s3, s4, s5, s6]);

      // 6. Gateways
      const g1 = this.gatewayRepo.create({ name: 'GW Centrale UBBEE', serialNumber: 'GW-UB-001', status: 'online', protocol: 'lorawan', ipAddress: '192.168.1.10', site: sU1 });
      const g2 = this.gatewayRepo.create({ name: 'GW Secondaire UBBEE', serialNumber: 'GW-UB-002', status: 'offline', protocol: 'zigbee', ipAddress: '192.168.1.11', site: sU1 });
      const g3 = this.gatewayRepo.create({ name: 'GW Magasin RIVOLI', serialNumber: 'GW-CS-001', status: 'online', protocol: 'lorawan', site: sC1 });
      const g4 = this.gatewayRepo.create({ name: 'GW Magasin RIVOLI 2', serialNumber: 'GW-CS-002', status: 'online', protocol: 'zigbee', site: sC1 });
      const g5 = this.gatewayRepo.create({ name: 'GW Entrepôt M.', serialNumber: 'GW-LM-001', status: 'offline', protocol: 'lorawan', site: sL3 });

      await this.gatewayRepo.save([g1, g2, g3, g4, g5]);

      s1.gateway = g1;
      s2.gateway = g3;
      await this.sensorRepo.save([s1, s2]);

      // 7. Seed Alerts (Défaut Parc)
      const a1 = this.alertRepo.create({ message: 'Perte de communication avec capteur', severity: 'CRITICAL', timestamp: new Date(), active: true, sensor: s1 });
      const a2 = this.alertRepo.create({ message: 'Taux CO2 extrêmement élevé (> 1200 ppm)', severity: 'CRITICAL', timestamp: new Date(), active: true, sensor: s2 });
      const a3 = this.alertRepo.create({ message: 'Batterie faible (10%)', severity: 'WARNING', timestamp: new Date(), active: true, sensor: s1 });
      const a4 = this.alertRepo.create({ message: 'Surchauffe détectée CVC', severity: 'WARNING', timestamp: new Date(), active: true, sensor: s4 });

      await this.alertRepo.save([a1, a2, a3, a4]);

      console.log('✅ Database seeded with Multi-Tenant structure!');
    }

    // Ensure Energy Sensor Exists for V4 Dashboard
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

  getHello(): string {
    return 'SmartBuild API Operational';
  }

  async getSites(orgId?: string) {
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
      if (hasCritical) statusColor = 'red';
      else if (hasWarning) statusColor = 'orange';

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

    // Remap pour inclure les compteurs pour le front-end
    return orgs.map(org => {
      // Calcul du nombred 'équipements (devicesCount)
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
              if (zone.sensors) devicesCount += zone.sensors.length;
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

  private async geocodeAddress(siteData: any) {
    if (siteData.latitude && siteData.longitude) return;

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
      if (!query) continue;
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
          return; // Success, stop trying other queries
        }
      } catch (err) {
        console.error(`Geocoding failed for query '${query}':`, err);
      }
    }
    console.warn(`Could not geocode any of the queries for site: ${siteData.name}`);
  }

  async createOrganization(orgData: any) {
    const newOrg = this.orgRepo.create(orgData);
    return this.orgRepo.save(newOrg);
  }

  async updateOrganization(id: string, orgData: any) {
    await this.orgRepo.update(id, orgData);
    return this.orgRepo.findOne({ where: { id } });
  }

  async deleteOrganization(id: string) {
    return this.orgRepo.delete(id);
  }

  async createSite(siteData: any, orgId: string) {
    const org = await this.orgRepo.findOne({ where: { id: orgId } });
    if (!org) throw new Error("Organization not found");

    if (!siteData.latitude || !siteData.longitude) {
      await this.geocodeAddress(siteData);
    }

    const newSite = this.siteRepo.create({
      ...siteData,
      organization: org
    });
    return this.siteRepo.save(newSite);
  }

  async updateSite(id: string, siteData: any) {
    if (!siteData.latitude || !siteData.longitude) {
      await this.geocodeAddress(siteData);
    }

    await this.siteRepo.update(id, siteData);
    return this.siteRepo.findOne({ where: { id } });
  }

  async deleteSite(id: string) {
    return this.siteRepo.delete(id);
  }

  async createZone(zoneData: any, siteId: string) {
    const site = await this.siteRepo.findOne({ where: { id: siteId } });
    if (!site) throw new Error("Site not found");

    const newZone = this.zoneRepo.create({
      ...zoneData,
      site: site
    });
    return this.zoneRepo.save(newZone);
  }

  async updateZone(id: string, zoneData: any) {
    await this.zoneRepo.update(id, zoneData);
    return this.zoneRepo.findOne({ where: { id } });
  }

  async deleteZone(id: string) {
    return this.zoneRepo.delete(id);
  }

  async getGateways(orgId?: string) {
    const where = orgId ? { site: { organizationId: orgId } } : {};
    return this.gatewayRepo.find({ where, relations: ['site', 'sensors'] });
  }

  async createGateway(gatewayData: any) {
    let site = null;
    if (gatewayData.siteId) {
      site = await this.siteRepo.findOne({ where: { id: gatewayData.siteId } });
      if (!site) throw new Error("Site not found");
    }

    const newGateway = this.gatewayRepo.create({
      ...gatewayData,
      site: site
    });
    return this.gatewayRepo.save(newGateway);
  }


  async getSensors(orgId?: string) {
    const where = orgId ? { zone: { site: { organizationId: orgId } } } : {};
    return this.sensorRepo.find({ where, relations: ['zone', 'zone.site'] });
  }

  async getReadings(limit: number = 100, orgId?: string) {
    const where = orgId ? { sensor: { zone: { site: { organizationId: orgId } } } } : {};
    return this.readingRepo.find({
      where,
      order: { timestamp: 'DESC' },
      take: limit,
      relations: ['sensor'],
    });
  }

  async getGlobalEnergy(orgId?: string, siteId?: string) {
    const limit = 400; // double limit to handle two types of sensors
    const where: any = { sensor: { type: In(['energy', 'hvac_energy']) } };

    if (siteId) {
      where.sensor.zone = { site: { id: siteId } };
    } else if (orgId) {
      where.sensor.zone = { site: { organizationId: orgId } };
    }
    const readings = await this.readingRepo.find({
      where,
      order: { timestamp: 'DESC' },
      take: limit,
      relations: ['sensor'],
    });

    // We want chronologically ascending for charts
    readings.reverse();

    const groupedGlobal = new Map<number, number>();
    const groupedHvac = new Map<number, number>();

    for (const r of readings) {
      // Group by 5s windows
      const timeKey = Math.round(r.timestamp.getTime() / 5000) * 5000;
      if (r.sensor.type === 'energy') {
        groupedGlobal.set(timeKey, (groupedGlobal.get(timeKey) || 0) + r.value);
      } else if (r.sensor.type === 'hvac_energy') {
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

  async getAverageTemperature(orgId?: string, siteId?: string) {
    const limit = 1000;
    const where: any = { sensor: { type: 'temperature' } };
    if (siteId) {
      where.sensor.zone = { site: { id: siteId } };
    } else if (orgId) {
      where.sensor.zone = { site: { organizationId: orgId } };
    }

    // Fetch recent readings
    const readings = await this.readingRepo.find({
      where,
      order: { timestamp: 'DESC' },
      take: limit,
      relations: ['sensor', 'sensor.zone'],
    });

    // Filter by business hours (e.g., 8:00 to 19:00)
    const businessReadings = readings.filter(r => {
      const hour = r.timestamp.getHours();
      return hour >= 8 && hour < 19;
    });

    // Group by day 
    const grouped = new Map<string, { sum: number, count: number }>();
    for (const r of businessReadings) {
      const day = r.timestamp.toISOString().split('T')[0]; // YYYY-MM-DD
      const current = grouped.get(day) || { sum: 0, count: 0 };
      grouped.set(day, { sum: current.sum + r.value, count: current.count + 1 });
    }

    const res = Array.from(grouped.entries()).map(([day, data]) => ({
      day,
      averageTemp: Math.round((data.sum / data.count) * 10) / 10
    })).sort((a, b) => a.day.localeCompare(b.day));

    return res;
  }

  async getAlerts(orgId?: string, siteId?: string) {
    const where: any = { active: true };
    if (siteId) {
      where.sensor = { zone: { site: { id: siteId } } };
    } else if (orgId) {
      where.sensor = { zone: { site: { organizationId: orgId } } };
    }
    return this.alertRepo.find({
      where,
      order: { timestamp: 'DESC' },
      relations: ['sensor', 'sensor.zone', 'sensor.zone.site', 'sensor.zone.site.organization'],
    });
  }

  async getHvacPerformance(orgId?: string, siteId?: string) {
    // Mock simulation for HVAC runtime vs Setpoint for the last 7 days since we don't have real thermostat runtime logs yet
    const today = new Date();
    const result = [];
    for (let i = 6; i >= 0; i--) {
      const d = new Date(today);
      d.setDate(d.getDate() - i);
      const dayStr = d.toISOString().split('T')[0];

      // Add some random variation
      const runtime = 6 + (Math.random() * 4); // Between 6 and 10 hours
      const setpoint = 21.0;
      const actual = 19.5 + (Math.random() * 3); // Between 19.5 and 22.5

      result.push({
        day: dayStr,
        runtime: Math.round(runtime * 10) / 10,
        setpoint: setpoint,
        actual: Math.round(actual * 10) / 10
      });
    }
    return result;
  }

  // IoT Webhook processing
  async processIotWebhook(webhookData: any) {
    const { deviceType, externalId, payload } = webhookData;

    if (!deviceType || !externalId || !payload) {
      throw new Error('Missing required fields in webhook payload (deviceType, externalId, payload).');
    }

    // Decode the raw payload
    const decoded = this.payloadFormatter.decode(deviceType, payload);

    if (!decoded) {
      throw new Error('Failed to decode payload.');
    }

    // Find the sensor
    const sensor = await this.sensorRepo.findOne({
      where: { externalId },
      relations: ['zone', 'zone.site']
    });

    if (!sensor) {
      // In a real system, we might auto-provision it. Here we just reject.
      throw new Error(`Sensor not found with externalId: ${externalId}`);
    }

    // Determine the primary value based on the sensor type
    let primaryValue = 0;
    if (sensor.type === 'temperature' && decoded.temperature !== undefined) primaryValue = decoded.temperature;
    else if (sensor.type === 'humidity' && decoded.humidity !== undefined) primaryValue = decoded.humidity;
    else if (sensor.type === 'co2' && decoded.co2 !== undefined) primaryValue = decoded.co2;
    // fallback or generic reading logic
    else primaryValue = decoded.temperature || decoded.co2 || decoded.humidity || 0;

    const reading = this.readingRepo.create({
      value: parseFloat(primaryValue.toFixed(2)),
      timestamp: new Date(),
      sensor: sensor,
      // could also store the full `decoded` object if we added a JSON column to Reading
    });

    await this.readingRepo.save(reading);

    // Evaluate rules on new reading
    await this.rulesEngine.evaluate(reading, sensor);

    this.eventsGateway.broadcastDataRefresh(sensor.zone?.site?.id);

    return { success: true, readingId: reading.id, decoded };
  }

  async globalSearch(query: string, orgId: string, role: string) {
    if (!query || query.length < 2) return [];

    const searchStr = `%${query}%`;
    const results: any[] = [];
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111' && (role === 'SUPER_ADMIN' || role === 'ADMIN_FONCTIONNEL');

    // 1. Search Sites
    const sitesQuery = this.siteRepo.createQueryBuilder('site')
      .leftJoinAndSelect('site.organization', 'organization')
      .where('(site.name LIKE :search OR site.city LIKE :search)', { search: searchStr });
    if (!isGlobalContext) sitesQuery.andWhere('site.organizationId = :orgId', { orgId });
    const sites = await sitesQuery.take(5).getMany();

    sites.forEach(s => results.push({
      id: s.id,
      type: 'site',
      title: s.name,
      subtitle: `Bâtiment • ${s.organization?.name || 'Inconnu'} • ${s.city}`,
      url: `/sites/${s.id}`
    }));

    // 2. Search Zones
    const zonesQuery = this.zoneRepo.createQueryBuilder('zone')
      .leftJoinAndSelect('zone.site', 'site')
      .where('zone.name LIKE :search', { search: searchStr });
    if (!isGlobalContext) zonesQuery.andWhere('site.organizationId = :orgId', { orgId });
    const zones = await zonesQuery.take(5).getMany();

    zones.forEach(z => results.push({
      id: z.id,
      type: 'zone',
      title: z.name,
      subtitle: `Zone • ${z.site.name}`,
      url: `/sites/${z.site.id}` // Navigue vers le site parent
    }));

    // 3. Search Sensors
    const sensorsQuery = this.sensorRepo.createQueryBuilder('sensor')
      .leftJoinAndSelect('sensor.zone', 'zone')
      .leftJoinAndSelect('zone.site', 'site')
      .where('(sensor.name LIKE :search OR sensor.externalId LIKE :search)', { search: searchStr });
    if (!isGlobalContext) sensorsQuery.andWhere('site.organizationId = :orgId', { orgId });
    const sensors = await sensorsQuery.take(5).getMany();

    sensors.forEach(s => results.push({
      id: s.id,
      type: 'sensor',
      title: s.name,
      subtitle: `Capteur ${s.type} • ${s.zone?.site?.name || 'N/A'}`,
      url: s.zone?.site ? `/sites/${s.zone.site.id}` : '#'
    }));

    // 4. Search Gateways
    const gatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
      .leftJoinAndSelect('gateway.site', 'site')
      .where('(gateway.name LIKE :search OR gateway.serialNumber LIKE :search)', { search: searchStr });
    if (!isGlobalContext) gatewaysQuery.andWhere('site.organizationId = :orgId', { orgId });
    const gateways = await gatewaysQuery.take(3).getMany();

    gateways.forEach(g => results.push({
      id: g.id,
      type: 'gateway',
      title: g.name,
      subtitle: `Passerelle • ${g.serialNumber}`,
      url: `/network`
    }));

    // 5. Search Organizations (Admins only)
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

    // 6. Search Users
    const usersQuery = this.userRepo.createQueryBuilder('user')
      .leftJoinAndSelect('user.organization', 'org')
      .where('(user.name LIKE :search OR user.email LIKE :search)', { search: searchStr });
    if (!isGlobalContext) usersQuery.andWhere('user.organizationId = :orgId', { orgId });
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

  async getUsers(organizationId?: string) {
    if (organizationId) {
      return this.userRepo.find({ where: { organization: { id: organizationId } } });
    }
    return this.userRepo.find({ relations: ['organization'] });
  }

  async createUser(userData: any) {
    let org = null;
    if (userData.organizationId) {
      org = await this.orgRepo.findOne({ where: { id: userData.organizationId } });
    }
    const user = this.userRepo.create({ ...userData, organization: org });
    return this.userRepo.save(user);
  }

  async updateUser(id: string, userData: any) {
    await this.userRepo.update(id, userData);
    return this.userRepo.findOne({ where: { id } });
  }

  async deleteUser(id: string) {
    await this.userRepo.delete(id);
    return { success: true };
  }

  async getCustomRoles(organizationId?: string) {
    if (organizationId) {
      return this.customRoleRepo.find({ where: { organization: { id: organizationId } } });
    }
    return this.customRoleRepo.find({ relations: ['organization'] });
  }

  async createCustomRole(roleData: any) {
    let org = null;
    if (roleData.organizationId) {
      org = await this.orgRepo.findOne({ where: { id: roleData.organizationId } });
    }
    const role = this.customRoleRepo.create({ ...roleData, organization: org });
    return this.customRoleRepo.save(role);
  }

  async updateCustomRole(id: string, roleData: any) {
    await this.customRoleRepo.update(id, roleData);
    return this.customRoleRepo.findOne({ where: { id } });
  }

  async deleteCustomRole(id: string) {
    await this.customRoleRepo.delete(id);
    return { success: true };
  }
  async executeEquipmentAction(payload: { equipmentId: string; action: string; value?: any }) {
    // In a real scenario, this would lookup the equipment by ID and publish an MQTT payload
    // to the actual physical device. For this demo, we'll just log and mock success.
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

  async getDashboardKpis(orgId: string, role: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111' && (role === 'SUPER_ADMIN' || role === 'ADMIN_FONCTIONNEL');

    const totalClients = isGlobalContext ? await this.orgRepo.count() : 1;

    let sitesQuery = this.siteRepo.createQueryBuilder('site');
    if (!isGlobalContext) sitesQuery = sitesQuery.where('site.organizationId = :orgId', { orgId });
    const totalSites = await sitesQuery.getCount();

    let alertsQuery = this.alertRepo.createQueryBuilder('alert')
      .leftJoin('alert.sensor', 'sensor')
      .leftJoin('sensor.zone', 'zone')
      .leftJoin('zone.site', 'site')
      .where('alert.active = :active', { active: true });
    if (!isGlobalContext) alertsQuery = alertsQuery.andWhere('site.organizationId = :orgId', { orgId });

    const activeIncidents = await alertsQuery.getCount();
    const criticalAlerts = Math.floor(activeIncidents * 0.3); // Mocking 30% are critical for now 

    // Find sites with active incidents (mocking "out of target" using sites with incidents)
    const outOfTargetSitesQuery = this.alertRepo.createQueryBuilder('alert')
      .select('zone.siteId')
      .leftJoin('alert.sensor', 'sensor')
      .leftJoin('sensor.zone', 'zone')
      .leftJoin('zone.site', 'site')
      .where('alert.active = :active', { active: true })
      .groupBy('zone.siteId');
    if (!isGlobalContext) outOfTargetSitesQuery.andWhere('site.organizationId = :orgId', { orgId });

    const outOfTargetSitesResult = await outOfTargetSitesQuery.getRawMany();
    const outOfTargetSites = outOfTargetSitesResult.length;

    let zonesQuery = this.zoneRepo.createQueryBuilder('zone')
      .leftJoin('zone.site', 'site');
    if (!isGlobalContext) zonesQuery = zonesQuery.where('site.organizationId = :orgId', { orgId });
    const totalZones = await zonesQuery.getCount();

    let sensorsQuery = this.sensorRepo.createQueryBuilder('sensor')
      .leftJoin('sensor.zone', 'zone')
      .leftJoin('zone.site', 'site');
    if (!isGlobalContext) sensorsQuery = sensorsQuery.where('site.organizationId = :orgId', { orgId });
    const totalSensors = await sensorsQuery.getCount();

    let usersQuery = this.userRepo.createQueryBuilder('user');
    if (!isGlobalContext) usersQuery = usersQuery.where('user.organizationId = :orgId', { orgId });
    const activeUsers = await usersQuery.getCount();

    let gatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
      .leftJoin('gateway.site', 'site');
    if (!isGlobalContext) gatewaysQuery = gatewaysQuery.where('site.organizationId = :orgId', { orgId });
    const totalGateways = await gatewaysQuery.getCount();

    let offlineGatewaysQuery = this.gatewayRepo.createQueryBuilder('gateway')
      .leftJoin('gateway.site', 'site')
      .where('gateway.status = :status', { status: 'offline' });
    if (!isGlobalContext) offlineGatewaysQuery = offlineGatewaysQuery.andWhere('site.organizationId = :orgId', { orgId });
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
}


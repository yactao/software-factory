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
exports.SimulationService = void 0;
const common_1 = require("@nestjs/common");
const typeorm_1 = require("@nestjs/typeorm");
const typeorm_2 = require("typeorm");
const sensor_entity_1 = require("./entities/sensor.entity");
const reading_entity_1 = require("./entities/reading.entity");
const rules_engine_service_1 = require("./rules-engine.service");
const events_gateway_1 = require("./iot/events.gateway");
let SimulationService = class SimulationService {
    sensorRepo;
    readingRepo;
    rulesEngine;
    eventsGateway;
    intervalId;
    constructor(sensorRepo, readingRepo, rulesEngine, eventsGateway) {
        this.sensorRepo = sensorRepo;
        this.readingRepo = readingRepo;
        this.rulesEngine = rulesEngine;
        this.eventsGateway = eventsGateway;
    }
    onModuleInit() {
        console.log('🚀 Starting Internal Simulation Service...');
        this.startSimulation();
    }
    startSimulation() {
        this.intervalId = setInterval(async () => {
            const allSensors = await this.sensorRepo.find({ relations: ['zone', 'zone.site'] });
            const sensors = allSensors.filter(sensor => {
                const siteName = sensor.zone?.site?.name?.toLowerCase() || '';
                return !siteName.includes('projet y') && !siteName.includes('batiment y');
            });
            if (sensors.length === 0) {
                console.warn('⚠️ No sensors found to simulate data for.');
                return;
            }
            for (const sensor of sensors) {
                const value = this.generateFakeValue(sensor);
                const reading = this.readingRepo.create({
                    value: parseFloat(value.toFixed(2)),
                    timestamp: new Date(),
                    sensor: sensor,
                });
                await this.readingRepo.save(reading);
                await this.rulesEngine.evaluate(reading, sensor);
            }
            this.eventsGateway.broadcastDataRefresh();
        }, 5000);
    }
    generateFakeValue(sensor) {
        const now = Date.now();
        let offset = 0;
        let scale = 1;
        if (sensor.zone && sensor.zone.site) {
            const siteName = sensor.zone.site.name;
            let hash = 0;
            for (let i = 0; i < siteName.length; i++) {
                hash = siteName.charCodeAt(i) + ((hash << 5) - hash);
            }
            offset = hash % 100;
            scale = 1 + (Math.abs(hash % 50) / 100);
        }
        let sensorHash = sensor.name ? sensor.name.charCodeAt(0) : 0;
        const timeOffset = (offset * 1000) + (sensorHash * 100);
        switch (sensor.type) {
            case 'temperature':
                const baseTemp = 18 + (offset % 5);
                return baseTemp + Math.sin((now + timeOffset) / 10000) * 4 * scale;
            case 'humidity':
                const baseHum = 45 + (Math.abs(offset) % 20);
                return baseHum + Math.cos((now + timeOffset) / 15000) * 15;
            case 'co2':
                const baseCo2 = 400 + Math.abs(offset % 400);
                return baseCo2 + (Math.random() * 50 * scale);
            case 'energy':
                const baseEnergy = 200 + Math.abs(offset * 25);
                return (baseEnergy + Math.random() * 500) * scale;
            case 'hvac_energy':
                const baseHvac = 100 + Math.abs(offset * 15);
                return (baseHvac + Math.random() * 300) * scale;
            default:
                return Math.random() * 100;
        }
    }
};
exports.SimulationService = SimulationService;
exports.SimulationService = SimulationService = __decorate([
    (0, common_1.Injectable)(),
    __param(0, (0, typeorm_1.InjectRepository)(sensor_entity_1.Sensor)),
    __param(1, (0, typeorm_1.InjectRepository)(reading_entity_1.Reading)),
    __metadata("design:paramtypes", [typeorm_2.Repository,
        typeorm_2.Repository,
        rules_engine_service_1.RulesEngineService,
        events_gateway_1.EventsGateway])
], SimulationService);
//# sourceMappingURL=simulation.service.js.map
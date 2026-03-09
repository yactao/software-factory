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
Object.defineProperty(exports, "__esModule", { value: true });
exports.Sensor = void 0;
const typeorm_1 = require("typeorm");
const zone_entity_1 = require("./zone.entity");
const reading_entity_1 = require("./reading.entity");
const gateway_entity_1 = require("./gateway.entity");
let Sensor = class Sensor {
    id;
    externalId;
    name;
    type;
    unit;
    zone;
    readings;
    gateway;
    deletedAt;
};
exports.Sensor = Sensor;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], Sensor.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ unique: true }),
    __metadata("design:type", String)
], Sensor.prototype, "externalId", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Sensor.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Sensor.prototype, "type", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Sensor.prototype, "unit", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => zone_entity_1.Zone, (zone) => zone.sensors),
    __metadata("design:type", zone_entity_1.Zone)
], Sensor.prototype, "zone", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => reading_entity_1.Reading, (reading) => reading.sensor),
    __metadata("design:type", Array)
], Sensor.prototype, "readings", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => gateway_entity_1.Gateway, gateway => gateway.sensors, { nullable: true }),
    __metadata("design:type", gateway_entity_1.Gateway)
], Sensor.prototype, "gateway", void 0);
__decorate([
    (0, typeorm_1.DeleteDateColumn)(),
    __metadata("design:type", Date)
], Sensor.prototype, "deletedAt", void 0);
exports.Sensor = Sensor = __decorate([
    (0, typeorm_1.Entity)()
], Sensor);
//# sourceMappingURL=sensor.entity.js.map
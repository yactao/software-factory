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
exports.Gateway = void 0;
const typeorm_1 = require("typeorm");
const site_entity_1 = require("./site.entity");
const sensor_entity_1 = require("./sensor.entity");
let Gateway = class Gateway {
    id;
    serialNumber;
    name;
    status;
    ipAddress;
    protocol;
    createdAt;
    site;
    sensors;
    deletedAt;
};
exports.Gateway = Gateway;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], Gateway.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)({ unique: true }),
    __metadata("design:type", String)
], Gateway.prototype, "serialNumber", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Gateway.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)({ default: 'online' }),
    __metadata("design:type", String)
], Gateway.prototype, "status", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Gateway.prototype, "ipAddress", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Gateway.prototype, "protocol", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)(),
    __metadata("design:type", Date)
], Gateway.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => site_entity_1.Site, site => site.gateways, { onDelete: 'CASCADE' }),
    __metadata("design:type", site_entity_1.Site)
], Gateway.prototype, "site", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => sensor_entity_1.Sensor, sensor => sensor.gateway),
    __metadata("design:type", Array)
], Gateway.prototype, "sensors", void 0);
__decorate([
    (0, typeorm_1.DeleteDateColumn)(),
    __metadata("design:type", Date)
], Gateway.prototype, "deletedAt", void 0);
exports.Gateway = Gateway = __decorate([
    (0, typeorm_1.Entity)()
], Gateway);
//# sourceMappingURL=gateway.entity.js.map
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
exports.Zone = void 0;
const typeorm_1 = require("typeorm");
const site_entity_1 = require("./site.entity");
const sensor_entity_1 = require("./sensor.entity");
let Zone = class Zone {
    id;
    name;
    type;
    floor;
    site;
    sensors;
    deletedAt;
};
exports.Zone = Zone;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], Zone.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Zone.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Zone.prototype, "type", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Zone.prototype, "floor", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => site_entity_1.Site, (site) => site.zones),
    __metadata("design:type", site_entity_1.Site)
], Zone.prototype, "site", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => sensor_entity_1.Sensor, (sensor) => sensor.zone),
    __metadata("design:type", Array)
], Zone.prototype, "sensors", void 0);
__decorate([
    (0, typeorm_1.DeleteDateColumn)(),
    __metadata("design:type", Date)
], Zone.prototype, "deletedAt", void 0);
exports.Zone = Zone = __decorate([
    (0, typeorm_1.Entity)()
], Zone);
//# sourceMappingURL=zone.entity.js.map
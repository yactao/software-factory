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
exports.Site = void 0;
const typeorm_1 = require("typeorm");
const zone_entity_1 = require("./zone.entity");
const organization_entity_1 = require("./organization.entity");
const gateway_entity_1 = require("./gateway.entity");
let Site = class Site {
    id;
    name;
    type;
    address;
    city;
    postalCode;
    country;
    latitude;
    longitude;
    zones;
    organization;
    organizationId;
    gateways;
};
exports.Site = Site;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], Site.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Site.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Site.prototype, "type", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Site.prototype, "address", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Site.prototype, "city", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Site.prototype, "postalCode", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Site.prototype, "country", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 6, nullable: true }),
    __metadata("design:type", Number)
], Site.prototype, "latitude", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'decimal', precision: 10, scale: 6, nullable: true }),
    __metadata("design:type", Number)
], Site.prototype, "longitude", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => zone_entity_1.Zone, (zone) => zone.site),
    __metadata("design:type", Array)
], Site.prototype, "zones", void 0);
__decorate([
    (0, typeorm_1.ManyToOne)(() => organization_entity_1.Organization, org => org.sites, { nullable: true, onDelete: 'CASCADE' }),
    (0, typeorm_1.JoinColumn)({ name: 'organizationId' }),
    __metadata("design:type", organization_entity_1.Organization)
], Site.prototype, "organization", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Site.prototype, "organizationId", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => gateway_entity_1.Gateway, gateway => gateway.site),
    __metadata("design:type", Array)
], Site.prototype, "gateways", void 0);
exports.Site = Site = __decorate([
    (0, typeorm_1.Entity)()
], Site);
//# sourceMappingURL=site.entity.js.map
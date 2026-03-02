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
exports.Organization = void 0;
const typeorm_1 = require("typeorm");
const user_entity_1 = require("./user.entity");
const site_entity_1 = require("./site.entity");
let Organization = class Organization {
    id;
    name;
    type;
    country;
    contactFirstName;
    contactLastName;
    city;
    address;
    postalCode;
    phone;
    email;
    establishmentDate;
    legalForm;
    subscriptionPlan;
    maxUsers;
    maxDevices;
    maxSites;
    createdAt;
    users;
    sites;
};
exports.Organization = Organization;
__decorate([
    (0, typeorm_1.PrimaryGeneratedColumn)('uuid'),
    __metadata("design:type", String)
], Organization.prototype, "id", void 0);
__decorate([
    (0, typeorm_1.Column)(),
    __metadata("design:type", String)
], Organization.prototype, "name", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "type", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "country", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "contactFirstName", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "contactLastName", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "city", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "address", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "postalCode", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "phone", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "email", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "establishmentDate", void 0);
__decorate([
    (0, typeorm_1.Column)({ nullable: true }),
    __metadata("design:type", String)
], Organization.prototype, "legalForm", void 0);
__decorate([
    (0, typeorm_1.Column)({ default: 'Enterprise' }),
    __metadata("design:type", String)
], Organization.prototype, "subscriptionPlan", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', default: 5 }),
    __metadata("design:type", Number)
], Organization.prototype, "maxUsers", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', default: 100 }),
    __metadata("design:type", Number)
], Organization.prototype, "maxDevices", void 0);
__decorate([
    (0, typeorm_1.Column)({ type: 'int', default: 5 }),
    __metadata("design:type", Number)
], Organization.prototype, "maxSites", void 0);
__decorate([
    (0, typeorm_1.CreateDateColumn)(),
    __metadata("design:type", Date)
], Organization.prototype, "createdAt", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => user_entity_1.User, user => user.organization),
    __metadata("design:type", Array)
], Organization.prototype, "users", void 0);
__decorate([
    (0, typeorm_1.OneToMany)(() => site_entity_1.Site, site => site.organization),
    __metadata("design:type", Array)
], Organization.prototype, "sites", void 0);
exports.Organization = Organization = __decorate([
    (0, typeorm_1.Entity)('organizations')
], Organization);
//# sourceMappingURL=organization.entity.js.map
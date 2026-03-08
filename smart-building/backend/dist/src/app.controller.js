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
exports.AppController = void 0;
const common_1 = require("@nestjs/common");
const app_service_1 = require("./app.service");
const rules_engine_service_1 = require("./rules-engine.service");
const jwt_auth_guard_1 = require("./auth/jwt-auth.guard");
const roles_guard_1 = require("./auth/roles.guard");
const zod_validation_pipe_1 = require("./pipes/zod-validation.pipe");
const invite_user_schema_1 = require("./dto/invite-user.schema");
const webhook_schema_1 = require("./dto/webhook.schema");
const custom_role_schema_1 = require("./dto/custom-role.schema");
const common_2 = require("@nestjs/common");
let AppController = class AppController {
    appService;
    rulesEngineService;
    constructor(appService, rulesEngineService) {
        this.appService = appService;
        this.rulesEngineService = rulesEngineService;
    }
    getHello() {
        return this.appService.getHello();
    }
    async getHealth() {
        return this.appService.checkHealth();
    }
    getSites(orgId, role) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
        return this.appService.getSites(filterOrgId);
    }
    getOrganizations() {
        return this.appService.getOrganizations();
    }
    createOrganization(orgData) {
        return this.appService.createOrganization(orgData);
    }
    updateOrganization(id, orgData) {
        return this.appService.updateOrganization(id, orgData);
    }
    deleteOrganization(id) {
        return this.appService.deleteOrganization(id);
    }
    createSite(orgId, siteData) {
        const finalOrgId = siteData.organizationId || orgId;
        return this.appService.createSite(siteData, finalOrgId);
    }
    updateSite(id, siteData) {
        return this.appService.updateSite(id, siteData);
    }
    deleteSite(id) {
        return this.appService.deleteSite(id);
    }
    createZone(zoneData) {
        if (!zoneData.siteId) {
            throw new Error("siteId is required to create a zone");
        }
        return this.appService.createZone(zoneData, zoneData.siteId);
    }
    updateZone(id, zoneData) {
        return this.appService.updateZone(id, zoneData);
    }
    deleteZone(id) {
        return this.appService.deleteZone(id);
    }
    getSensors(orgId, role) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
        return this.appService.getSensors(filterOrgId);
    }
    getGateways(orgId, role) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
        return this.appService.getGateways(filterOrgId);
    }
    createGateway(gatewayData) {
        return this.appService.createGateway(gatewayData);
    }
    getReadings(limit, orgId) {
        const parsedLimit = limit ? parseInt(limit, 10) : 100;
        return this.appService.getReadings(parsedLimit, orgId);
    }
    getGlobalEnergy(orgId, siteId) {
        return this.appService.getGlobalEnergy(orgId, siteId);
    }
    getAverageTemperature(orgId, siteId) {
        return this.appService.getAverageTemperature(orgId, siteId);
    }
    getAlerts(orgId, role, siteId) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
        return this.appService.getAlerts(filterOrgId, siteId);
    }
    getHvacPerformance(orgId, siteId) {
        return this.appService.getHvacPerformance(orgId, siteId);
    }
    getRules(orgId, role) {
        const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
        const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
        return this.rulesEngineService.getRules(filterOrgId);
    }
    createRule(orgId, ruleData) {
        return this.rulesEngineService.createRule({ ...ruleData, organizationId: orgId });
    }
    processIotWebhook(webhookData) {
        return this.appService.processIotWebhook(webhookData);
    }
    getDashboardKpis(orgId, role) {
        return this.appService.getDashboardKpis(orgId, role);
    }
    globalSearch(q, orgId, role) {
        return this.appService.globalSearch(q, orgId, role);
    }
    getUsers(orgId) {
        return this.appService.getUsers(orgId);
    }
    createUser(userData) {
        return this.appService.createUser(userData);
    }
    updateUser(id, userData) {
        return this.appService.updateUser(id, userData);
    }
    deleteUser(id) {
        return this.appService.deleteUser(id);
    }
    getCustomRoles(orgId) {
        return this.appService.getCustomRoles(orgId);
    }
    createCustomRole(roleData) {
        return this.appService.createCustomRole(roleData);
    }
    updateCustomRole(id, roleData) {
        return this.appService.updateCustomRole(id, roleData);
    }
    deleteCustomRole(id) {
        return this.appService.deleteCustomRole(id);
    }
    executeEquipmentAction(orgId, payload) {
        return this.appService.executeEquipmentAction(payload);
    }
};
exports.AppController = AppController;
__decorate([
    (0, common_1.Get)(),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", String)
], AppController.prototype, "getHello", null);
__decorate([
    (0, common_1.Get)('health'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", Promise)
], AppController.prototype, "getHealth", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('sites'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getSites", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('organizations'),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", []),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getOrganizations", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('organizations'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createOrganization", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Put)('organizations/:id'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "updateOrganization", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Delete)('organizations/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "deleteOrganization", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('sites'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createSite", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Put)('sites/:id'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "updateSite", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Delete)('sites/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "deleteSite", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('zones'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createZone", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Put)('zones/:id'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "updateZone", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Delete)('zones/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "deleteZone", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('sensors'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getSensors", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('gateways'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getGateways", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('gateways'),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createGateway", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('readings'),
    __param(0, (0, common_1.Query)('limit')),
    __param(1, (0, common_1.Headers)('x-organization-id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getReadings", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('energy/global'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Query)('siteId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getGlobalEnergy", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('temperature/average'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Query)('siteId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getAverageTemperature", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('alerts'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __param(2, (0, common_1.Query)('siteId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getAlerts", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('energy/hvac-performance'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Query)('siteId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getHvacPerformance", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('rules'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getRules", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('rules'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createRule", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('iot/webhook'),
    (0, common_2.UsePipes)(new zod_validation_pipe_1.ZodValidationPipe(webhook_schema_1.IotWebhookSchema)),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "processIotWebhook", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('dashboard/kpis'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getDashboardKpis", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('search'),
    __param(0, (0, common_1.Query)('q')),
    __param(1, (0, common_1.Headers)('x-organization-id')),
    __param(2, (0, common_1.Headers)('x-user-role')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, String, String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "globalSearch", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('users'),
    __param(0, (0, common_1.Query)('organizationId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getUsers", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard, roles_guard_1.RolesGuard),
    (0, common_1.Post)('users'),
    (0, common_2.UsePipes)(new zod_validation_pipe_1.ZodValidationPipe(invite_user_schema_1.InviteUserSchema)),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createUser", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Put)('users/:id'),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "updateUser", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Delete)('users/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "deleteUser", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Get)('custom-roles'),
    __param(0, (0, common_1.Query)('organizationId')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "getCustomRoles", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard, roles_guard_1.RolesGuard),
    (0, common_1.Post)('custom-roles'),
    (0, common_2.UsePipes)(new zod_validation_pipe_1.ZodValidationPipe(custom_role_schema_1.CustomRoleSchema)),
    __param(0, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "createCustomRole", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard, roles_guard_1.RolesGuard),
    (0, common_1.Put)('custom-roles/:id'),
    (0, common_2.UsePipes)(new zod_validation_pipe_1.ZodValidationPipe(custom_role_schema_1.CustomRoleSchema)),
    __param(0, (0, common_1.Param)('id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "updateCustomRole", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard, roles_guard_1.RolesGuard),
    (0, common_1.Delete)('custom-roles/:id'),
    __param(0, (0, common_1.Param)('id')),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "deleteCustomRole", null);
__decorate([
    (0, common_1.UseGuards)(jwt_auth_guard_1.JwtAuthGuard),
    (0, common_1.Post)('equipment/action'),
    __param(0, (0, common_1.Headers)('x-organization-id')),
    __param(1, (0, common_1.Body)()),
    __metadata("design:type", Function),
    __metadata("design:paramtypes", [String, Object]),
    __metadata("design:returntype", void 0)
], AppController.prototype, "executeEquipmentAction", null);
exports.AppController = AppController = __decorate([
    (0, common_1.Controller)('api'),
    __metadata("design:paramtypes", [app_service_1.AppService,
        rules_engine_service_1.RulesEngineService])
], AppController);
//# sourceMappingURL=app.controller.js.map
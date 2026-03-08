"use strict";
var __decorate = (this && this.__decorate) || function (decorators, target, key, desc) {
    var c = arguments.length, r = c < 3 ? target : desc === null ? desc = Object.getOwnPropertyDescriptor(target, key) : desc, d;
    if (typeof Reflect === "object" && typeof Reflect.decorate === "function") r = Reflect.decorate(decorators, target, key, desc);
    else for (var i = decorators.length - 1; i >= 0; i--) if (d = decorators[i]) r = (c < 3 ? d(r) : c > 3 ? d(target, key, r) : d(target, key)) || r;
    return c > 3 && r && Object.defineProperty(target, key, r), r;
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.RolesGuard = void 0;
const common_1 = require("@nestjs/common");
let RolesGuard = class RolesGuard {
    canActivate(context) {
        const request = context.switchToHttp().getRequest();
        const userRole = request.headers['x-user-role'];
        if (!userRole)
            return true;
        if (userRole === 'SUPER_ADMIN')
            return true;
        const path = request.route.path;
        const method = request.method;
        if ((path.includes('/api/users') || path.includes('/api/custom-roles')) && method !== 'GET') {
            if (userRole !== 'SUPER_ADMIN') {
                throw new common_1.ForbiddenException('Rôle insuffisant. Redirection rejetée.');
            }
        }
        if (userRole === 'CLIENT') {
            if (path.includes('/api/rules') && method !== 'GET') {
                throw new common_1.ForbiddenException('Opération non autorisée pour votre profil Client.');
            }
            if (path.includes('/api/network')) {
                throw new common_1.ForbiddenException('Le monitoring réseau est réservé aux Administrateurs.');
            }
        }
        return true;
    }
};
exports.RolesGuard = RolesGuard;
exports.RolesGuard = RolesGuard = __decorate([
    (0, common_1.Injectable)()
], RolesGuard);
//# sourceMappingURL=roles.guard.js.map
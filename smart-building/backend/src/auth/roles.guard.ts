import { Injectable, CanActivate, ExecutionContext, ForbiddenException } from '@nestjs/common';

@Injectable()
export class RolesGuard implements CanActivate {
    canActivate(context: ExecutionContext): boolean {
        const request = context.switchToHttp().getRequest();
        const userRole = request.headers['x-user-role']; // Simule le token/session

        // Bypass en mode développement s'il n'y a pas de rôle
        if (!userRole) return true;

        if (userRole === 'SUPER_ADMIN') return true;

        const path = request.route.path;
        const method = request.method;

        // Restriction stricte pour la création d'utilisateurs et de rôles sur-mesure
        if ((path.includes('/api/users') || path.includes('/api/custom-roles')) && method !== 'GET') {
            if (userRole !== 'SUPER_ADMIN') {
                throw new ForbiddenException('Rôle insuffisant. Redirection rejetée.');
            }
        }

        // Restriction d'accès aux logs de la console
        if (path.includes('/api/logs')) {
            if (userRole !== 'SUPER_ADMIN') {
                throw new ForbiddenException('L\'accès aux journaux d\'audit et de sécurité est réservé aux Administrateurs Globaux.');
            }
        }

        // Restriction stricte pour le rôle CLIENT
        if (userRole === 'CLIENT') {
            // Un client ne doit pas pouvoir créer/modifier de règles globales
            if (path.includes('/api/rules') && method !== 'GET') {
                throw new ForbiddenException('Opération non autorisée pour votre profil Client.');
            }

            // Ajoutez ici d'autres restrictions (ex: accès au réseau IoT)
            if (path.includes('/api/network')) {
                throw new ForbiddenException('Le monitoring réseau est réservé aux Administrateurs.');
            }
        }

        return true; // Les ADMIN_FONCTIONNEL ont accès par défaut aux fonctionnalités
    }
}

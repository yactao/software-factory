import { Injectable, Logger } from '@nestjs/common';

export type NotificationChannel = 'EMAIL' | 'SMS' | 'PUSH';

@Injectable()
export class NotificationsService {
    private readonly logger = new Logger(NotificationsService.name);

    /**
     * Simulates sending a notification to users.
     * @param organizationId The organization to notify
     * @param message The alert message
     * @param channels The channels to broadcast on
     */
    async sendNotification(organizationId: string | undefined, message: string, channels: NotificationChannel[] = ['EMAIL']) {
        // In a real application, we would fetch users associated with this organization (e.g., ADMIN_FONCTIONNEL or CLIENT admins)
        // and send real API calls (Twilio, SendGrid, etc.)

        this.logger.log(`\n================= NOTIFICATION =================\n` +
            `🏢 Organization: ${organizationId || 'GLOBAL'}\n` +
            `📣 Channels: ${channels.join(', ')}\n` +
            `💬 Message: ${message}\n` +
            `================================================\n`);

        // Return a simulation result
        return {
            success: true,
            dispatchedTo: channels,
            timestamp: new Date().toISOString()
        };
    }
}

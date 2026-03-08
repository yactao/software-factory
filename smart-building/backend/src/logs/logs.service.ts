import { Injectable, Logger } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { AuditLog } from '../entities/audit-log.entity';
import * as fs from 'fs';
import * as path from 'path';

@Injectable()
export class LogsService {
    private readonly logger = new Logger(LogsService.name);

    constructor(
        @InjectRepository(AuditLog)
        private readonly auditLogRepo: Repository<AuditLog>,
    ) { }

    async getAuditLogs(orgId?: string, limit: number = 200) {
        const where = orgId ? { organizationId: orgId } : {};
        return this.auditLogRepo.find({
            where,
            order: { timestamp: 'DESC' },
            take: limit,
            relations: ['user'], // Fetch user info
        });
    }

    getSystemLogs(linesToRead: number = 500) {
        return this.readLastLinesFromLogDir('api-combined-', linesToRead);
    }

    getIotLogs(linesToRead: number = 500) {
        return this.readLastLinesFromLogDir('iot-traffic-', linesToRead);
    }

    /**
     * Reads raw text backwards from the latest file matching the prefix in the logs directory.
     * This is basic file streaming reading the last X lines.
     */
    private readLastLinesFromLogDir(prefix: string, maxLines: number): any {
        try {
            const logsDir = path.join(process.cwd(), 'logs');
            if (!fs.existsSync(logsDir)) {
                return { error: 'Dossier de logs introuvable', logs: [] };
            }

            // Find all files starting with prefix
            const files = fs.readdirSync(logsDir).filter(f => f.startsWith(prefix) && f.endsWith('.log'));
            if (files.length === 0) {
                return { error: `Aucun fichier de type ${prefix} trouvé`, logs: [] };
            }

            // Latest file based on sort
            files.sort().reverse();
            const latestFile = path.join(logsDir, files[0]);

            // Simple implementation: Read full file and slice
            const fileContent = fs.readFileSync(latestFile, 'utf-8');
            const lines = fileContent.trim().split('\n');

            const parsedLogs = lines.slice(-maxLines).map(line => {
                try {
                    return JSON.parse(line);
                } catch (e) {
                    return { message: line };
                }
            });

            return {
                filename: files[0],
                totalLinesFile: lines.length,
                logs: parsedLogs
            };

        } catch (error) {
            this.logger.error("Error reading logs:", error);
            return { error: "Failed to read logs", detail: error.message, logs: [] };
        }
    }
}

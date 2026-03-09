import { Controller, Get, Query, UseGuards } from '@nestjs/common';
import { LogsService } from './logs.service';
import { JwtAuthGuard } from '../auth/jwt-auth.guard';
import { RolesGuard } from '../auth/roles.guard';

@Controller('api/logs')
@UseGuards(JwtAuthGuard, RolesGuard)
export class LogsController {
    constructor(private readonly logsService: LogsService) { }

    @Get('audit')
    async getAuditLogs(@Query('orgId') orgId?: string, @Query('limit') limit?: number) {
        // SECURITY FIX: Enforce a hard cap on the limit of returned rows
        const parsedLimit = isNaN(Number(limit)) ? 200 : Math.min(Number(limit), 2000);
        return this.logsService.getAuditLogs(orgId, parsedLimit);
    }

    @Get('system')
    async getSystemLogs(@Query('lines') lines?: number) {
        const parsedLines = isNaN(Number(lines)) ? 500 : Math.min(Number(lines), 1000);
        return this.logsService.getSystemLogs(parsedLines);
    }

    @Get('iot')
    async getIotLogs(@Query('lines') lines?: number) {
        const parsedLines = isNaN(Number(lines)) ? 500 : Math.min(Number(lines), 1000);
        return this.logsService.getIotLogs(parsedLines);
    }
}

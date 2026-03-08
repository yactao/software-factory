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
        return this.logsService.getAuditLogs(orgId, limit);
    }

    @Get('system')
    async getSystemLogs(@Query('lines') lines?: number) {
        return this.logsService.getSystemLogs(lines || 500);
    }

    @Get('iot')
    async getIotLogs(@Query('lines') lines?: number) {
        return this.logsService.getIotLogs(lines || 500);
    }
}

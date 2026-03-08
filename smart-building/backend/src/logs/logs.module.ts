import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AuditLog } from '../entities/audit-log.entity';
import { LogsController } from './logs.controller';
import { LogsService } from './logs.service';

@Module({
    imports: [TypeOrmModule.forFeature([AuditLog])],
    controllers: [LogsController],
    providers: [LogsService],
})
export class LogsModule { }

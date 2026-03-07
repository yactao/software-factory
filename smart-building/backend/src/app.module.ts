import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { AppController } from './app.controller';
import { AppService } from './app.service';
import { Site } from './entities/site.entity';
import { Zone } from './entities/zone.entity';
import { Sensor } from './entities/sensor.entity';
import { Reading } from './entities/reading.entity';
import { Alert } from './entities/alert.entity';
import { Rule } from './entities/rule.entity';
import { Organization } from './entities/organization.entity';
import { User } from './entities/user.entity';
import { CustomRole } from './entities/custom-role.entity';
import { Gateway } from './entities/gateway.entity';
import { DeviceTemplate } from './entities/device-template.entity';
import { PayloadMapping } from './entities/payload-mapping.entity';
import { SimulationService } from './simulation.service';
import { RulesEngineService } from './rules-engine.service';
import { NotificationsModule } from './notifications/notifications.module';
import { AiModule } from './ai/ai.module';
import { AuthModule } from './auth/auth.module';
import { PayloadFormatterService } from './iot/payload-formatter.service';
import { EventsGateway } from './iot/events.gateway';
import { IntegrationsController } from './integrations.controller';
import { UniversalMqttListenerService } from './iot/universal-mqtt-listener.service';
import { CopilotModule } from './copilot/copilot.module';
import { MqttService } from './mqtt.service';

@Module({
  imports: [
    TypeOrmModule.forRoot({
      type: 'better-sqlite3',
      database: 'smartbuild_v3.sqlite',
      entities: [Site, Zone, Sensor, Reading, Alert, Rule, Organization, User, CustomRole, Gateway, DeviceTemplate, PayloadMapping],
      synchronize: true, // Auto-create tables (Dev only)
      logging: false, // Turn off logging to reduce noise
    }),
    TypeOrmModule.forFeature([Site, Zone, Sensor, Reading, Alert, Rule, Organization, User, CustomRole, Gateway, DeviceTemplate, PayloadMapping]),
    NotificationsModule,
    AiModule,
    AuthModule,
    CopilotModule,
  ],
  controllers: [AppController, IntegrationsController],
  providers: [AppService, SimulationService, RulesEngineService, PayloadFormatterService, EventsGateway, UniversalMqttListenerService, MqttService],
  exports: [AppService],
})
export class AppModule { }

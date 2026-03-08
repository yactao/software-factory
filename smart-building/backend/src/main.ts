import { NestFactory } from '@nestjs/core';
import { WinstonModule } from 'nest-winston';
import { loggerConfig } from './logger/logger.config';
import { AppModule } from './app.module';
import { RolesGuard } from './auth/roles.guard';

async function bootstrap() {
  const app = await NestFactory.create(AppModule, {
    logger: WinstonModule.createLogger(loggerConfig),
  });
  app.enableCors({ origin: '*', allowedHeaders: '*' }); // Allow frontend to fetch data with custom headers
  app.useGlobalGuards(new RolesGuard());
  await app.listen(process.env.PORT ?? 3001, '0.0.0.0'); // Listen on all network interfaces
}
bootstrap();

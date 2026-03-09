"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const core_1 = require("@nestjs/core");
const nest_winston_1 = require("nest-winston");
const logger_config_1 = require("./logger/logger.config");
const app_module_1 = require("./app.module");
const roles_guard_1 = require("./auth/roles.guard");
async function bootstrap() {
    const app = await core_1.NestFactory.create(app_module_1.AppModule, {
        logger: nest_winston_1.WinstonModule.createLogger(logger_config_1.loggerConfig),
    });
    app.enableCors({ origin: '*', allowedHeaders: '*' });
    app.useGlobalGuards(new roles_guard_1.RolesGuard());
    await app.listen(process.env.PORT ?? 3001, '0.0.0.0');
}
bootstrap();
//# sourceMappingURL=main.js.map
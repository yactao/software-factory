import { utilities as nestWinstonModuleUtilities } from 'nest-winston';
import * as winston from 'winston';
import DailyRotateFile = require('winston-daily-rotate-file');

export const loggerConfig = {
    transports: [
        new winston.transports.Console({
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.ms(),
                nestWinstonModuleUtilities.format.nestLike('UBBEE-API', {
                    colors: true,
                    prettyPrint: true,
                }),
            ),
        }),
        new DailyRotateFile({
            filename: 'logs/api-error-%DATE%.log',
            datePattern: 'YYYY-MM-DD',
            zippedArchive: true,
            maxSize: '20m',
            maxFiles: '14d',
            level: 'error',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json()
            )
        }),
        new DailyRotateFile({
            filename: 'logs/api-combined-%DATE%.log',
            datePattern: 'YYYY-MM-DD',
            zippedArchive: true,
            maxSize: '20m',
            maxFiles: '14d',
            format: winston.format.combine(
                winston.format.timestamp(),
                winston.format.json()
            )
        }),
    ],
};

export const iotLoggerInfo = winston.createLogger({
    level: 'info',
    format: winston.format.combine(
        winston.format.timestamp(),
        winston.format.json()
    ),
    transports: [
        new DailyRotateFile({
            filename: 'logs/iot-traffic-%DATE%.log',
            datePattern: 'YYYY-MM-DD',
            zippedArchive: true,
            maxSize: '50m',
            maxFiles: '7d', // Keep less days for IoT noise
        })
    ]
});

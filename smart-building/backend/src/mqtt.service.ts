import { Injectable, OnModuleInit } from '@nestjs/common';
import { connect, MqttClient } from 'mqtt';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { Reading } from './entities/reading.entity';
import { Sensor } from './entities/sensor.entity';
import { Gateway } from './entities/gateway.entity';

@Injectable()
export class MqttService implements OnModuleInit {
    private client: MqttClient;

    constructor(
        @InjectRepository(Reading)
        private readingRepo: Repository<Reading>,
        @InjectRepository(Sensor)
        private sensorRepo: Repository<Sensor>,
        @InjectRepository(Gateway)
        private gatewayRepo: Repository<Gateway>,
    ) { }

    onModuleInit() {
        this.client = connect('mqtt://localhost:1883');

        this.client.on('connect', () => {
            console.log('✅ Connected to MQTT Broker');
            this.client.subscribe('smartbuilding/+/+/telemetry');
            this.client.subscribe('ubbee/provisioning/handshake');
        });

        this.client.on('message', async (topic, message) => {
            try {
                const payload = JSON.parse(message.toString());
                if (topic === 'ubbee/provisioning/handshake') {
                    await this.handleHandshake(payload);
                } else if (topic.endsWith('/telemetry')) {
                    await this.handleMessage(payload);
                }
            } catch (err) {
                console.error(`❌ Error processing MQTT message on ${topic}:`, err);
            }
        });
    }

    private async handleHandshake(payload: any) {
        const { mac } = payload;
        if (!mac) return;

        console.log(`🔌 Handshake reçu pour la MAC: ${mac}`);

        // Vérifier dans la base de données si une passerelle a été provisionnée avec cette MAC
        const gateway = await this.gatewayRepo.findOne({
            where: { serialNumber: mac },
            relations: ['site']
        });

        if (!gateway) {
            console.log(`⚠️ U-Bot inconnu (${mac}), handshake refusé.`);
            return;
        }

        // Si la Gateway est trouvée, on la passe "en ligne"
        gateway.status = 'online';
        await this.gatewayRepo.save(gateway);

        const buildingId = gateway.site ? gateway.site.id : 'unknown-building';
        console.log(`✅ U-Bot reconnu et passé online ! Assigation au site : ${buildingId}`);

        // Réponse Cloud (Descente de configuration)
        const configData = {
            building_id: buildingId,
            status: 'approved',
            timestamp: new Date().toISOString()
        };

        this.client.publish(`ubbee/provisioning/${mac}/config`, JSON.stringify(configData));
    }

    private async handleMessage(payload: any) {
        // Expected Payload: { device_id: "...", data: { temperature: 21.5, ... }, timestamp: "..." }
        const { device_id, data, timestamp } = payload;

        // 1. Find or Create Sensor(s) based on data keys
        for (const [key, value] of Object.entries(data)) {
            if (typeof value !== 'number' && typeof value !== 'boolean' && typeof value !== 'string') continue;

            const sensorExternalId = `${device_id}_${key}`;
            let sensor = await this.sensorRepo.findOne({ where: { externalId: sensorExternalId } });

            if (!sensor) {
                // Create Sensor on the fly (Auto-discovery)
                sensor = this.sensorRepo.create({
                    externalId: sensorExternalId,
                    name: `${key} (${device_id})`,
                    type: key,
                    unit: this.guessUnit(key),
                });
                await this.sensorRepo.save(sensor);
                console.log(`🆕 New Sensor Discovered: ${sensor.name}`);
            }

            // 2. Save Reading
            // For boolean/string values, we might need a different storage strategy or conversion
            // Here we assume 'value' column is float, so we convert boolean to 1/0
            let numericValue = value;
            if (typeof value === 'boolean') numericValue = value ? 1 : 0;
            if (typeof value === 'string') continue; // Skip strings for now or add a string_value column

            const reading = this.readingRepo.create({
                value: Number(numericValue),
                timestamp: new Date(timestamp),
                sensor: sensor,
            });

            await this.readingRepo.save(reading);
            // console.log(`💾 Saved ${key}: ${numericValue}`);
        }
    }

    private guessUnit(key: string): string {
        if (key.includes('temp')) return '°C';
        if (key.includes('humid')) return '%';
        if (key.includes('co2')) return 'ppm';
        if (key.includes('power')) return 'W';
        return '';
    }
}

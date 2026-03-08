import { Injectable, Logger, UnauthorizedException } from '@nestjs/common';
import { AppService } from '../app.service';
import * as dotenv from 'dotenv';
import * as path from 'path';

// Load .env from root
dotenv.config({ path: path.join(__dirname, '../../../../.env') });

interface ChatMessage {
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | null;
    tool_calls?: any[];
    tool_call_id?: string;
    name?: string;
}

@Injectable()
export class CopilotService {
    private readonly logger = new Logger(CopilotService.name);
    // Use DeepSeek API as the backend for the AI if not using local Llama/Qwen.
    // It fully supports OpenAI function calling format.
    private readonly apiUrl = 'https://api.deepseek.com/chat/completions';
    private apiKey: string;

    constructor(private readonly appService: AppService) {
        this.apiKey = (process.env.DEEPSEEK_API_KEY || '').replace(/['"]/g, '');
        if (!this.apiKey) {
            this.logger.warn('DEEPSEEK_API_KEY is not defined in .env! Copilot will not work.');
        }
    }

    // Define the tools that the LLM is allowed to call
    private getAvailableTools() {
        return [
            {
                type: 'function',
                function: {
                    name: 'get_sensor_history',
                    description: 'Get historical data for a specific sensor over a given time period.',
                    parameters: {
                        type: 'object',
                        properties: {
                            deviceId: { type: 'string', description: 'The unique ID of the device/sensor.' },
                            startTime: { type: 'string', description: 'Start time in ISO format (e.g. 2026-02-20T00:00:00Z).' },
                            endTime: { type: 'string', description: 'End time in ISO format.' }
                        },
                        required: ['deviceId', 'startTime', 'endTime']
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'set_device_state',
                    description: 'Préparer une action de changement d\'état (ON/OFF, consigne, etc). L\'APPEL DE CET OUTIL NE DÉCLENCHE PAS L\'ACTION PHYSIQUEMENT, IL AFFICHE SEULEMENT LE BOUTON DE CONFIRMATION DANS L\'INTERFACE UBBEE. Appelle-le sans demander à l\'utilisateur.',
                    parameters: {
                        type: 'object',
                        properties: {
                            deviceId: { type: 'string', description: 'The unique ID of the device to control.' },
                            action: { type: 'string', description: 'The type of action: power, temp_setpoint, brightness.' },
                            value: { type: 'string', description: 'The new value, e.g. "ON", "OFF", "22", "80%".' }
                        },
                        required: ['deviceId', 'action', 'value']
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'list_my_available_devices',
                    description: 'Get a list of all devices available to the user. ALWAYS use this tool first if you do not know a device ID or need to find devices in a specific site/room/zone.',
                    parameters: {
                        type: 'object',
                        properties: {
                            searchText: { type: 'string', description: 'Optional search text to filter by name, site, or room (e.g. "Casa", "Open Space").' },
                            deviceType: { type: 'string', description: 'Optional device type (e.g. "hvac", "light", "sensor").' }
                        }
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'get_dashboard_kpis',
                    description: 'Get global KPIs for the current organization including health score, total energy, and active sites. Use this to analyze the general state of the platform.',
                    parameters: {
                        type: 'object',
                        properties: {}
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'get_alerts',
                    description: 'Get a list of current anomalies, inactive sensors, and threshold overruns.',
                    parameters: {
                        type: 'object',
                        properties: {}
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'get_hvac_performance',
                    description: 'Get HVAC (Heating, Ventilation, Air Conditioning) performance metrics and optimization suggestions.',
                    parameters: {
                        type: 'object',
                        properties: {}
                    }
                }
            },
            {
                type: 'function',
                function: {
                    name: 'get_global_energy',
                    description: 'Get the global energy consumption of the buildings compared to the previous month.',
                    parameters: {
                        type: 'object',
                        properties: {}
                    }
                }
            }
        ];
    }

    async processChat(userMessage: string, tenantId: string, userRole: string): Promise<any> {
        // 1. Initial Context injection
        const systemPrompt = `Tu es le Copilote UBBEE, un assistant IA expert en GTB et Energy Management.
IMPORTANT: L'utilisateur actuel a le rôle "${userRole}" sur le tenant "${tenantId}".

REGLES DE COMPORTEMENT:
1. Tu dois AUSSI répondre aux questions d'analyse globale de la plateforme (consommation globale, alertes, performances CVC, Score ESG). Utilise les outils fournis (\`get_dashboard_kpis\`, \`get_alerts\`, etc.) pour récupérer le contexte avant de répondre qualitativement.
2. Si l'utilisateur demande une action sur un équipement dont tu ne connais pas le ID, appelle systématiquement "list_my_available_devices" en premier.
3. Une fois l'ID trouvé, APPELLE IMMÉDIATEMENT la fonction "set_device_state".
4. NE DEMANDE JAMAIS UNE CONFIRMATION TEXTUELLE ("Voulez-vous que je le fasse ?"). L'appel de "set_device_state" ne fait que générer la carte de validation graphique sur l'écran du client ! C'est le client qui cliquera.
5. Contente-toi de dire "Je vous prépare l'action..." et déclenche l'outil "set_device_state" silencieusement.
6. Tu es proactif, tu n'hésites pas à proposer des optimisations si tu vois des anomalies dans les alertes ou une sur-consommation HVAC.

FORMATAGE DES REPONSES (TRES IMPORTANT) :
- Le widget de chat est très petit. Tes réponses doivent être **extrêmement concises**.
- Ne fais jamais de longs paragraphes. Utilise systématiquement des puces courtes (\`-\` ou \`*\`).
- Va droit au but, ne donne pas trop de détails sauf si on te le demande. Maximum 3-4 lignes de texte au total.
- Format Markdown autorisé pour le gras (\`**terme**\`). Ne mets pas de titres (\`#\`) ni trop d'emphase.

L'heure actuelle locale est ${new Date().toISOString()}.`;

        let messages: ChatMessage[] = [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userMessage }
        ];

        // 2. Call the LLM
        return await this.callLLM(messages, tenantId, userRole);
    }

    private async callLLM(messages: ChatMessage[], tenantId: string, userRole: string): Promise<any> {
        this.logger.log(`Calling LLM API with ${messages.length} messages`);

        try {
            const response = await fetch(this.apiUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.apiKey}`
                },
                body: JSON.stringify({
                    model: 'deepseek-chat',
                    messages: messages,
                    tools: this.getAvailableTools(),
                    tool_choice: 'auto',
                    temperature: 0.1
                })
            });

            if (!response.ok) {
                const err = await response.text();
                this.logger.error(`API Error: ${response.status} - ${err}`);
                return { role: 'assistant', content: 'Désolé, une erreur technique est survenue lors de la communication avec le cerveau de l\'IA.' };
            }

            const data = await response.json();
            const message = data.choices[0].message;

            // 3. Did the LLM want to call a tool?
            if (message.tool_calls && message.tool_calls.length > 0) {
                return await this.handleToolCalls(message, messages, tenantId, userRole);
            }

            // If no tool was called, return the final natural text
            return {
                role: 'assistant',
                content: message.content
            };

        } catch (e: any) {
            this.logger.error(`LLM execution failed: ${e.message}`);
            return { role: 'assistant', content: 'Erreur interne de l\'Agent.' };
        }
    }

    private async handleToolCalls(assistantMessage: any, history: ChatMessage[], tenantId: string, userRole: string): Promise<any> {
        this.logger.log(`LLM requested tool execution: ${assistantMessage.tool_calls.length} tools`);
        history.push(assistantMessage);

        const toolResponses: any[] = [];
        let requiresConfirmation = false;
        let pendingAction = null;

        for (const toolCall of assistantMessage.tool_calls) {
            const toolName = toolCall.function.name;
            const toolArgs = JSON.parse(toolCall.function.arguments);

            this.logger.log(`Executing Tool: ${toolName} with args: ${JSON.stringify(toolArgs)}`);
            let toolResultObj: any = {};

            try {
                // Execute logic based on the tool
                if (toolName === 'list_my_available_devices') {
                    // For the POC, we fetch all tenant devices from AppService
                    const devices = await this.appService.getSensors(tenantId);

                    // Basic filtering
                    let filtered = devices;
                    if (toolArgs.searchText) {
                        filtered = devices.filter((d: any) =>
                            d.name.toLowerCase().includes(toolArgs.searchText.toLowerCase()) ||
                            (d.zone && d.zone.name.toLowerCase().includes(toolArgs.searchText.toLowerCase())) ||
                            (d.zone && d.zone.site && d.zone.site.name.toLowerCase().includes(toolArgs.searchText.toLowerCase()))
                        );
                    }
                    if (toolArgs.deviceType) {
                        filtered = filtered.filter((d: any) => d.type.toLowerCase().includes(toolArgs.deviceType.toLowerCase()));
                    }

                    // Mask sensitive data for LLM
                    toolResultObj = {
                        status: 'success',
                        devices: filtered.map((d: any) => ({
                            id: d.id,
                            name: d.name,
                            type: d.type,
                            zone: d.zone?.name || 'Inconnue',
                            site: d.zone?.site?.name || 'Inconnu'
                        }))
                    };
                }
                else if (toolName === 'get_sensor_history') {
                    // Mock data or actual data query
                    toolResultObj = {
                        status: 'success',
                        data: [
                            { timestamp: '2026-02-27T10:00:00Z', value: 21.5 },
                            { timestamp: '2026-02-27T11:00:00Z', value: 22.1 },
                            { timestamp: '2026-02-27T12:00:00Z', value: 23.5 },
                        ]
                    };
                }
                else if (toolName === 'get_dashboard_kpis') {
                    const data = await this.appService.getDashboardKpis(tenantId, userRole);
                    toolResultObj = { status: 'success', data };
                }
                else if (toolName === 'get_alerts') {
                    const orgContext = (userRole === 'SUPER_ADMIN' && tenantId === '11111111-1111-1111-1111-111111111111') ? undefined : tenantId;
                    const data = await this.appService.getAlerts(orgContext);
                    toolResultObj = { status: 'success', data };
                }
                else if (toolName === 'get_hvac_performance') {
                    const orgContext = (userRole === 'SUPER_ADMIN' && tenantId === '11111111-1111-1111-1111-111111111111') ? undefined : tenantId;
                    const data = await this.appService.getHvacPerformance(orgContext);
                    toolResultObj = { status: 'success', data };
                }
                else if (toolName === 'get_global_energy') {
                    const orgContext = (userRole === 'SUPER_ADMIN' && tenantId === '11111111-1111-1111-1111-111111111111') ? undefined : tenantId;
                    const data = await this.appService.getGlobalEnergy(orgContext);
                    toolResultObj = { status: 'success', data };
                }
                else if (toolName === 'set_device_state') {
                    // RBAC check: Does user have rights to modify?
                    if (userRole !== 'SUPER_ADMIN' && userRole !== 'ADMIN_FONCTIONNEL') {
                        toolResultObj = { status: 'error', reason: 'Permission Denied: Only Energy Managers or Admins can modify equipment state.' };
                    }
                    else {
                        // Crucial: Human-in-the-loop
                        // We do NOT execute it immediately, we prepare it for confirmation
                        requiresConfirmation = true;
                        pendingAction = {
                            toolCallId: toolCall.id,
                            deviceId: toolArgs.deviceId,
                            action: toolArgs.action,
                            value: toolArgs.value
                        };
                        toolResultObj = {
                            status: 'pending_human_confirmation',
                            message: 'This action has been halted waiting for the user to click Confirm on the Front-end.'
                        };
                    }
                }
                else {
                    toolResultObj = { status: 'error', reason: 'Unknown tool' };
                }

            } catch (err: any) {
                toolResultObj = { status: 'error', reason: err.message || 'Execution exception' };
            }

            // Append Tool Result to history so LLM can read it
            history.push({
                role: 'tool',
                tool_call_id: toolCall.id,
                name: toolName,
                content: JSON.stringify(toolResultObj)
            });
        }

        // 4. Let LLM formulate final answer with the new tool context
        const finalResponse = await this.callLLM(history, tenantId, userRole);

        // Let's inject our "requiresConfirmation" flag into the final payload sent to the frontend React
        if (requiresConfirmation && pendingAction) {
            finalResponse.requires_human_confirmation = true;
            finalResponse.pending_action = pendingAction;
        }

        return finalResponse;
    }
}

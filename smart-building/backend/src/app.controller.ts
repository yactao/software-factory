import { Body, Controller, Get, Post, Put, Delete, Param, Query, Headers, UseGuards } from '@nestjs/common';
import { AppService } from './app.service';
import { RulesEngineService } from './rules-engine.service';
import { JwtAuthGuard } from './auth/jwt-auth.guard';
import { RolesGuard } from './auth/roles.guard';
import { ZodValidationPipe } from './pipes/zod-validation.pipe';
import { InviteUserSchema } from './dto/invite-user.schema';
import { IotWebhookSchema } from './dto/webhook.schema';
import { CustomRoleSchema } from './dto/custom-role.schema';
import { UsePipes } from '@nestjs/common';

@Controller('api')
export class AppController {
  constructor(
    private readonly appService: AppService,
    private readonly rulesEngineService: RulesEngineService,
  ) { }

  @Get()
  getHello(): string {
    return this.appService.getHello();
  }

  @Get('health')
  async getHealth() {
    return this.appService.checkHealth();
  }

  @UseGuards(JwtAuthGuard)
  @Get('sites')
  getSites(@Headers('x-organization-id') orgId: string, @Headers('x-user-role') role?: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
    const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
    return this.appService.getSites(filterOrgId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('organizations')
  getOrganizations() {
    return this.appService.getOrganizations();
  }

  @UseGuards(JwtAuthGuard)
  @Post('organizations')
  createOrganization(@Body() orgData: any) {
    return this.appService.createOrganization(orgData);
  }

  @UseGuards(JwtAuthGuard)
  @Put('organizations/:id')
  updateOrganization(@Param('id') id: string, @Body() orgData: any) {
    return this.appService.updateOrganization(id, orgData);
  }

  @UseGuards(JwtAuthGuard)
  @Delete('organizations/:id')
  deleteOrganization(@Param('id') id: string) {
    return this.appService.deleteOrganization(id);
  }

  @UseGuards(JwtAuthGuard)
  @Post('sites')
  createSite(@Headers('x-organization-id') orgId: string, @Body() siteData: any) {
    const finalOrgId = siteData.organizationId || orgId;
    return this.appService.createSite(siteData, finalOrgId);
  }

  @UseGuards(JwtAuthGuard)
  @Put('sites/:id')
  updateSite(@Param('id') id: string, @Body() siteData: any) {
    return this.appService.updateSite(id, siteData);
  }

  @UseGuards(JwtAuthGuard)
  @Delete('sites/:id')
  deleteSite(@Param('id') id: string) {
    return this.appService.deleteSite(id);
  }

  @UseGuards(JwtAuthGuard)
  @Post('zones')
  createZone(@Body() zoneData: any) {
    if (!zoneData.siteId) {
      throw new Error("siteId is required to create a zone");
    }
    return this.appService.createZone(zoneData, zoneData.siteId);
  }

  @UseGuards(JwtAuthGuard)
  @Put('zones/:id')
  updateZone(@Param('id') id: string, @Body() zoneData: any) {
    return this.appService.updateZone(id, zoneData);
  }

  @UseGuards(JwtAuthGuard)
  @Delete('zones/:id')
  deleteZone(@Param('id') id: string) {
    return this.appService.deleteZone(id);
  }

  @UseGuards(JwtAuthGuard)
  @Get('sensors')
  getSensors(@Headers('x-organization-id') orgId: string, @Headers('x-user-role') role?: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
    const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
    return this.appService.getSensors(filterOrgId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('gateways')
  getGateways(@Headers('x-organization-id') orgId: string, @Headers('x-user-role') role?: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
    const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
    return this.appService.getGateways(filterOrgId);
  }

  @UseGuards(JwtAuthGuard)
  @Post('gateways')
  createGateway(@Body() gatewayData: any) {
    return this.appService.createGateway(gatewayData);
  }

  @UseGuards(JwtAuthGuard)
  @Get('readings')
  getReadings(@Query('limit') limit?: string, @Headers('x-organization-id') orgId?: string) {
    const parsedLimit = limit ? parseInt(limit, 10) : 100;
    return this.appService.getReadings(parsedLimit, orgId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('energy/global')
  getGlobalEnergy(@Headers('x-organization-id') orgId: string, @Query('siteId') siteId?: string) {
    return this.appService.getGlobalEnergy(orgId, siteId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('temperature/average')
  getAverageTemperature(@Headers('x-organization-id') orgId: string, @Query('siteId') siteId?: string) {
    return this.appService.getAverageTemperature(orgId, siteId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('alerts')
  getAlerts(@Headers('x-organization-id') orgId: string, @Headers('x-user-role') role?: string, @Query('siteId') siteId?: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
    const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
    return this.appService.getAlerts(filterOrgId, siteId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('energy/hvac-performance')
  getHvacPerformance(@Headers('x-organization-id') orgId: string, @Query('siteId') siteId?: string) {
    return this.appService.getHvacPerformance(orgId, siteId);
  }

  @UseGuards(JwtAuthGuard)
  @Get('rules')
  getRules(@Headers('x-organization-id') orgId: string, @Headers('x-user-role') role?: string) {
    const isGlobalContext = orgId === '11111111-1111-1111-1111-111111111111';
    const filterOrgId = (role === 'SUPER_ADMIN' && isGlobalContext) ? undefined : orgId;
    return this.rulesEngineService.getRules(filterOrgId);
  }

  @UseGuards(JwtAuthGuard)
  @Post('rules')
  createRule(@Headers('x-organization-id') orgId: string, @Body() ruleData: any) {
    return this.rulesEngineService.createRule({ ...ruleData, organizationId: orgId });
  }

  // IoT Webhook entrypoint (Secured or Unsecured depending on architecture, here we secure it for demo)
  @UseGuards(JwtAuthGuard)
  @Post('iot/webhook')
  @UsePipes(new ZodValidationPipe(IotWebhookSchema))
  processIotWebhook(@Body() webhookData: any) {
    return this.appService.processIotWebhook(webhookData);
  }

  @UseGuards(JwtAuthGuard)
  @Get('dashboard/kpis')
  getDashboardKpis(
    @Headers('x-organization-id') orgId: string,
    @Headers('x-user-role') role: string
  ) {
    return this.appService.getDashboardKpis(orgId, role);
  }

  @UseGuards(JwtAuthGuard)
  @Get('search')
  globalSearch(
    @Query('q') q: string,
    @Headers('x-organization-id') orgId: string,
    @Headers('x-user-role') role: string
  ) {
    return this.appService.globalSearch(q, orgId, role);
  }

  @UseGuards(JwtAuthGuard)
  @Get('users')
  getUsers(@Query('organizationId') orgId?: string) {
    return this.appService.getUsers(orgId);
  }

  @UseGuards(JwtAuthGuard, RolesGuard)
  @Post('users')
  @UsePipes(new ZodValidationPipe(InviteUserSchema))
  createUser(@Body() userData: any) {
    return this.appService.createUser(userData);
  }

  @UseGuards(JwtAuthGuard)
  @Put('users/:id')
  updateUser(@Param('id') id: string, @Body() userData: any) {
    return this.appService.updateUser(id, userData);
  }

  @UseGuards(JwtAuthGuard)
  @Delete('users/:id')
  deleteUser(@Param('id') id: string) {
    return this.appService.deleteUser(id);
  }

  @UseGuards(JwtAuthGuard)
  @Get('custom-roles')
  getCustomRoles(@Query('organizationId') orgId?: string) {
    return this.appService.getCustomRoles(orgId);
  }

  @UseGuards(JwtAuthGuard, RolesGuard)
  @Post('custom-roles')
  @UsePipes(new ZodValidationPipe(CustomRoleSchema))
  createCustomRole(@Body() roleData: any) {
    return this.appService.createCustomRole(roleData);
  }

  @UseGuards(JwtAuthGuard, RolesGuard)
  @Put('custom-roles/:id')
  @UsePipes(new ZodValidationPipe(CustomRoleSchema))
  updateCustomRole(@Param('id') id: string, @Body() roleData: any) {
    return this.appService.updateCustomRole(id, roleData);
  }

  @UseGuards(JwtAuthGuard, RolesGuard)
  @Delete('custom-roles/:id')
  deleteCustomRole(@Param('id') id: string) {
    return this.appService.deleteCustomRole(id);
  }

  @UseGuards(JwtAuthGuard)
  @Post('equipment/action')
  executeEquipmentAction(
    @Headers('x-organization-id') orgId: string,
    @Body() payload: { equipmentId: string; action: string; value?: any }
  ) {
    return this.appService.executeEquipmentAction(payload);
  }
}


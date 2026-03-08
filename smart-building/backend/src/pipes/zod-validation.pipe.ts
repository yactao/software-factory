import { PipeTransform, ArgumentMetadata, BadRequestException } from '@nestjs/common';
import { ZodSchema } from 'zod';

export class ZodValidationPipe implements PipeTransform {
    constructor(private schema: ZodSchema<any>) { }

    transform(value: any, metadata: ArgumentMetadata) {
        try {
            // .parse() efface aussi les clés non déclarées si on utilise .strict()
            const parsedValue = this.schema.parse(value);
            return parsedValue;
        } catch (error: any) {
            if (error && error.errors) {
                throw new BadRequestException({
                    message: 'Erreur de validation des données',
                    errors: error.errors
                });
            }
            throw new BadRequestException('Paramètres invalides');
        }
    }
}

# Validación local — 20 de septiembre de 2026

Se ejecutó `bash demo_script.sh` completo contra Docker Desktop, con tres APIs, Nginx y PostgreSQL. El script finalizó con código 0. El log completo de esta ejecución se conserva en `docs/demo-output.txt`.

## Resultados observados

| Comprobación | Resultado |
|---|---|
| Arranque con Compose y comprobaciones de salud | Correcto |
| Suite de integración REST | 9/9 escenarios aprobados, 4,922 s |
| Mismo token y saldo en tres réplicas | Correcto; tres identificadores de réplica distintos |
| Recarga repetida concurrentemente ocho veces | Un único crédito/movimiento |
| Acceso repetido concurrentemente ocho veces | Un único cobro y lugar ocupado |
| Saldo insuficiente después de reservar aforo | Rollback: ocupación, saldo e historial conservados |
| Dos tarjetas compitiendo por un lugar | Un acceso aprobado y uno rechazado |
| Diez accesos con saldo para uno | Un aprobado y nueve rechazados; saldo final cero |
| Actualización inválida de capacidad | Nombre y precio anteriores conservados |
| Reintento tardío de fin de ronda | No borra la ocupación posterior |
| Seguridad | 401 sin token/token malformado, 403 de propietario/permisos, bloqueo de login persistente |
| Caída de una réplica durante carga | 206 lecturas correctas, 0 reintentos de cliente, 0 errores finales |
| Reinicio planificado de PostgreSQL y APIs | Tarjeta 22 conserva saldo 50,00 y un movimiento |
| Repetición de recarga después del reinicio | No duplica el crédito; token anterior continúa válido |
| Estado final | Tres APIs y PostgreSQL saludables; Nginx funcionando en localhost:8080 |

Nginx absorbió la caída en esta ejecución; el contador de reintentos del cliente fue cero. Eso no demuestra que los reintentos fueran necesarios en esa corrida. Su límite es de tres intentos por lectura ante un error transitorio. La idempotencia de escrituras se comprueba por separado con solicitudes repetidas concurrentes.

## Alcance de la evidencia

Es una verificación funcional de la demo, no un ensayo de disponibilidad mensual ni un benchmark de escalabilidad. No se midieron los umbrales de respuesta de TFU 1. La durabilidad se verificó con reinicio de procesos y conservación del volumen, no con pérdida de disco. PostgreSQL y Nginx siguen siendo puntos únicos de falla.

Se validó la sintaxis de Python, el script Bash y el diff. El UML fue renderizado con PlantUML e inspeccionado visualmente. El script PowerShell se proporciona como equivalente, pero no se ejecutó en Windows.

## Demo explícita de escalado 1 → 3

Se ejecutó `python3 demo_scaling.py` con salida 0. Registro completo: `docs/scaling-output.txt`.

- Fase inicial: únicamente `web_replica_1` en ejecución; 30/30 consultas atendidas por un solo identificador de réplica.
- Ampliación: se arrancaron `web_replica_2` y `web_replica_3` y se cambió el upstream del proxy para utilizar las tres.
- Fase final: 30/30 consultas correctas, atendidas por tres identificadores distintos, incluida la réplica original.
- La tarjeta 23 conservó saldo 75,00 y el token emitido antes de escalar siguió funcionando.
- Repetir la recarga original después del escalado conservó un solo movimiento y el mismo saldo.
- El script restauró los tres servicios y la configuración normal del proxy al finalizar.

El proxy se recrea entre fases y existe una breve interrupción planificada. La evidencia demuestra ampliación manual y estado compartido, sin afirmar autoescalado ni una mejora cuantificada del rendimiento. El reparto de esta muestra corta no tiene por qué ser exactamente igual entre réplicas.

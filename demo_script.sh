#!/bin/bash
echo "Levantando infraestructura resiliente..."
docker compose up -d --build

echo -e "\n1. Test Seguridad: Acceso sin Token (Debe fallar 401)"
curl -s -o /dev/null -w "Status: %{http_code}\n" -X POST http://localhost/process

echo -e "\n2. Test Seguridad: Payload Malformado (Debe fallar 422)"
curl -s -o /dev/null -w "Status: %{http_code}\n" -H "Authorization: Bearer TFU-UT2-SECRET-KEY" \
  -H "Content-Type: application/json" -d '{"item_id": -5}'

echo -e "\n3. Test Disponibilidad: Ejecutando carga concurrente y deteniendo replica..."
python client_test.py &
sleep 2
docker stop web_replica_1
echo -e "\nNodo 'web_replica_1' detenido. Observe como los re-intentos mitigan la transicion."
wait

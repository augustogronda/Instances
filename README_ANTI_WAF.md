# Guía Anti-WAF para Instancias Múltiples

## Problema
Los WAF (Web Application Firewalls) pueden bloquear múltiples conexiones desde la misma IP, incluso cuando tienes derecho legítimo a usar múltiples instancias virtuales.

## Soluciones Implementadas

### 1. Técnicas de Evasión Avanzadas
- **User-Agents Rotativos**: Diferentes navegadores y versiones
- **Fingerprints Únicos**: Cada instancia tiene características únicas
- **Delays Variables**: Tiempos aleatorios entre conexiones
- **Comportamiento Humano**: Simulación de movimientos de mouse y teclado

### 2. Características Anti-Detección
- Eliminación de propiedades de automatización
- Viewports y resoluciones aleatorias
- Locales y zonas horarias variadas
- Timeouts realistas

### 3. Gestión de Proxies
- Soporte para proxies rotativos
- Distribución de tráfico entre diferentes IPs
- Archivo `proxies.txt` para configuración

## Uso

### Instalación de Dependencias
```bash
pip install playwright
playwright install chromium
```

### Configuración de Proxies (Opcional)
1. Edita el archivo `proxies.txt`
2. Agrega tus proxies en formato `ip:puerto` o `ip:puerto:usuario:contraseña`
3. Marca la opción "Usar Proxies" en la interfaz

### Ejecución
1. Ejecuta `instancesIU_advanced.py`
2. Ingresa la URL objetivo
3. Especifica el número de instancias (máximo 5 recomendado)
4. Activa "Modo Sigiloso" para comportamiento más humano
5. Haz clic en "Ejecutar"

## Recomendaciones

### Para Evitar Bloqueos
1. **No exceder 5 instancias simultáneas**
2. **Usar delays de 5-15 segundos entre instancias**
3. **Activar modo sigiloso para comportamiento humano**
4. **Usar proxies si es posible**
5. **Rotar User-Agents regularmente**

### Configuración Óptima
- **Instancias**: 2-3 máximo
- **Delays**: 10-15 segundos entre instancias
- **Modo Sigiloso**: Siempre activado
- **Proxies**: Recomendado para uso intensivo

## Archivos del Proyecto

- `instancesIU_advanced.py`: Versión mejorada con técnicas anti-WAF
- `instancesIU_playwright.py`: Versión básica con Playwright
- `instancesIU.py`: Versión original con Selenium
- `proxies.txt`: Lista de proxies (configurar según necesidad)
- `config_advanced.json`: Configuración guardada

## Troubleshooting

### Si sigues siendo bloqueado:
1. Reduce el número de instancias
2. Aumenta los delays entre conexiones
3. Usa proxies de diferentes ubicaciones
4. Cambia el User-Agent manualmente
5. Verifica que el sitio web permita múltiples sesiones

### Errores Comunes:
- **"ChromeDriver not found"**: Usa la versión Playwright
- **"Proxy connection failed"**: Verifica los proxies en `proxies.txt`
- **"Timeout errors"**: Aumenta los timeouts en el código

## Consideraciones Legales

⚠️ **IMPORTANTE**: Este software está diseñado para uso legítimo con múltiples instancias virtuales. Asegúrate de:
- Tener derecho a usar múltiples sesiones
- Cumplir con los términos de servicio del sitio web
- No usar para actividades maliciosas
- Respetar las políticas de rate limiting

## Soporte

Para problemas específicos:
1. Verifica los logs en la consola
2. Revisa la configuración de proxies
3. Ajusta los parámetros de delay
4. Considera usar menos instancias simultáneas

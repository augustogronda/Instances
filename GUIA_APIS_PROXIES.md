# 🌐 Guía de APIs de Proxies Automáticas

## 🚀 Sistema de Obtención Automática de Proxies

He implementado un sistema que obtiene proxies automáticamente desde múltiples APIs gratuitas, incluyendo **ProxyScrape** que mencionaste.

## 📡 APIs Integradas

### **1. ProxyScrape** (Recomendado)
- **URL**: https://api.proxyscrape.com/
- **Protocolos**: HTTP, SOCKS4, SOCKS5
- **Ventajas**: API confiable, proxies frescos, buena velocidad
- **Límite**: 50 proxies por request

### **2. FreeProxy**
- **URL**: https://www.proxy-list.download/
- **Protocolos**: HTTP, HTTPS, SOCKS4, SOCKS5
- **Ventajas**: Múltiples protocolos, fácil de usar
- **Límite**: 30 proxies por request

### **3. ProxyList GitHub**
- **URL**: https://github.com/TheSpeedX/PROXY-List
- **Protocolos**: HTTP, SOCKS4, SOCKS5
- **Ventajas**: Lista mantenida, proxies verificados
- **Límite**: 40 proxies por request

## 🔧 Cómo Usar el Sistema Automático

### **Paso 1: Ejecutar la Aplicación**
```bash
python instancesIU_advanced.py
```

### **Paso 2: Obtener Proxies Automáticamente**
1. **Haz clic en "Obtener Proxies Automáticamente"**
2. **El sistema obtendrá proxies desde múltiples fuentes:**
   - ProxyScrape HTTP (15 proxies)
   - ProxyScrape SOCKS4 (10 proxies)
   - FreeProxy HTTP (10 proxies)
   - ProxyList HTTP (15 proxies)

### **Paso 3: Probar Conexión**
1. **Haz clic en "Probar Conexión de Proxies"**
2. **El sistema probará los primeros 3 proxies**
3. **Verás cuáles funcionan correctamente**

### **Paso 4: Usar con Instancias**
1. **Marca "Usar Proxies"**
2. **Configura tu URL y número de instancias**
3. **Haz clic en "Ejecutar"**

## 🎯 Ventajas del Sistema Automático

### **✅ Sin Configuración Manual**
- No necesitas buscar proxies manualmente
- Se actualizan automáticamente
- Siempre tienes proxies frescos

### **✅ Múltiples Fuentes**
- Combina proxies de diferentes APIs
- Mayor variedad de IPs
- Redundancia si una API falla

### **✅ Filtrado Inteligente**
- Elimina proxies duplicados
- Valida formato correcto
- Filtra proxies inválidos

### **✅ Pruebas Automáticas**
- Verifica que los proxies funcionen
- Muestra estadísticas de éxito
- Identifica proxies problemáticos

## 📊 Comparación de Métodos

| Método | Proxies | Configuración | Actualización | Confiabilidad |
|--------|---------|---------------|--------------|---------------|
| **Manual** | Limitados | Compleja | Manual | Variable |
| **Automático** | 50+ | Automática | Automática | Alta |

## 🔍 Detalles Técnicos

### **APIs Integradas:**
```python
PROXY_APIS = {
    'proxyscrape': {
        'http': 'https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
        'socks4': 'https://api.proxyscrape.com/v2/?request=get&protocol=socks4&timeout=10000&country=all',
        'socks5': 'https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=10000&country=all'
    },
    'freeproxy': {
        'http': 'https://www.proxy-list.download/api/v1/get?type=http',
        'https': 'https://www.proxy-list.download/api/v1/get?type=https',
        'socks4': 'https://www.proxy-list.download/api/v1/get?type=socks4',
        'socks5': 'https://www.proxy-list.download/api/v1/get?type=socks5'
    }
}
```

### **Proceso de Obtención:**
1. **Request a múltiples APIs** con delays entre requests
2. **Parseo de respuestas** según formato de cada API
3. **Validación de proxies** (formato, puerto, IP)
4. **Eliminación de duplicados**
5. **Pruebas de conectividad** (opcional)

## 🚀 Flujo de Trabajo Recomendado

### **Para Uso Diario:**
1. **Ejecuta la aplicación**
2. **Clic en "Obtener Proxies Automáticamente"**
3. **Espera 30-60 segundos** para obtener proxies
4. **Clic en "Probar Conexión"** para verificar
5. **Activa "Usar Proxies"** y ejecuta

### **Para Uso Intensivo:**
1. **Obtén proxies automáticamente**
2. **Prueba conexión**
3. **Guarda proxies que funcionan** en `proxies.txt`
4. **Combina con proxies premium** para mejor rendimiento

## ⚡ Optimizaciones Implementadas

### **Rate Limiting:**
- Delays entre requests a diferentes APIs
- Respeta límites de cada servicio
- Evita bloqueos por spam

### **Validación Inteligente:**
- Verifica formato IP:puerto
- Filtra comentarios y líneas vacías
- Valida que el puerto sea numérico

### **Manejo de Errores:**
- Continúa si una API falla
- Muestra errores específicos
- Mantiene proxies que funcionan

## 🔧 Configuración Avanzada

### **Personalizar APIs:**
Edita `proxy_apis_config.json` para:
- Agregar nuevas APIs
- Cambiar límites de proxies
- Ajustar timeouts
- Modificar rate limits

### **Filtrar por País:**
```python
# En ProxyScrape, puedes especificar país:
'https://api.proxyscrape.com/v2/?request=get&protocol=http&country=US'
```

### **Filtrar por Anonimidad:**
```python
# Proxies de alta anonimidad:
'https://api.proxyscrape.com/v2/?request=get&protocol=http&anonymity=elite'
```

## 📈 Estadísticas de Rendimiento

### **ProxyScrape:**
- **Velocidad**: ⭐⭐⭐⭐⭐
- **Confiabilidad**: ⭐⭐⭐⭐⭐
- **Variedad**: ⭐⭐⭐⭐
- **Actualización**: ⭐⭐⭐⭐⭐

### **FreeProxy:**
- **Velocidad**: ⭐⭐⭐⭐
- **Confiabilidad**: ⭐⭐⭐⭐
- **Variedad**: ⭐⭐⭐⭐⭐
- **Actualización**: ⭐⭐⭐⭐

## 🛠️ Solución de Problemas

### **"No se obtuvieron proxies":**
- Verifica conexión a internet
- Revisa si las APIs están funcionando
- Intenta con una sola API primero

### **"Proxies no funcionan":**
- Los proxies gratuitos pueden ser lentos
- Prueba con menos instancias
- Considera proxies premium

### **"Conexión lenta":**
- Usa proxies de tu región geográfica
- Evita proxies sobrecargados
- Considera proxies dedicados

## 💡 Consejos de Uso

### **Para Máxima Evasión:**
1. **Obtén proxies automáticamente** antes de cada sesión
2. **Combina con modo sigiloso**
3. **Usa delays variables** entre instancias
4. **Rota proxies** regularmente

### **Para Mejor Rendimiento:**
1. **Prueba proxies** antes de usar
2. **Guarda proxies que funcionan**
3. **Combina con proxies premium**
4. **Monitorea la velocidad**

## 🔒 Consideraciones de Seguridad

- **Proxies gratuitos** pueden registrar tráfico
- **Usa HTTPS** cuando sea posible
- **No envíes datos sensibles** por proxies gratuitos
- **Considera proxies premium** para uso crítico

## 📞 Soporte

Si tienes problemas:
1. **Revisa los logs** en la consola
2. **Prueba APIs individualmente**
3. **Verifica tu conexión a internet**
4. **Considera proxies premium** para uso intensivo
